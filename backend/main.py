"""Rapid 8D — FastAPI Entry Point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_config
from backend.middleware import UserAwareMiddleware, BodyLimitMiddleware
from backend.auth import require_admin, initialize, revoke_ai_consent, router as auth_router

@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app = FastAPI(title="Rapid 8D", version="0.3.0", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(auth_router)

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.3.0"}

# Independent authenticated sessions; client-supplied identity headers are ignored.
app.add_middleware(UserAwareMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(filter(None, os.environ.get("R8D_ALLOWED_ORIGINS", "").split(","))),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BodyLimitMiddleware)

from backend.api.session import router as session_router
from backend.api.chat import router as chat_router
from backend.api.report import router as report_router
from backend.api.upload import router as upload_router

app.include_router(session_router)
app.include_router(chat_router)
app.include_router(report_router)
app.include_router(upload_router)


# Config management routes
config_router = APIRouter(prefix="/api/config", tags=["config"])


@config_router.get("")
def get_settings(request: Request):
    cfg = get_config()
    return {
        "is_admin": request.state.user["role"] == "admin",
        "ai_service_name": os.environ.get("R8D_AI_SERVICE_NAME", "尚未配置"),
        "ai_ready": bool(cfg.provider_config().get("api_key")),
        "app": cfg.app,
        "llm": {
            "api": {
                "base_url": cfg.llm.get("api", {}).get("base_url", ""),
                "model": cfg.llm.get("api", {}).get("model", ""),
                "has_api_key": bool(cfg.provider_config().get("api_key", "")),
            },
        },
        "report": cfg.report,
    }


@config_router.put("/llm")
def update_llm_settings(updates: dict, request: Request = None):
    if not require_admin(request):
        return {"status": "error", "message": "权限不足，仅管理员可修改语言模型配置"}
    cfg = get_config()
    provider = updates.get("provider", "api")
    if provider == "api" and "api" in updates:
        allowed = {key: updates["api"][key] for key in ("base_url", "model") if key in updates["api"]}
        cfg.update_llm_provider("api", allowed)
        revoke_ai_consent()
    return {"status": "ok"}


@config_router.put("/app")
def update_app_settings(updates: dict, request: Request):
    require_admin(request)
    cfg = get_config()
    if "interface_lang" in updates:
        cfg.update_config("app", "interface_lang", updates["interface_lang"])
    if "report_lang" in updates:
        cfg.update_config("app", "report_lang", updates["report_lang"])
    return {"status": "ok"}


# ─── Glossary ─────────────────────────────────────────────────────

from backend.storage import data_root, atomic_write
GLOSSARY_PATH = data_root() / "glossary.md"


@config_router.get("/glossary")
def get_glossary():
    if GLOSSARY_PATH.exists():
        return {"content": GLOSSARY_PATH.read_text(encoding="utf-8")}
    return {"content": ""}


@config_router.put("/glossary")
def update_glossary(data: dict, request: Request):
    require_admin(request)
    content = data.get("content", "")
    GLOSSARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(GLOSSARY_PATH, content)
    return {"status": "ok"}


app.include_router(config_router)


if __name__ == "__main__":
    import uvicorn
    import os
    host = os.environ.get("R8D_HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=8723)
