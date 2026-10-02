"""Project folder manager — Context JSON file read/write, report management, project deletion."""

import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from backend.project.context import ProjectContext
from backend.storage import data_root, safe_component, atomic_write
from fastapi import HTTPException


class ProjectManager:
    def __init__(self, projects_root: Path | None = None):
        if projects_root is None:
            projects_root = data_root() / "projects"
        self.root = projects_root
        self.root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id: str) -> Path:
        try:
            return self.root / safe_component(project_id)
        except ValueError:
            raise HTTPException(400, "无效项目编号")

    def create_project(self, project_id: str, title: str = "未命名 8D 报告") -> ProjectContext:
        project_dir = self.project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        ctx = ProjectContext.new(project_id, title)
        self.save_context(project_id, ctx)
        return ctx

    def save_context(self, project_id: str, ctx: ProjectContext):
        """Save context as context_YYYY-MM-DD.json, overwrite today's file."""
        ctx.update_date()
        project_dir = self.project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        filename = f"context_{ctx.date}.json"
        filepath = project_dir / filename
        payload = json.dumps(ctx.to_dict(), ensure_ascii=False, indent=2)
        self._check_capacity(filepath, payload)
        atomic_write(filepath, payload)

    def _check_capacity(self, destination: Path, content: str):
        used = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
        replaced = destination.stat().st_size if destination.exists() else 0
        if used - replaced + len(content.encode("utf-8")) > int(os.environ.get("R8D_STORAGE_MB", "100")) * 1024 * 1024:
            raise HTTPException(413, "账号存储额度不足，请删除不再需要的项目")

    def load_context(self, project_id: str, date: str | None = None) -> ProjectContext | None:
        """Load context. If date is None, load the latest (highest date)."""
        project_dir = self.project_dir(project_id)
        if not project_dir.exists():
            return None

        context_files = sorted(project_dir.glob("context_*.json"))
        if not context_files:
            return None

        if date:
            try:
                safe_component(date)
            except ValueError:
                raise HTTPException(400, "无效版本日期")
            target = project_dir / f"context_{date}.json"
            if not target.exists():
                return None
        else:
            target = context_files[-1]  # latest by filename sort (date-based)

        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ProjectContext.from_dict(data)

    def list_contexts(self, project_id: str) -> list[dict]:
        """List all context versions for a project."""
        project_dir = self.project_dir(project_id)
        if not project_dir.exists():
            return []
        result = []
        for f in sorted(project_dir.glob("context_*.json"), reverse=True):
            date = f.stem.replace("context_", "")
            result.append({"date": date, "path": str(f), "size": f.stat().st_size})
        return result

    def save_report(self, project_id: str, html_content: str, docx_path: str = ""):
        """Save report files in project folder (backup copy)."""
        project_dir = self.project_dir(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")

        html_file = project_dir / f"report_{today}.html"
        self._check_capacity(html_file, html_content)
        atomic_write(html_file, html_content)

        if docx_path and Path(docx_path).exists():
            docx_dest = project_dir / f"report_{today}.docx"
            shutil.copy2(docx_path, docx_dest)

        return str(html_file)

    def list_reports(self, project_id: str) -> list[dict]:
        """List all report versions for a project."""
        project_dir = self.project_dir(project_id)
        if not project_dir.exists():
            return []
        result = []
        for f in sorted(project_dir.glob("report_*.html"), reverse=True):
            date = f.stem.replace("report_", "")
            result.append({
                "date": date,
                "html_path": str(f),
                "docx_path": str(project_dir / f"report_{date}.docx"),
            })
        return result

    def rename_project(self, project_id: str, title: str):
        """Rename a project by updating its context title."""
        ctx = self.load_context(project_id)
        if not ctx:
            raise FileNotFoundError(f"Project {project_id} not found")
        ctx.title = title
        ctx.update_date()
        self.save_context(project_id, ctx)

    def delete_project(self, project_id: str):
        """Delete entire project folder."""
        project_dir = self.project_dir(project_id)
        if project_dir.exists():
            shutil.rmtree(project_dir)

    def get_project_summary(self, project_id: str) -> dict | None:
        """Get lightweight project summary without loading full context."""
        ctx = self.load_context(project_id)
        if not ctx:
            return None
        completed = sum(1 for s in ctx.step_states.values() if s.status == "completed")
        return {
            "project_id": ctx.project_id,
            "title": ctx.title,
            "current_step": ctx.current_step,
            "date": ctx.date,
            "steps_completed": completed,
            "total_steps": 8,
            "message_count": len(ctx.messages),
            "context_versions": len(self.list_contexts(project_id)),
            "report_versions": len(self.list_reports(project_id)),
        }
