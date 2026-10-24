import copy,io,json,tempfile,threading,time,unittest,urllib.request,urllib.error
from pathlib import Path
from rapid8d.domain import *
from rapid8d.store import Store
from rapid8d.parsers import extract
from rapid8d.model import Settings,protect,parse_json,build_messages,completion
from rapid8d.server import App,create_server
ROOT=Path(__file__).resolve().parents[1]
def sample():
    c=new_case("演示案例 隔膜分切毛刺调查（模拟数据）","import","bilingual")
    c["sources"]=[dict(id="S1",name="模拟调查记录.txt",origin="user",chunks=[dict(locator="行 1",text="模拟：批次 A 在抽查 200 卷中发现 6 卷边缘毛刺；待确认完整影响范围。")],coverage="完整文本",warnings=[],char_count=42)]
    texts=[
        "质量负责人：演示人员。生产、设备与检验参与调查；具体授权待核实。\nQuality lead: demo reviewer. Production, maintenance and inspection participate; authority remains to be confirmed.",
        "## 现象与范围\n模拟案例：分切后的隔膜边缘出现毛刺。抽查 200 卷发现 6 卷，抽样不良比例为 3%。该比例只代表本次抽样。\nObserved edge burrs in 6 of 200 sampled rolls (3%). This is a sample result, not a population estimate.\n\n| 项目 | 已知事实 | 待确认 |\n| --- | --- | --- |\n| 产品 | 模拟隔膜 A | 图号和规格 |\n| 时间 | 演示日期 | 首次发生时间 |\n| 范围 | 6/200 卷 | 全部影响批次 |",
        "建议隔离相关批次并确认库存、在制及已交付范围。尚无实际围堵完成记录。\nContainment is proposed. Execution evidence has not yet been supplied.",
        "## 产生与逃逸\n刀片磨损为候选产生原因，当前仅有相关性线索，尚未完成因果验证。检验抽样覆盖不足为候选逃逸原因。\nBlade wear and inspection coverage are hypotheses. Neither is a verified root cause.",
        "永久措施待根因验证后选择。目前仅记录候选措施：刀片寿命管理、检查标准更新。\nPermanent corrective actions await root-cause validation.",
        "实施日期、负责人、样本量、观察周期及结果尚未提供。不能宣称问题已解决。\nImplementation and effectiveness data are missing; effectiveness is not established.",
        "拟根据已验证原因更新保养规则及检查文件，并评估同类设备。责任及完成证据待补。\nPrevention and deployment will follow verified causes. Completion remains open.",
        "本报告为模拟草稿，未具备结案条件。\nThis is a simulated draft. Closure conditions have not been met."
    ]
    for s,t in zip(c["stages"],texts):s.update(status="in_progress",report_markdown=t)
    cats=[]
    labels=["人员","设备","材料","方法","测量","环境"]
    causes=["换刀判定经验不足","刀片使用寿命待核实","原料性能波动","分切参数变更未评估","抽样覆盖不足","温湿度波动"]
    for i,label in enumerate(labels):
        cats.append(dict(id="CAT"+str(i),label=label,causes=[dict(id="H"+str(i),label=causes[i],status="suspected",source_refs=[dict(source_id="S1",locator="行 1",quote=None)],root_cause_refs=[],children=[])]))
    c["fishbone"]=dict(problem_statement="分切后隔膜边缘毛刺（模拟案例）",categories=cats)
    c["root_causes"]=[dict(id="RC-O1",kind="occurrence",statement="刀片磨损可能增加边缘毛刺",verification="unverified",confirmation="unreviewed",source_refs=[dict(source_id="S1",locator="行 1",quote=None)],verification_record="尚无改变刀片状态的对比验证记录。")]
    c["gaps"]=[dict(id="G1",stage="D4",description="缺少对比验证及检出能力数据",suggested_next_step="形成验证计划并收集实际结果",resolved=False)]
    return c
def proposal(c):
    return dict(stages=[dict(id=s["id"],status="complete",report_markdown=s["report_markdown"],source_refs=[]) for s in c["stages"]],summary="已整理模拟资料，关键验证仍缺失。",next_question="刀片更换前后是否有同条件对比数据？",facts=[],hypotheses=[],root_causes=copy.deepcopy(c["root_causes"]),fishbone=copy.deepcopy(c["fishbone"]),actions=[],gaps=copy.deepcopy(c["gaps"]),conflicts=[])
class Core(unittest.TestCase):
    def test_review_requires_evidence_and_sequence(self):
        c=sample()
        with self.assertRaises(UserError):review_stage(c,"D4","我",[True,True],"核对")
        with self.assertRaises(UserError):review_stage(c,"D8","我",[True,True],"核对")
        with self.assertRaises(UserError):review_stage(c,"D1",None,[True,True],None)
        review_stage(c,"D1","审核员",[True,True],"已核对成员与职责")
        self.assertEqual(stage(c,"D1")["status"],"complete")
    def test_model_ids_cannot_inject_ui_attributes(self):
        c=sample();p=proposal(c);p["root_causes"][0]["id"]='x" onclick="bad'
        with self.assertRaises(UserError):validate_proposal(p,c,"import","D1")
    def test_invalidate_downstream(self):
        c=sample()
        for s in c["stages"]:s.update(status="complete",review={"by":"me"})
        invalidate(c,"D4")
        self.assertEqual(stage(c,"D3")["status"],"complete")
        self.assertTrue(all(s["review"] is None for s in c["stages"][3:]))
        self.assertEqual(c["report_kind"],"draft")
    def test_ai_cannot_close_or_fabricate_source(self):
        c=sample();p=validate_proposal(proposal(c),c,"import","D1")
        self.assertTrue(all(s["status"]!="complete" for s in p["stages"]))
        p["stages"][0]["source_refs"]=[dict(source_id="FAKE")]
        with self.assertRaises(UserError):validate_proposal(p,c,"import","D1")
    def test_import_requires_all_stages_and_verified_nodes_need_proof(self):
        c=sample();p=proposal(c);p["stages"].pop()
        with self.assertRaises(UserError):validate_proposal(p,c,"import","D1")
        tree=copy.deepcopy(c["fishbone"]);tree["categories"][0]["causes"][0]["status"]="verified"
        with self.assertRaises(UserError):validate_fishbone(tree,{"S1"},set())
    def test_apply_is_explicit_and_stale_proposal_refused(self):
        c=sample();p=validate_proposal(proposal(c),c,"import","D1");p["stages"][1]["report_markdown"]="NEW"
        obj=dict(base_revision=0,data=p);r=apply_proposal(c,obj,["D1"])
        self.assertEqual(stage(r,"D2")["report_markdown"],stage(c,"D2")["report_markdown"])
        c["revision"]=1
        with self.assertRaises(UserError):apply_proposal(c,obj,["D2"])
    def test_versions_and_case_isolation(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d);c=store.create("A");other=store.create("B")
            original=copy.deepcopy(c);c["stages"][0]["report_markdown"]="manual"
            saved=store.save(c,0,"edit")
            with self.assertRaises(UserError):store.save(original,0,"stale")
            h=store.history(c["id"])[0]
            self.assertEqual(store.version(c["id"],h["id"])["stages"][0]["report_markdown"],"")
            with self.assertRaises(UserError):store.version(other["id"],h["id"])
            p=store.proposal(c["id"],{},saved["revision"]);self.assertEqual(store.pending_proposal(c["id"],1)["id"],p["id"])
    def test_dpapi_and_settings_hide_key(self):
        with tempfile.TemporaryDirectory() as d:
            st=Settings(d);key="synthetic-secret-only"
            result=st.save(dict(base_url="https://example.invalid/v1",model="demo",api_key=key))
            self.assertTrue(result["key_set"]);self.assertNotIn(key,json.dumps(result))
            self.assertNotIn(key,st.path.read_text());self.assertEqual(st.read(True)["api_key"],key)
            st.save(dict(base_url="https://example.invalid/v1",model="demo",api_key=""));self.assertEqual(st.read(True)["api_key"],key)
            with self.assertRaises(UserError):st.save(dict(base_url="http://remote.invalid/v1",model="demo"))
    def test_prompt_uses_selected_sources_and_contract(self):
        c=sample();c["sources"].append(dict(id="S2",name="exclude",chunks=[dict(text="PRIVATE_UNSELECTED",locator="line1")]))
        m=build_messages(c,"guided","D4",["S1"],ROOT/"prompts")
        self.assertNotIn("PRIVATE_UNSELECTED",m[1]["content"])
        self.assertIn("report_markdown",m[0]["content"]);self.assertIn("verification_record",m[0]["content"])
        with self.assertRaises(UserError):parse_json('{"invalid":')
    def test_text_limits_and_scan_refusal(self):
        t=extract("large.txt",("中"*120010).encode());self.assertEqual(t["char_count"],120000);self.assertTrue(t["warnings"])
        from pypdf import PdfWriter
        p=PdfWriter();p.add_blank_page(200,200);b=io.BytesIO();p.write(b)
        with self.assertRaises(UserError):extract("scan.pdf",b.getvalue())
    def test_docx_and_excel_extract_have_locators(self):
        from docx import Document
        d=Document();d.add_paragraph("模拟调查");d.add_table(rows=1,cols=1).cell(0,0).text="6/200";b=io.BytesIO();d.save(b)
        result=extract("sample.docx",b.getvalue());self.assertEqual(len(result["chunks"]),2);self.assertIn("表",result["chunks"][1]["locator"])
        from openpyxl import Workbook
        w=Workbook();w.active["A1"]="模拟";w.active["B1"]="=1+1";b=io.BytesIO();w.save(b)
        x=extract("sample.xlsx",b.getvalue());self.assertIn("A1",x["chunks"][0]["text"]);self.assertTrue(any("公式" in y for y in x["warnings"]))
    def test_exports_reopen_and_long_table(self):
        from rapid8d.exporter import export
        from pypdf import PdfReader
        from docx import Document
        c=sample()
        d=Document(io.BytesIO(export(c,"docx")));self.assertIn("8D",d.paragraphs[0].text)
        raw=export(c,"pdf");text="\n".join(x.extract_text() for x in PdfReader(io.BytesIO(raw)).pages)
        self.assertIn("D8",text);self.assertIn("RC-O1",text)
        c["stages"][1]["report_markdown"]="| 字段 | 记录 |\n| --- | --- |\n| 测试 | "+("多行长文本验证。"*1500)+" |"
        self.assertGreater(len(PdfReader(io.BytesIO(export(c,"pdf"))).pages),5)
    def test_local_http_boundary_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            a=App(ROOT,d);server=create_server(a);threading.Thread(target=server.serve_forever,daemon=True).start()
            base="http://127.0.0.1:"+str(server.server_port)
            def req(path,body=None,headers=None):
                h={"X-Rapid-Token":a.token,"Content-Type":"application/json"};h.update(headers or {})
                r=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
                with urllib.request.urlopen(r) as result:return json.load(result)
            try:
                with self.assertRaises(urllib.error.HTTPError) as err:req("/api/cases",headers={"X-Rapid-Token":"wrong"})
                self.assertEqual(err.exception.code,401)
                with self.assertRaises(urllib.error.HTTPError):req("/api/cases",headers={"Origin":"https://evil.invalid"})
                c=req("/api/cases",{"title":"HTTP test"})
                c=req("/api/cases/"+c["id"]+"/source",{"revision":0,"text":"真实测试资料"})
                self.assertEqual(len(c["sources"]),1)
                with self.assertRaises(urllib.error.HTTPError):req("/api/cases/"+c["id"]+"/edit")
                with self.assertRaises(urllib.error.HTTPError) as err:req("/api/cases/"+c["id"]+"/edit",{"revision":0,"stage":"D1","text":"stale"})
                self.assertEqual(err.exception.code,409)
                from unittest.mock import patch
                a.settings.save(dict(base_url=base+"/mock",model="mock"))
                def fake(config,case,mode,sid,selected,root):
                    p=proposal(sample());p["root_causes"]=[];p["fishbone"]={"problem_statement":"测试","categories":[]};p["gaps"]=[]
                    return validate_proposal(p,case,mode,sid)
                with patch("rapid8d.server.analyze",fake):
                    job=req("/api/cases/"+c["id"]+"/analyze",{"revision":c["revision"],"mode":"import","stage":"D1","source_ids":[c["sources"][0]["id"]]})
                    for _ in range(100):
                        state=req("/api/jobs/"+job["job_id"])
                        if state["status"]!="running":break
                        time.sleep(.02)
                    self.assertEqual(state["status"],"done",state)
                    c=req("/api/cases/"+c["id"]);p=req("/api/cases/"+c["id"]+"/proposals")
                    self.assertEqual(p["id"],state["proposal_id"])
                    c=req("/api/cases/"+c["id"]+"/accept",{"revision":c["revision"],"proposal_id":p["id"],"stages":["D1","D2"]})
                    self.assertTrue(c["stages"][0]["report_markdown"]);self.assertEqual(c["stages"][3]["report_markdown"],"")
            finally:server.shutdown();server.server_close()
if __name__=="__main__":unittest.main()
