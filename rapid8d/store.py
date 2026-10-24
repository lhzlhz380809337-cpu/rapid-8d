from __future__ import annotations
import copy, json, sqlite3, threading
from contextlib import contextmanager
from pathlib import Path
from .domain import UserError,now,new_case,uid
class Store:
    def __init__(self,folder):
        self.folder=Path(folder); self.folder.mkdir(parents=True,exist_ok=True)
        self.path=self.folder/"cases.sqlite3"
        self.lock=threading.RLock()
        with self.connect() as db:
            db.executescript("PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, data TEXT NOT NULL); CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT, revision INTEGER, at TEXT, reason TEXT, data TEXT); CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, case_id TEXT, data TEXT);")
    @contextmanager
    def connect(self):
        db=sqlite3.connect(str(self.path),timeout=20)
        try:
            with db: yield db
        finally: db.close()
    def all(self):
        with self.connect() as db:
            cases=[json.loads(x[0]) for x in db.execute("SELECT data FROM cases")]
        return sorted([dict(id=c["id"],title=c["title"],updated_at=c["updated_at"],mode=c["mode"],revision=c["revision"],complete=sum(s["status"]=="complete" for s in c["stages"]),report_kind=c["report_kind"]) for c in cases],key=lambda x:x["updated_at"],reverse=True)
    def get(self,cid):
        with self.connect() as db: row=db.execute("SELECT data FROM cases WHERE id=?",(cid,)).fetchone()
        if not row: raise UserError("案例不存在。",404)
        return json.loads(row[0])
    def create(self,title,mode="guided",language="zh"):
        c=new_case(title,mode,language)
        with self.connect() as db: db.execute("INSERT INTO cases VALUES(?,?)",(c["id"],json.dumps(c,ensure_ascii=False)))
        return c
    def save(self,c,expected,reason):
        with self.lock,self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old=db.execute("SELECT data FROM cases WHERE id=?",(c["id"],)).fetchone()
            if not old: raise UserError("案例不存在。",404)
            previous=json.loads(old[0])
            if previous["revision"]!=expected: raise UserError("此案例有更新，请重新载入，避免覆盖。",409)
            c=copy.deepcopy(c); c["revision"]=expected+1; c["updated_at"]=now()
            db.execute("INSERT INTO versions(case_id,revision,at,reason,data) VALUES(?,?,?,?,?)",(c["id"],previous["revision"],now(),reason,old[0]))
            db.execute("UPDATE cases SET data=? WHERE id=?",(json.dumps(c,ensure_ascii=False),c["id"]))
        return c
    def history(self,cid):
        with self.connect() as db:
            return [dict(id=x[0],revision=x[1],at=x[2],reason=x[3]) for x in db.execute("SELECT id,revision,at,reason FROM versions WHERE case_id=? ORDER BY id DESC LIMIT 100",(cid,))]
    def version(self,cid,vid):
        with self.connect() as db: row=db.execute("SELECT data FROM versions WHERE case_id=? AND id=?",(cid,vid)).fetchone()
        if not row: raise UserError("版本不存在。",404)
        return json.loads(row[0])
    def proposal(self,cid,data,base_revision):
        p=dict(id=uid("P"),case_id=cid,base_revision=base_revision,data=data,created_at=now())
        with self.connect() as db: db.execute("INSERT INTO proposals VALUES(?,?,?)",(p["id"],cid,json.dumps(p,ensure_ascii=False)))
        return p
    def get_proposal(self,cid,pid):
        with self.connect() as db: row=db.execute("SELECT data FROM proposals WHERE id=? AND case_id=?",(pid,cid)).fetchone()
        if not row: raise UserError("建议不存在。",404)
        return json.loads(row[0])
    def pending_proposal(self,cid,revision):
        with self.connect() as db:
            rows=db.execute("SELECT data FROM proposals WHERE case_id=? ORDER BY rowid DESC LIMIT 5",(cid,)).fetchall()
        for row in rows:
            p=json.loads(row[0])
            if p["base_revision"]==revision: return p
        return {"id":None}
