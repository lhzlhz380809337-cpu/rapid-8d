"""8D Conversation Engine — state machine, LLM orchestration, context persistence."""

import re
from pathlib import Path
from datetime import datetime
from backend.config import Config
from backend.llm.factory import LLMProviderFactory
from backend.project.manager import ProjectManager
from backend.project.context import ProjectContext, ChatMessage, STEPS
from backend.i18n import t as i18n_t, get_lang_str
from backend.storage import data_root
from fastapi import HTTPException

FOCUS_CACHE: dict[tuple[str, str], str] = {}
GLOSSARY_CACHE: str | None = None
GLOSSARY_CACHE_MTIME: float = 0


def _load_glossary() -> str:
    """Load custom glossary/context from prompts/glossary.md (users edit this)."""
    global GLOSSARY_CACHE, GLOSSARY_CACHE_MTIME
    path = data_root() / "glossary.md"
    if not path.exists():
        return ""
    try:
        mtime = path.stat().st_mtime
        if GLOSSARY_CACHE is not None and mtime == GLOSSARY_CACHE_MTIME:
            return GLOSSARY_CACHE
        content = path.read_text(encoding="utf-8").strip()
        GLOSSARY_CACHE = content
        GLOSSARY_CACHE_MTIME = mtime
        return content
    except Exception:
        return GLOSSARY_CACHE or ""

# Prompt heading patterns for zh and en
HEADINGS = {
    "zh": ["## 角色", "## 目标", "## 输出要求", "## 引导问题", "### 5W2H", "### IS"],
    "en": ["## Role", "## Objective", "## Output Requirements", "## Guiding Questions", "### 5W2H", "### IS"],
}
TIELV_MARKER = {"zh": "## 【铁律】", "en": "## Golden Rules"}
TIELV_HEADING = {"zh": "## 铁律（必须遵守）", "en": "## Golden Rules (Must Follow)"}


def _load_prompt_file(step: str, lang: str = "zh") -> str:
    names = {
        "D1": "team", "D2": "problem", "D3": "containment",
        "D4": "root_cause", "D5": "corrective", "D6": "implement",
        "D7": "prevent", "D8": "recognize",
    }
    filename = names.get(step, step.lower())
    base = Path(__file__).parent / "prompts"
    # Try language-specific version first, fall back to default (zh)
    if lang != "zh":
        lang_path = base / "en" / f"{step.lower()}_{filename}.md"
        if lang_path.exists():
            return lang_path.read_text(encoding="utf-8")
    prompt_path = base / f"{step.lower()}_{filename}.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


def get_step_focus(step: str, lang: str = "zh") -> str:
    cache_key = (step, lang)
    if cache_key in FOCUS_CACHE:
        return FOCUS_CACHE[cache_key]
    raw = _load_prompt_file(step, lang)
    if not raw:
        FOCUS_CACHE[cache_key] = i18n_t(lang, "fallback_focus", step=step)
        return FOCUS_CACHE[cache_key]
    headings = HEADINGS.get(lang, HEADINGS["zh"])
    sections = []
    for heading in headings:
        start = raw.find(heading)
        if start >= 0:
            end = raw.find("\n## ", start + len(heading))
            if end < 0:
                end = len(raw)
            sections.append(raw[start:end].strip())
    tielv_start = raw.find(TIELV_MARKER.get(lang, TIELV_MARKER["zh"]))
    if tielv_start >= 0:
        tielv_end = raw.find("\n## ", tielv_start + 10)
        if tielv_end < 0:
            tielv_end = len(raw)
        tielv_text = raw[tielv_start:tielv_end].strip()
        rules = re.findall(r'\d+\.\s[^\n]+', tielv_text)
        if rules:
            tielv_label = TIELV_HEADING.get(lang, TIELV_HEADING["zh"])
            sections.insert(0, tielv_label + "\n" + "\n".join(rules))
    FOCUS_CACHE[cache_key] = "\n\n".join(sections) if sections else raw[:1500]
    return FOCUS_CACHE[cache_key]


def _build_chat_system_prompt(step: str, lang: str = "zh") -> str:
    focus = get_step_focus(step, lang)
    role = i18n_t(lang, "chat_role", step=step)
    principles = i18n_t(lang, "chat_principles")
    documents = i18n_t(lang, "chat_documents")
    label = i18n_t(lang, "chat_focus_label")
    tail = i18n_t(lang, "chat_focus_tail", step=step)
    glossary = _load_glossary()
    glossary_block = f"\n\n## 用户自定义上下文 / Custom Context\n{glossary}" if glossary else ""
    return f"""{role}

{principles}

{documents}

{label}
{focus}

{tail}{glossary_block}"""


def _build_output_generation_prompt(step: str, context_notes: str, lang: str = "zh") -> str:
    """Build prompt for generating phase output."""
    # "both" falls back to zh i18n strings, with a bilingual output requirement appended below
    i18n_lang = lang if lang != "both" else "zh"
    focus = get_step_focus(step, i18n_lang)
    role = i18n_t(i18n_lang, "output_gen_role", step=step)
    label1 = i18n_t(i18n_lang, "output_gen_label1")
    label2 = i18n_t(i18n_lang, "output_gen_label2")
    ctx_empty = i18n_t(i18n_lang, "output_gen_ctx_empty")
    reqs = i18n_t(i18n_lang, "output_gen_requirements")
    req_lines = "\n".join(f"{i+1}. {r}" for i, r in enumerate(reqs))
    fmt = i18n_t(i18n_lang, "output_gen_format")

    bilingual_req = ""
    if lang == "both":
        bilingual_req = (
            "\n\n## 语言要求（最高优先级）\n"
            "请以中英双语输出所有内容。每个段落中文在前，英文在后。"
            "不要只输出单一语言。\n\n"
            "## Language Requirement (Highest Priority)\n"
            "Output ALL content in BOTH Chinese and English. "
            "For each section, provide Chinese first, followed by the English translation. "
            "Do NOT output in a single language."
        )

    glossary = _load_glossary()
    glossary_block = f"\n\n## 用户自定义上下文 / Custom Context\n{glossary}" if glossary else ""

    return f"""{role}

{label1}
{focus}

{label2}
{context_notes or ctx_empty}

## {label1.replace('## ', '')}
{req_lines}

{fmt}{bilingual_req}{glossary_block}"""


def _build_review_prompt(step: str, all_steps_data: str, lang: str = "zh") -> str:
    """Build prompt for reviewing current step's context against ALL stages' data."""
    focus = get_step_focus(step, lang)
    role = i18n_t(lang, "review_role", step=step)
    s = i18n_t(lang, "review_rules")
    rules_lines = "\n".join(f"{i+1}. {r}" for i, r in enumerate(s))
    points_lines = "\n".join(f"{i+1}. {p}" for i, p in enumerate(i18n_t(lang, "review_points")))
    fmt = i18n_t(lang, "review_output_format")
    rules_title = "Rules" if lang == "en" else "铁律"
    phase_req_title = f"{step} Reference" if lang == "en" else f"{step} 阶段要求"
    data_title = "All Phase Data" if lang == "en" else "所有阶段数据"
    check_title = "Check Points" if lang == "en" else "检查要点"

    return f"""{role}

## {rules_title}
{rules_lines}

## {phase_req_title}
{focus}

## {data_title}
{all_steps_data}

## {check_title}
{points_lines}

{fmt}"""


class ConversationEngine:
    def __init__(self, config: Config, pm: ProjectManager | None = None):
        self.config = config
        self._llm = None
        self.project_mgr = pm or ProjectManager()
        self._context_cache: dict[str, ProjectContext] = {}

    @property
    def llm(self):
        if self._llm is None:
            self._llm = LLMProviderFactory.create(self.config)
        return self._llm

    @property
    def lang(self) -> str:
        return self.config.interface_lang

    @property
    def report_lang(self) -> str:
        return self.config.report_lang

    def get_or_create_context(self, project_id: str) -> ProjectContext:
        if project_id in self._context_cache:
            return self._context_cache[project_id]
        ctx = self.project_mgr.load_context(project_id)
        if not ctx:
            raise HTTPException(404, "项目不存在或无权访问")
        self._context_cache[project_id] = ctx
        return ctx

    # ─── Helpers ───────────────────────────────────────────────────

    def _maybe_inject_focus(self, ctx: ProjectContext, step: str):
        """If this step has no messages yet, inject the focus text as the first assistant message."""
        existing = [m for m in ctx.messages if m.step == step]
        if existing:
            return
        focus = get_step_focus(step, self.lang)
        if focus:
            ctx.messages.append(ChatMessage(
                role="assistant", content=focus,
                step=step, timestamp=datetime.now().isoformat(),
            ))

    # ─── Chat (right panel) ────────────────────────────────────────

    def process_message(self, project_id: str, user_message: str, step: str | None = None) -> dict:
        ctx = self.get_or_create_context(project_id)
        if step and step in STEPS:
            ctx.current_step = step
        current = ctx.current_step
        self._maybe_inject_focus(ctx, current)
        system_prompt = _build_chat_system_prompt(current, self.lang)
        history = []
        for m in ctx.messages[-20:]:
            role = "user" if m.role in ("user", "system") else "assistant"
            history.append({"role": role, "content": m.content})
        timestamp = datetime.now().isoformat()
        ctx.messages.append(ChatMessage(role="user", content=user_message, step=current, timestamp=timestamp))
        llm_reply = self.llm.chat(system_prompt, user_message, history)
        ctx.messages.append(ChatMessage(role="assistant", content=llm_reply, step=current, timestamp=datetime.now().isoformat()))
        if ctx.step_states[current].status == "pending":
            ctx.step_states[current].status = "in_progress"
        self.project_mgr.save_context(project_id, ctx)
        return {
            "reply": llm_reply,
            "current_step": ctx.current_step,
            "step_status": ctx.step_states[current].status,
            "project_id": project_id,
        }

    # ─── Step navigation ───────────────────────────────────────────

    def jump_to_step(self, project_id: str, target_step: str):
        if target_step not in STEPS:
            raise ValueError(f"Invalid step: {target_step}")
        ctx = self.get_or_create_context(project_id)
        ctx.current_step = target_step
        self._maybe_inject_focus(ctx, target_step)
        if ctx.step_states[target_step].status == "pending":
            ctx.step_states[target_step].status = "in_progress"
        self.project_mgr.save_context(project_id, ctx)

    # ─── Context notes ─────────────────────────────────────────────

    def update_context_notes(self, project_id: str, step: str, notes: str):
        ctx = self.get_or_create_context(project_id)
        ctx.step_states[step].context_notes = notes
        self.project_mgr.save_context(project_id, ctx)

    def get_context_notes(self, project_id: str, step: str) -> str:
        ctx = self.get_or_create_context(project_id)
        return ctx.step_states[step].context_notes

    # ─── Review context ────────────────────────────────────────────

    def review_context(self, project_id: str, step: str) -> dict:
        """Review current step context against ALL stages' data."""
        ctx = self.get_or_create_context(project_id)
        lang = self.lang

        ctx_label = "Context" if lang == "en" else "上下文"
        ai_label = "AI Output" if lang == "en" else "AI输出"
        confirmed_label = " (confirmed)" if lang == "en" else "（已确认）"
        chat_label = "Chat" if lang == "en" else "对话"

        # Collect ALL stages' data
        all_parts = []
        for s in STEPS:
            parts = [f"### {s}"]
            state = ctx.step_states[s]
            if state.context_notes.strip():
                parts.append(f"**{ctx_label}**:\n{state.context_notes[:600]}")
            if state.ai_output.strip():
                cf = confirmed_label if state.output_confirmed else ""
                parts.append(f"**{ai_label}{cf}**:\n{state.ai_output[:600]}")
            step_messages = [m for m in ctx.messages if m.step == s]
            if step_messages:
                msgs = "\n".join(f"[{m.role}] {m.content[:300]}" for m in step_messages[-8:])
                parts.append(f"**{chat_label}**:\n{msgs}")
            if len(parts) > 1:
                all_parts.append("\n".join(parts))

        all_steps_data = "\n\n---\n\n".join(all_parts)

        prompt = _build_review_prompt(step, all_steps_data, lang)
        raw = self.llm.chat(
            "You are a quality engineer. Respond ONLY with valid JSON. Never fabricate data.",
            prompt, []
        )

        findings = self._parse_findings_json(raw)

        if findings:
            type_labels = i18n_t(lang, "review_type_labels")
            title = i18n_t(lang, "review_title")
            footer = i18n_t(lang, "review_footer")
            lines = [f"{title}\n"]
            for i, f in enumerate(findings):
                t = type_labels.get(f.get("type", ""), f.get("type", ""))
                s = f.get("summary", "")
                lines.append(f"{i + 1}. **[{t}]** {s}")
            lines.append(f"\n{footer}")
            ctx.messages.append(ChatMessage(
                role="system",
                content="\n".join(lines),
                step=step,
                timestamp=datetime.now().isoformat(),
            ))
            self.project_mgr.save_context(project_id, ctx)

        return {"findings": findings}

    # ─── Output generation ─────────────────────────────────────────

    def generate_step_output(self, project_id: str, step: str) -> dict:
        """Generate AI output from context notes only (no cross-check)."""
        ctx = self.get_or_create_context(project_id)
        context_notes = ctx.step_states[step].context_notes

        prompt = _build_output_generation_prompt(step, context_notes, self.report_lang)
        raw = self.llm.chat(
            "You are a quality engineer. Respond ONLY with valid JSON. Never fabricate data.",
            prompt, []
        )

        output, _, suggestions = self._parse_output_json(raw)

        ctx.step_states[step].ai_output = output
        ctx.step_states[step].suggestions = suggestions
        self.project_mgr.save_context(project_id, ctx)

        return {"output": output, "suggestions": suggestions}

    def confirm_output(self, project_id: str, step: str, output: str):
        ctx = self.get_or_create_context(project_id)
        ctx.step_states[step].ai_output = output
        ctx.step_states[step].output_confirmed = True
        ctx.step_states[step].status = "completed"
        ctx.step_states[step].summary = output[:500]
        self.project_mgr.save_context(project_id, ctx)

    # ─── Helpers ───────────────────────────────────────────────────

    def _parse_output_json(self, raw: str) -> tuple[str, list, list]:
        try:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw)
            if json_match:
                raw = json_match.group(1)
            import json
            data = json.loads(raw)
            return data.get("output", raw), data.get("warnings", []), data.get("suggestions", [])
        except (json.JSONDecodeError, AttributeError):
            return raw, [], []

    def _parse_findings_json(self, raw: str) -> list[dict]:
        try:
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', raw)
            if json_match:
                raw = json_match.group(1)
            import json
            data = json.loads(raw)
            return data.get("findings", [])
        except (json.JSONDecodeError, AttributeError):
            return []

    def force_save(self, project_id: str):
        if project_id in self._context_cache:
            self.project_mgr.save_context(project_id, self._context_cache[project_id])
