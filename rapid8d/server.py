from __future__ import annotations
import base64,copy,hmac,json,mimetypes,os,secrets,threading,time,traceback,urllib.parse
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from . import __version__
from .domain import *
from .store import Store
from .model import Settings,analyze,completion
from .parsers import extract
from .fishbone import svg
from .exporter import export
class App:
    def __init__(self,root,data):
        self.root=Path(root);self.data=Path(data);self.store=Store(data);self.settings=Settings(data)
        self.token=secrets.token_urlsafe(32);self.jobs={};self.last_ping=time.monotonic();self.close_requested=None;self.server=None
    def add_source(self,c,name,content,origin="document"):
        source=dict(id=uid("S"),name=str(name)[:200],origin=origin,added_at=now(),**content)
        c["sources"].append(source);invalidate(c,"D2");return source
    def dispatch(self,method,path,body):
        bits=path.strip("/").split("/")
        if path=="/api/bootstrap":
            return dict(cases=self.store.all(),settings=self.settings.read(),checks=CHECKS,data_path=str(self.data),version=__version__)
        if path=="/api/ping": self.last_ping=time.monotonic(); self.close_requested=None; return {"ok":True}
        if path=="/api/disconnect": self.close_requested=time.monotonic();return {"ok":True}
        if path=="/api/quit":
            threading.Timer(.4,self.server.shutdown).start();return {"ok":True}
        if path=="/api/settings":
            return self.settings.save(body) if method=="POST" else self.settings.read()
        if path=="/api/test-model":
            completion(self.settings.read(True),[{"role":"user","content":"Reply with OK only."}],True);return {"ok":True}
        if path=="/api/cases":
            return self.store.create(body.get("title",""),body.get("mode","guided"),body.get("language","zh")) if method=="POST" else self.store.all()
        if len(bits)==3 and bits[:2]==["api","jobs"]:
            job=self.jobs.get(bits[2])
            if not job: raise UserError("任务不存在。",404)
            return job
        if len(bits)<3 or bits[:2]!=["api","cases"]: raise UserError("接口不存在。",404)
        cid=bits[2]; c=self.store.get(cid)
        if len(bits)==3:return c
        action=bits[3]
        if action=="history":
            return self.store.version(cid,int(bits[4])) if len(bits)==5 else self.store.history(cid)
        if action=="fishbone.svg":return ("image/svg+xml",svg(c["fishbone"]).encode(),"")
        if action=="proposal" and len(bits)==5:return self.store.get_proposal(cid,bits[4])
        if action=="proposals":return self.store.pending_proposal(cid,c["revision"])
        expected=body.get("revision")
        if method=="POST" and action not in ("export","analyze") and expected!=c["revision"]:
            raise UserError("案例已更新，请重新载入后再操作。",409)
        if action=="edit":
            sid=body.get("stage");s=stage(c,sid)
            text=body.get("text")
            if not isinstance(text,str) or len(text)>100000: raise UserError("正文无效或过长。")
            if s["report_markdown"]!=text:
                s["report_markdown"]=text;s["manual"]=True
                if s["status"]=="not_started":s["status"]="in_progress"
                invalidate(c,sid)
            if "title" in body:
                title=str(body["title"]).strip()
                if not title:raise UserError("案例名称不能为空。")
                c["title"]=title[:160]
            if body.get("language") in ("zh","bilingual","en"):c["language"]=body["language"]
            return self.store.save(c,expected,"手动编辑 "+sid)
        if action=="source":
            text=body.get("text","")
            if not isinstance(text,str) or not text.strip():raise UserError("请先粘贴资料。")
            parsed=extract("pasted.txt",text.encode("utf-8"))
            self.add_source(c,body.get("name") or "粘贴资料",parsed,"user")
            return self.store.save(c,expected,"添加粘贴资料")
        if action=="upload":
            try: raw=base64.b64decode(body.get("data",""),validate=True)
            except Exception:raise UserError("上传文件编码无效。")
            name=str(body.get("name","")); parsed=extract(name,raw)
            source=self.add_source(c,name,parsed)
            folder=self.data/"originals"/cid;folder.mkdir(parents=True,exist_ok=True)
            suffix=Path(name).suffix.lower()
            (folder/(source["id"]+suffix)).write_bytes(raw)
            return self.store.save(c,expected,"导入 "+name[:80])
        if action=="analysis":
            tree=body.get("fishbone");roots=body.get("root_causes",[])
            sourceids={s["id"] for s in c["sources"]}
            validate_roots(roots,sourceids)
            rootids={r["id"] for r in roots}
            for r in roots:r["confirmation"]="unreviewed"
            validate_fishbone(tree,sourceids,rootids)
            c["fishbone"]=tree;c["root_causes"]=roots;check_action_links(c);invalidate(c,"D4")
            if stage(c,"D4")["status"]=="not_started":stage(c,"D4")["status"]="in_progress"
            return self.store.save(c,expected,"编辑鱼骨与根因")
        if action=="resolve":
            key=body.get("kind","gaps")
            if key not in ("gaps","conflicts"):raise UserError("记录类型无效。")
            note=str(body.get("note","")).strip()
            if not note:raise UserError("请写明处理依据。")
            for item in c[key]:
                if item["id"]==body.get("id"):
                    item["resolution"]=note;item["resolved"]=True;item["resolved_at"]=now()
                    invalidate(c,item.get("stage") or "D2")
                    return self.store.save(c,expected,"处理关键缺口/冲突")
            raise UserError("记录不存在。")
        if action=="review":
            review_stage(c,body["stage"],body.get("reviewer"),body.get("checks"),body.get("note"),body.get("roots_confirmed"),body.get("na_escape"))
            return self.store.save(c,expected,"阶段复核 "+body["stage"])
        if action=="restore":
            old=self.store.version(cid,int(body["version_id"]))
            old["id"]=cid
            for s in old["stages"]:
                if s["status"]=="complete":s["status"]="ready_for_review"
                s["review"]=None
            old["report_kind"]="draft"
            return self.store.save(old,expected,"恢复历史版本（待复核）")
        if action=="accept":
            proposal=self.store.get_proposal(cid,body["proposal_id"])
            result=apply_proposal(c,proposal,body.get("stages",[]))
            return self.store.save(result,expected,"采用AI建议："+",".join(body["stages"]))
        if action=="export":
            kind=body.get("format")
            if kind not in ("docx","pdf","json"):raise UserError("导出格式无效。")
            raw=json.dumps(c,ensure_ascii=False,indent=2).encode() if kind=="json" else export(c,kind)
            file=f'Rapid8D-{cid}-r{c["revision"]}.{kind}'
            folder=self.data/"exports";folder.mkdir(exist_ok=True)
            (folder/file).write_bytes(raw)
            (folder/(file+".snapshot.json")).write_text(json.dumps(c,ensure_ascii=False),encoding="utf-8")
            return ("application/octet-stream",raw,file)
        if action=="analyze":
            if expected!=c["revision"]:raise UserError("案例已更新，请先载入最新内容。",409)
            config=self.settings.read(True)
            if not config.get("base_url"):raise UserError("请先配置模型接口。")
            mode=body.get("mode","guided");sid=body.get("stage","D1")
            if mode not in ("guided","import"):raise UserError("分析模式无效。")
            stage(c,sid)
            message=str(body.get("message","")).strip()
            selected=list(body.get("source_ids",[s["id"] for s in c["sources"]]))
            if message:
                if len(message)>MAX_MESSAGE:raise UserError("单条消息过长，请改为粘贴资料。")
                src=self.add_source(c,"对话 "+sid,dict(chunks=[dict(locator="用户消息",text=message)],coverage="完整消息",warnings=[],char_count=len(message)),"user")
                selected.append(src["id"]); c["messages"].append(dict(role="user",stage=sid,text=message,at=now()))
                c=self.store.save(c,expected,"新增对话")
            if mode=="import" and not selected:raise UserError("请先粘贴或上传分析资料。")
            jid=uid("J");self.jobs[jid]=dict(id=jid,status="running",message="正在分析资料，通常需要几十秒…")
            def run():
                try:
                    data=analyze(config,c,mode,sid,selected,self.root/"prompts")
                    current=self.store.get(cid)
                    if current["revision"]!=c["revision"]:raise UserError("分析期间案例已修改。请重新分析，避免覆盖最新内容。",409)
                    current["messages"].append(dict(role="assistant",stage=sid,text=data.get("summary","")+"\n\n"+(data.get("next_question") or ""),at=now()))
                    current=self.store.save(current,c["revision"],"AI分析回应")
                    p=self.store.proposal(cid,data,current["revision"])
                    self.jobs[jid]=dict(id=jid,status="done",proposal_id=p["id"])
                except UserError as ex:self.jobs[jid]=dict(id=jid,status="error",message=ex.message)
                except Exception:self.jobs[jid]=dict(id=jid,status="error",message="模型结果处理失败；现有报告已保留。请检查接口或重试。")
            threading.Thread(target=run,daemon=True).start()
            return {"job_id":jid}
        raise UserError("操作不存在。",404)
MAX_MESSAGE=30000
def create_server(app,port=0):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def respond(self,status,data,ctype="application/json; charset=utf-8",filename=""):
            if isinstance(data,(dict,list)):data=json.dumps(data,ensure_ascii=False).encode()
            if isinstance(data,str):data=data.encode()
            self.send_response(status)
            self.send_header("Content-Type",ctype);self.send_header("Content-Length",str(len(data)))
            self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            if filename:self.send_header("Content-Disposition",'attachment; filename="'+filename+'"')
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
        def handle_request(self,method):
            try:
                host=self.headers.get("Host","")
                if host not in (f"127.0.0.1:{self.server.server_port}",f"localhost:{self.server.server_port}"):
                    raise UserError("主机地址无效。",403)
                origin=self.headers.get("Origin")
                if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}",f"http://localhost:{self.server.server_port}"):
                    raise UserError("拒绝跨站请求。",403)
                path=urllib.parse.urlsplit(self.path).path
                if path=="/health":
                    return self.respond(200,{"app":"Rapid8D","version":__version__})
                if path.startswith("/api/"):
                    if not hmac.compare_digest(self.headers.get("X-Rapid-Token",""),app.token):raise UserError("会话已失效，请重新双击启动程序。",401)
                    if method=="GET" and path not in ("/api/bootstrap","/api/settings","/api/cases") and not (path.startswith("/api/jobs/") or (path.startswith("/api/cases/") and (len(path.strip("/").split("/"))==3 or "/history" in path or path.endswith("/fishbone.svg") or "/proposal/" in path or path.endswith("/proposals")))):
                        raise UserError("此操作需要POST。",405)
                    length=int(self.headers.get("Content-Length","0"))
                    if length<0 or length>30*1024*1024:raise UserError("请求过大。",413)
                    body=json.loads(self.rfile.read(length)) if length else {}
                    result=app.dispatch(method,path,body)
                    if isinstance(result,tuple):self.respond(200,result[1],result[0],result[2])
                    else:self.respond(200,result)
                else:
                    allowed={"/":"index.html","/app.js":"app.js","/style.css":"style.css","/favicon.svg":"favicon.svg"}
                    if method!="GET" or path not in allowed:raise UserError("页面不存在。",404)
                    filename=allowed[path];data=(app.root/"ui"/filename).read_bytes()
                    self.respond(200,data,mimetypes.guess_type(filename)[0] or "application/octet-stream")
            except UserError as ex:self.respond(ex.status,{"error":ex.message})
            except (ValueError,KeyError,TypeError):self.respond(400,{"error":"请求格式不正确。"})
            except Exception:self.respond(500,{"error":"操作未完成，原有记录已保留。请检查文件内容后重试。"})
        def do_GET(self):self.handle_request("GET")
        def do_POST(self):self.handle_request("POST")
    server=ThreadingHTTPServer(("127.0.0.1",port),Handler);server.daemon_threads=True
    app.server=server;return server
