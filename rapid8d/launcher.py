"""Per-user loopback desktop app, using the installed browser as a window."""
import argparse,json,os,subprocess,sys,threading,time,urllib.request,webbrowser,ctypes,hashlib
from pathlib import Path
from .server import App,create_server
def root_path():return Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parent.parent))
def launch_window(url,folder):
    candidates=[]
    for env in ("PROGRAMFILES(X86)","PROGRAMFILES","LOCALAPPDATA"):
        base=Path(os.environ.get(env,"C:/"))
        candidates.extend([base/"Microsoft/Edge/Application/msedge.exe",base/"Google/Chrome/Application/chrome.exe"])
    for path in candidates:
        if path.exists():
            subprocess.Popen([str(path),"--app="+url,"--user-data-dir="+str(folder/"browser-profile"),"--no-first-run","--disable-session-crashed-bubble","--window-size=1440,960"],creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            return
    webbrowser.open(url)
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--no-browser",action="store_true");parser.add_argument("--data-dir");parser.add_argument("--port",type=int,default=0)
    args=parser.parse_args()
    data=Path(args.data_dir or Path(os.environ.get("LOCALAPPDATA",Path.home()))/"Rapid8D")
    data.mkdir(parents=True,exist_ok=True);session=data/"session.json";mutex=None
    if os.name=="nt" and not args.no_browser:
        kernel=ctypes.windll.kernel32
        kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
        kernel.ReleaseMutex.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        mutex=kernel.CreateMutexW(None,False,"Local\\Rapid8D-"+hashlib.sha256(str(data.resolve()).lower().encode()).hexdigest()[:24])
        if kernel.WaitForSingleObject(mutex,15000) not in (0,128):raise RuntimeError("Rapid 8D 正在启动，请稍后再试。")
    def unlock():
        nonlocal mutex
        if mutex:kernel.ReleaseMutex(mutex);kernel.CloseHandle(mutex);mutex=None
    if session.exists() and not args.no_browser:
        try:
            old=json.loads(session.read_text())
            with urllib.request.urlopen(f'http://127.0.0.1:{old["port"]}/health',timeout=1) as r:healthy=json.load(r)
            if healthy.get("app")=="Rapid8D":
                launch_window(f'http://127.0.0.1:{old["port"]}/#token={old["token"]}',data);unlock();return
        except Exception:pass
    try:
        app=App(root_path(),data);server=create_server(app,args.port)
        info=dict(port=server.server_port,token=app.token,pid=os.getpid())
        session.write_text(json.dumps(info),encoding="utf-8")
    finally:unlock()
    if not args.no_browser:launch_window(f'http://127.0.0.1:{server.server_port}/#token={app.token}',data)
    def monitor():
        while True:
            time.sleep(5);elapsed=time.monotonic()-app.last_ping
            if not args.no_browser and ((app.close_requested and time.monotonic()-app.close_requested>45) or elapsed>300):
                server.shutdown();return
    threading.Thread(target=monitor,daemon=True).start()
    try:server.serve_forever()
    finally:
        server.server_close()
        try:
            if json.loads(session.read_text()).get("pid")==os.getpid():session.unlink()
        except Exception:pass
if __name__=="__main__":main()
