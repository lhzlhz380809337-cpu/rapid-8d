"""Fail-closed cookie authentication; never trust X-User-ID."""
import asyncio
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from fastapi import HTTPException
from backend.auth import current_user, reserve_ai
from backend.storage import data_root, safe_component

# JSON project transactions use one worker and serialize each account's operations.
_locks = [asyncio.Lock() for _ in range(64)]
_ai_slots = asyncio.Semaphore(2)


def get_user_data_dir(user_id, base=None):
    if not user_id:
        raise ValueError("Authenticated user required")
    path = (base or data_root()) / "users" / safe_component(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


class UserAwareMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            allowed = set(filter(None, os.environ.get("R8D_ALLOWED_ORIGINS", "").split(",")))
            if origin and origin not in allowed and origin != str(request.base_url).rstrip("/"):
                return JSONResponse({"detail": "请求来源不允许"}, status_code=403)
            if path.startswith("/api/auth/") and request.headers.get("content-type", "").split(";")[0] != "application/json":
                return JSONResponse({"detail": "需要 JSON 请求"}, status_code=415)
        public = path in {"/api/health", "/api/auth/login"}
        if path.startswith("/api") and request.method != "OPTIONS" and not public:
            user = await asyncio.to_thread(current_user, request)
            if not user:
                return JSONResponse({"detail": "请先登录"}, status_code=401)
            request.state.user = user
            request.state.user_id = user["id"]
            is_ai = request.method == "POST" and (path == "/api/chat" or any(s in path for s in ("/generate-output/", "/review-context/", "/generate-with-llm")))
            async with _locks[hash(user["id"]) % len(_locks)]:
                if is_ai:
                    if not user["ai_consent"]:
                        return JSONResponse({"detail": "请先在账号页面确认 AI 数据处理授权"}, status_code=403)
                    from backend.config import get_config
                    cfg = get_config()
                    if not cfg.provider_config().get("api_key") and cfg.llm_provider == "api":
                        return JSONResponse({"detail": "管理员尚未配置 AI 服务，项目仍可手动编辑"}, status_code=503)
                    try:
                        await asyncio.to_thread(reserve_ai, user["id"])
                    except HTTPException as exc:
                        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
                    async with _ai_slots:
                        response = await call_next(request)
                else:
                    response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        if "/reports/" in path and path.endswith("/preview"):
            response.headers["Content-Security-Policy"] = "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'"
        return response


class BodyLimitMiddleware:
    """Limit chunked bodies before multipart parsing as well as Content-Length bodies."""
    def __init__(self, app, limit=11 * 1024 * 1024):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                return await JSONResponse({"detail": "请求内容过大"}, status_code=413)(scope, receive, send)
            chunks.append(message)
            if not message.get("more_body", False):
                break
        async def replay():
            return chunks.pop(0) if chunks else await receive()
        await self.app(scope, replay, send)
