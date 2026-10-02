"""File upload API — supports images and documents."""

import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from backend.api.session import get_user_project_manager
from fastapi.responses import FileResponse

# Image types
IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Document types
DOC_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "text/xml",
    "application/json",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
DOC_EXTENSIONS = {"txt", "md", "log", "csv", "xml", "json", "pdf", "docx", "doc", "xlsx", "xls"}

ALLOWED_TYPES = IMAGE_TYPES | DOC_TYPES
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOC_SIZE = 5 * 1024 * 1024     # 5 MB

SUPPORTED_HINT = "Support: txt, md, log, csv, xml, json, pdf, docx, xlsx, png, jpg, gif, webp"

router = APIRouter(prefix="/api", tags=["upload"])


def get_upload_dir(project_id: str, request: Request) -> Path:
    pm = get_user_project_manager(request)
    if not pm.load_context(project_id):
        raise HTTPException(404, "项目不存在或无权访问")
    return pm.project_dir(project_id) / "uploads"


@router.post("/upload/{project_id}")
async def upload_file(project_id: str, request: Request, file: UploadFile = File(...)):
    upload_dir = get_upload_dir(project_id, request)
    # Basic validation
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            400,
            f"Unsupported file type: {file.content_type}. {SUPPORTED_HINT}"
        )

    data = await file.read(MAX_IMAGE_SIZE + 1)
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    is_image = file.content_type in IMAGE_TYPES

    # Size check
    max_size = MAX_IMAGE_SIZE if is_image else MAX_DOC_SIZE
    if len(data) > max_size:
        raise HTTPException(
            400,
            f"File too large ({len(data)} bytes). Max: {max_size // (1024*1024)} MB"
        )

    # Extension fallback
    if ext not in (IMAGE_EXTENSIONS | DOC_EXTENSIONS):
        if is_image:
            ext = "png"
        else:
            ext = "txt"

    filename = f"{uuid.uuid4().hex}.{ext}"
    if ext in {"docx", "xlsx"}:
        import io
        import zipfile
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 10000 or sum(entry.file_size for entry in entries) > 20 * 1024 * 1024:
                    raise HTTPException(413, "文档解压后过大")
        except zipfile.BadZipFile:
            raise HTTPException(400, "文档格式无效")
    upload_dir.mkdir(parents=True, exist_ok=True)

    filepath = upload_dir / filename
    import os
    used = sum(p.stat().st_size for p in get_user_project_manager(request).root.rglob("*") if p.is_file())
    if used + len(data) > int(os.environ.get("R8D_STORAGE_MB", "100")) * 1024 * 1024:
        raise HTTPException(413, "账号存储额度不足，请删除不再需要的项目")
    filepath.write_bytes(data)

    result = {
        "url": f"/api/uploads/{project_id}/{filename}",
        "filename": filename,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size": len(data),
        "is_image": is_image,
    }

    # Parse text for documents
    if not is_image:
        from backend.api.file_parser import parse_file
        from starlette.concurrency import run_in_threadpool
        parsed = await run_in_threadpool(parse_file, str(filepath), file.filename or filename)
        result["text"] = parsed["text"]
        result["parse_status"] = parsed["parse_status"]

    return result


@router.get("/uploads/{project_id}/{filename}")
async def get_file(project_id: str, filename: str, request: Request):
    import re
    if not re.fullmatch(r"[0-9a-f]{32}\.[a-z0-9]{1,5}", filename):
        raise HTTPException(400, "无效附件名")
    filepath = get_upload_dir(project_id, request) / filename
    if not filepath.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(filepath))
