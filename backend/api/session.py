"""Project management API routes — replaces old session-centric design."""

from fastapi import APIRouter, HTTPException, Request
from backend.project.manager import ProjectManager
from backend.middleware import get_user_data_dir

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_user_project_manager(request: Request) -> ProjectManager:
    """Return a ProjectManager scoped to the current user's data directory."""
    user_id = getattr(request.state, "user_id", None)
    base = get_user_data_dir(user_id)
    projects_root = base / "projects"
    return ProjectManager(projects_root=projects_root)


@router.post("")
def create_project(title: str = "未命名 8D 报告", request: Request = None):
    import uuid
    if len(title) > 120:
        raise HTTPException(422, "项目名称不能超过 120 字")
    project_id = str(uuid.uuid4())
    pm = get_user_project_manager(request)
    if sum(1 for p in pm.root.iterdir() if p.is_dir()) >= 50:
        raise HTTPException(409, "试用账号最多保存 50 个项目")
    pm.create_project(project_id, title)
    return {"project_id": project_id, "title": title}


@router.get("")
def list_projects(request: Request):
    """List all projects with summaries."""
    pm = get_user_project_manager(request)
    projects = []
    if pm.root.exists():
        for project_dir in sorted(pm.root.iterdir(), reverse=True):
            if not project_dir.is_dir():
                continue
            try:
                summary = pm.get_project_summary(project_dir.name)
                if summary:
                    projects.append(summary)
            except Exception:
                continue
    return projects


@router.get("/{project_id}")
def get_project(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    summary = pm.get_project_summary(project_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Project not found")
    contexts = pm.list_contexts(project_id)
    reports = pm.list_reports(project_id)
    return {**summary, "contexts": contexts, "reports": reports}


@router.put("/{project_id}")
def rename_project(project_id: str, title: str, request: Request):
    if len(title) > 120:
        raise HTTPException(422, "项目名称不能超过 120 字")
    pm = get_user_project_manager(request)
    try:
        pm.rename_project(project_id, title)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "ok", "project_id": project_id, "title": title}


@router.delete("/{project_id}")
def delete_project(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    summary = pm.get_project_summary(project_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Project not found")
    pm.delete_project(project_id)
    return {"status": "deleted", "project_id": project_id}


@router.get("/{project_id}/contexts")
def list_contexts(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    return pm.list_contexts(project_id)


@router.get("/{project_id}/contexts/latest")
def load_latest_context(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="No context found")
    return ctx.to_dict()


@router.get("/{project_id}/contexts/{date}")
def load_context(project_id: str, date: str, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id, date)
    if not ctx:
        raise HTTPException(status_code=404, detail="Context version not found")
    return ctx.to_dict()


