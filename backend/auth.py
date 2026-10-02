"""Invite-only accounts, revocable cookie sessions and durable AI quotas."""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from backend.storage import data_root

router = APIRouter(prefix="/api/auth", tags=["account"])
COOKIE = "r8d_session"
MIN_PASSWORD_LENGTH = 8

@contextmanager
def database():
    con = sqlite3.connect(data_root() / "accounts.sqlite3", timeout=20)
    con.row_factory = sqlite3.Row
    try:
        with con:
            yield con
    finally:
        con.close()

def password_hash(password: str, salt: str) -> str:
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

def create_user(username: str, password: str, role: str = "user"):
    if not re.fullmatch(r"[A-Za-z0-9_]{3,40}", username) or not MIN_PASSWORD_LENGTH <= len(password) <= 128:
        raise ValueError(f"账号需为 3–40 位字母、数字或下划线，密码需为 {MIN_PASSWORD_LENGTH}–128 位")
    salt, user_id = secrets.token_hex(16), uuid.uuid4().hex
    with database() as con:
        con.execute("INSERT INTO users(id,username,password,salt,role) VALUES(?,?,?,?,?)",
                    (user_id, username.lower(), password_hash(password, salt), salt, role))
    return user_id

def initialize():
    with database() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
          password TEXT NOT NULL,salt TEXT NOT NULL,role TEXT NOT NULL,ai_consent INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS usage(day TEXT NOT NULL,user_id TEXT NOT NULL,count INTEGER NOT NULL,PRIMARY KEY(day,user_id));
        CREATE TABLE IF NOT EXISTS attempts(key TEXT PRIMARY KEY,count INTEGER NOT NULL,until INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        ''')
        exists = con.execute("SELECT 1 FROM users WHERE role='admin'").fetchone()
    if not exists:
        password = os.environ.get("R8D_ADMIN_PASSWORD", "")
        if not password:
            raise RuntimeError(f"首次启动请设置 R8D_ADMIN_PASSWORD（至少 {MIN_PASSWORD_LENGTH} 位），没有默认管理员密码")
        create_user(os.environ.get("R8D_ADMIN_USERNAME", "admin"), password, "admin")
    # A changed recipient/model requires fresh consent, including changes made through environment variables.
    from backend.config import get_config
    cfg = get_config()
    provider = cfg.provider_config()
    fingerprint = repr((cfg.llm_provider, provider.get("base_url"), provider.get("model"), os.environ.get("R8D_AI_SERVICE_NAME")))
    with database() as con:
        previous = con.execute("SELECT value FROM metadata WHERE key='ai_service'").fetchone()
        if not previous or previous[0] != fingerprint:
            con.execute("UPDATE users SET ai_consent=0")
            con.execute("INSERT OR REPLACE INTO metadata VALUES('ai_service',?)", (fingerprint,))


def revoke_ai_consent():
    with database() as con:
        con.execute("UPDATE users SET ai_consent=0")

def current_user(request: Request):
    token = request.cookies.get(COOKIE, "")
    if not token:
        return None
    with database() as con:
        row = con.execute("SELECT u.id,u.username,u.role,u.ai_consent FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=? AND s.expires>?",
                          (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
    return dict(row) if row else None

def require_admin(request: Request):
    if not request.state.user or request.state.user["role"] != "admin":
        raise HTTPException(403, "仅管理员可执行此操作")
    return True

def reserve_ai(user_id: str):
    """Reserve before calling a provider; failed calls count to avoid retry abuse."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with database() as con:
        con.execute("BEGIN IMMEDIATE")
        total = con.execute("SELECT COALESCE(SUM(count),0) FROM usage WHERE day=?", (day,)).fetchone()[0]
        monthly = con.execute("SELECT COALESCE(SUM(count),0) FROM usage WHERE day LIKE ?", (day[:7] + "%",)).fetchone()[0]
        if monthly >= int(os.environ.get("R8D_AI_MONTHLY_TOTAL", "1000")):
            raise HTTPException(429, "本月 AI 总额度已用完，请联系管理员")
        row = con.execute("SELECT count FROM usage WHERE day=? AND user_id=?", (day,user_id)).fetchone()
        if total >= int(os.environ.get("R8D_AI_DAILY_TOTAL", "100")) or (row[0] if row else 0) >= int(os.environ.get("R8D_AI_DAILY_USER", "20")):
            raise HTTPException(429, "今日 AI 额度已用完；已保存项目仍可查看和编辑")
        con.execute("INSERT INTO usage VALUES(?,?,1) ON CONFLICT(day,user_id) DO UPDATE SET count=count+1", (day,user_id))

class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)

@router.post("/login")
def login(body: Credentials, request: Request, response: Response):
    key = "login:" + (request.client.host if request.client else "unknown")
    now = int(time.time())
    with database() as con:
        con.execute("BEGIN IMMEDIATE")
        con.execute("DELETE FROM attempts WHERE until<?", (now,))
        con.execute("DELETE FROM sessions WHERE expires<?", (now,))
        row = con.execute("SELECT count FROM attempts WHERE key=?", (key,)).fetchone()
        if row and row[0] >= 20:
            raise HTTPException(429, "登录尝试过多，请 15 分钟后重试")
        con.execute("INSERT INTO attempts VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1", (key,now+900))
        user = con.execute("SELECT * FROM users WHERE username=?", (body.username.lower(),)).fetchone()
    digest = password_hash(body.password, user["salt"] if user else "00" * 16)
    if not user or not hmac.compare_digest(digest, user["password"]):
        raise HTTPException(401, "账号或密码不正确")
    token = secrets.token_urlsafe(32)
    with database() as con:
        con.execute("INSERT INTO sessions VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(),user["id"],now+86400))
        con.execute("UPDATE attempts SET count=MAX(0,count-1) WHERE key=?", (key,))
    response.set_cookie(COOKIE, token, httponly=True, secure=os.environ.get("R8D_COOKIE_SECURE", "true").lower() == "true", samesite="strict", max_age=86400, path="/api")
    return {"status": "ok"}

@router.post("/logout")
def logout(request: Request, response: Response):
    with database() as con:
        con.execute("DELETE FROM sessions WHERE token=?", (hashlib.sha256(request.cookies.get(COOKIE, "").encode()).hexdigest(),))
    response.delete_cookie(COOKIE, path="/api")
    return {"status": "ok"}

@router.get("/me")
def me(request: Request):
    return request.state.user

@router.post("/users")
def invite(body: Credentials, request: Request):
    require_admin(request)
    with database() as con:
        if con.execute("SELECT COUNT(*) FROM users").fetchone()[0] >= 100:
            raise HTTPException(409, "试用部署最多支持 100 个账号")
    try:
        uid = create_user(body.username, body.password)
    except sqlite3.IntegrityError:
        raise HTTPException(409, "账号已存在")
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    return {"id": uid, "username": body.username.lower()}

class Consent(BaseModel):
    accepted: bool


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


@router.put("/password")
def change_password(body: PasswordChange, request: Request, response: Response):
    with database() as con:
        user = con.execute("SELECT * FROM users WHERE id=?", (request.state.user_id,)).fetchone()
        if not hmac.compare_digest(password_hash(body.current_password, user["salt"]), user["password"]):
            raise HTTPException(403, "当前密码不正确")
        salt = secrets.token_hex(16)
        con.execute("UPDATE users SET salt=?,password=? WHERE id=?", (salt,password_hash(body.new_password,salt),user["id"]))
        con.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
    response.delete_cookie(COOKIE, path="/api")
    return {"status": "ok"}

@router.put("/consent")
def consent(body: Consent, request: Request):
    with database() as con:
        con.execute("UPDATE users SET ai_consent=? WHERE id=?", (int(body.accepted),request.state.user_id))
    return {"status": "ok"}

@router.delete("/account")
def delete_account(body: Credentials, request: Request, response: Response):
    import shutil
    user = request.state.user
    if user["role"] == "admin":
        raise HTTPException(409, "管理员账号需由部署负责人在维护时处理")
    with database() as con:
        row = con.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
        if body.username.lower() != row["username"] or not hmac.compare_digest(password_hash(body.password,row["salt"]),row["password"]):
            raise HTTPException(403, "账号或密码不正确")
    directory = data_root() / "users" / user["id"]
    if directory.exists():
        shutil.rmtree(directory)
    with database() as con:
        con.execute("DELETE FROM sessions WHERE user_id=?", (user["id"],))
        con.execute("DELETE FROM usage WHERE user_id=?", (user["id"],))
        con.execute("DELETE FROM users WHERE id=?", (user["id"],))
    response.delete_cookie(COOKIE, path="/api")
    return {"status": "deleted"}
