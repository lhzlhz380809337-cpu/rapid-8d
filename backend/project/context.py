"""Context JSON serialization/deserialization for 8D project state."""

from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any


STEPS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]


@dataclass
class StepState:
    status: str = "pending"  # pending | in_progress | completed
    summary: str = ""
    context_notes: str = ""      # user-edited context (Markdown, may embed images)
    ai_output: str = ""          # confirmed AI output (Markdown + Mermaid blocks)
    output_confirmed: bool = False
    images: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)  # AI-generated hints for user, not in report


@dataclass
class ChatMessage:
    role: str = ""        # user | assistant | system
    content: str = ""
    step: str = "D1"
    timestamp: str = ""


@dataclass
class ProjectContext:
    project_id: str = ""
    date: str = ""
    title: str = ""
    current_step: str = "D1"
    step_states: dict[str, StepState] = field(default_factory=lambda: {s: StepState() for s in STEPS})
    messages: list[ChatMessage] = field(default_factory=list)
    report_requirements: str = ""

    @classmethod
    def new(cls, project_id: str, title: str = "未命名 8D 报告") -> "ProjectContext":
        return cls(
            project_id=project_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            title=title,
            current_step="D1",
        )

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "date": self.date,
            "title": self.title,
            "current_step": self.current_step,
            "step_states": {k: asdict(v) for k, v in self.step_states.items()},
            "messages": [asdict(m) for m in self.messages],
            "report_requirements": self.report_requirements,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectContext":
        ctx = cls(
            project_id=data.get("project_id", ""),
            date=data.get("date", ""),
            title=data.get("title", ""),
            current_step=data.get("current_step", "D1"),
            report_requirements=data.get("report_requirements", ""),
        )
        for step, state in data.get("step_states", {}).items():
            if step in ctx.step_states:
                ctx.step_states[step] = StepState(**state)
        ctx.messages = [ChatMessage(**m) for m in data.get("messages", [])]
        return ctx

    def update_date(self):
        self.date = datetime.now().strftime("%Y-%m-%d")
