import base64,io,json,subprocess,time,urllib.request,sys
from pathlib import Path
from openpyxl import Workbook
ROOT=Path(__file__).resolve().parents[1]
exe=ROOT/".qa/installed/Rapid8D.exe";data=ROOT/".qa/installed-data";data.mkdir(exist_ok=True)
mock=json.loads((ROOT/".qa/mock-session.json").read_text())
info={}
def start():
    began=time.perf_counter()
    p=subprocess.Popen([str(exe),"--no-browser","--data-dir",str(data)],creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(200):
        try:
            s=json.loads((data/"session.json").read_text())
            if s["pid"]==p.pid:
                with urllib.request.urlopen("http://127.0.0.1:"+str(s["port"])+"/health",timeout=1):pass
                info.update(s);return p,round(time.perf_counter()-began,3)
        except Exception:pass
        time.sleep(.1)
    raise RuntimeError("Installed application startup failed")
def req(route,body=None,raw=False):
    r=urllib.request.Request("http://127.0.0.1:"+str(info["port"])+"/api"+route,data=json.dumps(body).encode() if body is not None else None,headers={"X-Rapid-Token":info["token"],"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=30) as response:return response.read() if raw else json.load(response)
p,startup=start()
try:
    req("/settings",dict(base_url="http://127.0.0.1:"+str(mock["port"])+"/v1",model="synthetic-test"))
    req("/test-model",{})
    c=req("/cases",dict(title="安装验收（模拟资料）",mode="import",language="bilingual"))
    wb=Workbook();wb.active["A1"]="模拟抽查";wb.active["B1"]=200;mem=io.BytesIO();wb.save(mem)
    fixtures=[("investigation.docx",(ROOT/".qa/sample.docx").read_bytes()),("investigation.pdf",(ROOT/".qa/sample.pdf").read_bytes()),("samples.xlsx",mem.getvalue())]
    for name,raw in fixtures:
        c=req("/cases/"+c["id"]+"/upload",dict(revision=c["revision"],name=name,data=base64.b64encode(raw).decode()))
        assert c["sources"][-1]["chunks"]
    job=req("/cases/"+c["id"]+"/analyze",dict(revision=c["revision"],mode="import",stage="D1",source_ids=[c["sources"][0]["id"]]))
    for _ in range(150):
        j=req("/jobs/"+job["job_id"])
        if j["status"]!="running":break
        time.sleep(.1)
    assert j["status"]=="done",j
    c=req("/cases/"+c["id"]);proposal=req("/cases/"+c["id"]+"/proposals")
    c=req("/cases/"+c["id"]+"/accept",dict(revision=c["revision"],proposal_id=proposal["id"],stages=["D"+str(i) for i in range(1,9)]))
    for kind,prefix in [("docx",b"PK"),("pdf",b"%PDF")]:
        raw=req("/cases/"+c["id"]+"/export",{"format":kind},True);assert raw.startswith(prefix)
    cid=c["id"];revision=c["revision"]
    req("/quit",{});p.wait(10);assert not (data/"session.json").exists()
    p,restart=start();saved=req("/cases/"+cid);assert saved["revision"]==revision;assert len(saved["sources"])==3;assert saved["stages"][7]["report_markdown"]
    result=dict(startup_to_local_service_seconds=startup,restart_to_local_service_seconds=restart,case_persistence=True,docx_pdf_xlsx_import=True,word_pdf_export=True,installed_binary=True,real_model_tested=False)
    (ROOT/".qa/installed-smoke.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))
finally:
    if p.poll() is None:
        req("/quit",{});p.wait(10)
