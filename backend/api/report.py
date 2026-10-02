"""Report generation and export API routes — context-based with validation."""

import json
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from datetime import datetime
from backend.config import get_config
from backend.i18n import t as i18n_t
from backend.api.session import get_user_project_manager
from backend.report.generator import ReportGenerator
from backend.report.validator import ContentValidator
from backend.report.safety import safe_report_html
from backend.llm.factory import LLMProviderFactory

router = APIRouter(prefix="/api/reports", tags=["reports"])


class GenerateWithLLMRequest(BaseModel):
    requirements: str = Field(default="", max_length=8000)


class ReportRequirementsRequest(BaseModel):
    requirements: str = Field(max_length=8000)


DEFAULT_REQUIREMENTS = """1. 使用正式 8D 报告书面语言
2. 使用 HTML 表格整理数据（<table>标签，带边框样式）
3. 适当使用 Mermaid 图表（鱼骨图/流程图/甘特图），用 <pre class="mermaid"> 包裹
4. 缺失信息标注 [待补充]（红色文字）
5. 严禁编造数据"""


@router.post("/{project_id}/generate")
def generate_report(project_id: str, request: Request):
    """Generate report from current context. Returns paths for file dialog."""
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")

    config = get_config()
    report_lang = config.report_lang
    generator = ReportGenerator(output_dir=pm.project_dir(project_id) / "exports")
    html_content = safe_report_html(generator.generate_html(ctx, lang=report_lang))

    # Generate docx
    docx_path = generator.generate_docx(ctx, lang=report_lang)

    # Save to project folder as backup
    backup_html = pm.save_report(project_id, html_content, docx_path)

    # Collect user messages for validation summary
    user_messages = [m.content for m in ctx.messages if m.role == "user"]
    validator = ContentValidator(user_messages)
    step_contents = generator._extract_step_content(ctx)

    all_warnings = []
    for step_name, content in step_contents.items():
        for w in validator.validate(content):
            w["step"] = step_name
            all_warnings.append(w)

    return {
        "html_content": html_content,
        "backup_html_path": backup_html,
        "docx_path": docx_path,
        "project_id": project_id,
        "title": ctx.title,
        "warnings": all_warnings[:10],  # cap at 10 for API response
    }


@router.get("/{project_id}/preview", response_class=HTMLResponse)
def preview_report(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    # Prefer saved AI report, fallback to template generation
    reports = pm.list_reports(project_id)
    if reports:
        latest = reports[0]["html_path"]
        if Path(latest).exists():
            return HTMLResponse(content=safe_report_html(Path(latest).read_text(encoding="utf-8")))

    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")
    config = get_config()
    generator = ReportGenerator(output_dir=pm.project_dir(project_id) / "exports")
    html = generator.generate_html(ctx, lang=config.report_lang)
    return HTMLResponse(content=safe_report_html(html))


@router.get("/{project_id}/export/docx")
def export_docx(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")
    config = get_config()
    generator = ReportGenerator(output_dir=pm.project_dir(project_id) / "exports")
    path = generator.generate_docx(ctx, lang=config.report_lang)
    return FileResponse(
        path,
        filename=f"8D_{ctx.title}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/{project_id}/export/pdf")
def export_pdf(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")
    config = get_config()
    generator = ReportGenerator(output_dir=pm.project_dir(project_id) / "exports")
    path = generator.generate_pdf(ctx, lang=config.report_lang)
    return FileResponse(
        path,
        filename=f"8D_{ctx.title}.pdf",
        media_type="application/pdf",
    )


@router.get("/{project_id}/export/html")
def export_html(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")
    config = get_config()
    generator = ReportGenerator(output_dir=pm.project_dir(project_id) / "exports")
    html = generator.generate_html(ctx, lang=config.report_lang)
    today = datetime.now().strftime("%Y-%m-%d")
    path = pm.root / project_id / f"report_{today}.html"
    return {"html": safe_report_html(html), "backup_path": str(path)}


# ─── Report requirements ──────────────────────────────────────────

@router.put("/{project_id}/requirements")
def save_report_requirements(project_id: str, req: ReportRequirementsRequest, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")
    ctx.report_requirements = req.requirements
    ctx.update_date()
    pm.save_context(project_id, ctx)
    return {"status": "ok"}


@router.get("/{project_id}/requirements")
def get_report_requirements(project_id: str, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")
    return {
        "default_requirements": DEFAULT_REQUIREMENTS,
        "custom_requirements": ctx.report_requirements,
    }


# ─── LLM-based full report generation ─────────────────────────────

def _build_full_report_prompt(ctx, custom_requirements: str, lang: str = "zh") -> str:
    """Build a prompt for the LLM to generate a complete 8D report."""
    tbd = i18n_t(lang, "placeholder_tbd_empty")
    steps_data_parts = []
    for step in ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]:
        state = ctx.step_states[step]
        if state.ai_output.strip():
            steps_data_parts.append(f"### {step}\n{state.ai_output}")
        else:
            steps_data_parts.append(f"### {step}\n{tbd}")

    steps_text = "\n\n".join(steps_data_parts)

    requirements = i18n_t(lang, "report_default_requirements")
    if custom_requirements.strip():
        requirements += "\n" + custom_requirements.strip()

    if lang == "both":
        return _build_full_report_prompt_bilingual(ctx, steps_text, requirements)

    return _build_full_report_prompt_single(lang, steps_text, requirements)


def _build_full_report_prompt_single(lang: str, steps_text: str, requirements: str) -> str:
    """Build single-language report prompt."""
    if lang == "en":
        return f"""You are a senior 8D quality engineer. Generate a complete 8D report based on the phase data below.

## Report Requirements
{requirements}

## Phase Data
{steps_text}

## Output Format
Output a complete HTML document directly (starting from <!DOCTYPE html> to </html>), nothing else.

HTML requirements:
- Inline <style> tag for styles: font-family 'Segoe UI', Arial, sans-serif; body 14px; line-height 1.85; color #2c3e50
- Cover page: centered, dark divider line with small color block decoration below, "8D Problem Solving Report" in #1a5276, project name and date in gray
- Phase cards: white background, border-radius 6px, thin border #e8ecf0, light shadow, padding 20px-24px
- Phase title: left 4px #2980b9 vertical bar decoration, gradient background (#f0f6fb → white), font-size 17px
- Tables: border-collapse, dark header (#2c3e50) white text, alternating rows #f8f9fa, border #d5dbdf
- Max width 960px, centered, white background, generous paragraph spacing
- Bottom signature block: divider + Prepared/Reviewed/Approved three columns
- Flowcharts, sequence diagrams use Mermaid, wrapped in <pre class="mermaid">
- Missing info use <span style="color:red">[TBD]</span>
- Must include Mermaid CDN and fishbone rendering script in <head>:
  <script src="https://unpkg.com/mermaid@11/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'default', securityLevel:'loose'}});</script>
- Fishbone diagram (required for D4 root cause analysis): use JSON format:
  <script type="application/json" class="fishbone-data">
  {{
    "problem": "Problem description",
    "categories": [
      {{"name": "Man", "causes": ["cause 1", "cause 2"]}},
      {{"name": "Machine", "causes": ["cause 1", "cause 2"]}},
      {{"name": "Material", "causes": ["cause 1"]}},
      {{"name": "Method", "causes": ["cause 1", "cause 2"]}},
      {{"name": "Environment", "causes": ["cause 1"]}},
      {{"name": "Measurement", "causes": ["cause 1", "cause 2"]}}
    ]
  }}
  </script>
  <div class="fishbone-container"></div>

Output HTML directly, do not wrap in markdown code fences."""

    # Chinese (default)
    return f"""你是一名资深 8D 质量工程师，请根据以下各阶段数据，生成一份完整的 8D 报告。

## 报告要求
{requirements}

## 各阶段数据
{steps_text}

## 输出格式
请直接输出完整的 HTML 文档（从 <!DOCTYPE html> 开始，到 </html> 结束），不要包含其他内容。

HTML 要求：
- 使用内联 <style> 标签定义样式：字体 Microsoft YaHei，正文 14px，行高 1.85，文字色 #2c3e50
- 封面：居中，深色分割线下方有小色块装饰，"8D 问题解决报告" 用 #1a5276 色，项目名和日期灰色
- 每个阶段卡片：白色背景，圆角 6px，细边框 #e8ecf0，轻阴影，内边距 20px-24px
- 阶段标题：左侧 4px #2980b9 竖线装饰，渐变背景（#f0f6fb → 白色），字号 17px
- 表格：border-collapse，表头深色底（#2c3e50）白字，奇偶行交替 #f8f9fa 背景，边框 #d5dbdf
- 最大宽度 960px，居中，整体背景纯白，段落间距充足
- 底部签名栏：分隔线 + 编制/审核/批准 三栏
- 流程图、时序图用 Mermaid，<pre class="mermaid"> 包裹
- 缺失信息用 <span style="color:red">[待补充]</span>
- 必须在 <head> 中包含 Mermaid CDN 和 鱼骨图渲染脚本：
  <script src="https://unpkg.com/mermaid@11/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true, theme:'default', securityLevel:'loose'}});</script>
- 鱼骨图（D4 阶段根本原因分析必须用，系统会自动渲染）：使用以下 JSON 格式输出：
  <script type="application/json" class="fishbone-data">
  {{
    "problem": "问题描述",
    "categories": [
      {{"name": "人", "causes": ["原因1", "原因2"]}},
      {{"name": "机", "causes": ["原因1", "原因2"]}},
      {{"name": "料", "causes": ["原因1"]}},
      {{"name": "法", "causes": ["原因1", "原因2"]}},
      {{"name": "环", "causes": ["原因1"]}},
      {{"name": "测", "causes": ["原因1", "原因2"]}}
    ]
  }}
  </script>
  <div class="fishbone-container"></div>

直接输出 HTML，不要用 markdown 代码块包裹。"""


def _build_full_report_prompt_bilingual(ctx, steps_text: str, requirements: str) -> str:
    """Build bilingual report prompt (Chinese + English side by side)."""
    return f"""你是一名资深 8D 质量工程师，请根据以下各阶段数据，生成一份中英双语的 8D 报告。

## 报告要求
{requirements}
**额外要求**：报告中每个阶段、每个段落都需要中英双语对照，格式为中文在上、英文在下，英文用斜体灰色展示。

## 各阶段数据
{steps_text}

## 输出格式
请直接输出完整的 HTML 文档（从 <!DOCTYPE html> 开始，到 </html> 结束），不要包含其他内容。

HTML 要求：
- 使用内联 <style> 标签定义样式
- 中文部分字体 Microsoft YaHei，正文 14px，行高 1.85，文字色 #2c3e50
- 英文部分用 <p lang="en" style="font-style:italic; color:#7f8c8d"> 包裹，字体 Georgia
- 封面：居中，"8D 问题解决报告" / "8D Problem Solving Report"
- 底部签名栏：编制/审核/批准 + Prepared/Reviewed/Approved
- 其他样式要求与单语版本一致
- Mermaid CDN 和鱼骨图渲染脚本同上

直接输出 HTML，不要用 markdown 代码块包裹。"""


@router.post("/{project_id}/generate-with-llm")
def generate_report_with_llm(project_id: str, req: GenerateWithLLMRequest, request: Request):
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")

    config = get_config()
    llm = LLMProviderFactory.create(config)

    # Save requirements to project context
    if req.requirements:
        ctx.report_requirements = req.requirements
        ctx.update_date()
        pm.save_context(project_id, ctx)

    report_lang = config.report_lang
    prompt = _build_full_report_prompt(ctx, req.requirements, report_lang)

    try:
        raw = llm.chat(
            "You are a quality engineer. Respond ONLY with a complete HTML document. Never fabricate data.",
            prompt, []
        )
    except Exception:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="LLM call failed")

    # Extract HTML from response (strip code fences if LLM wrapped it)
    html = raw.strip()
    fence_match = re.search(r'```html?\s*([\s\S]*?)\s*```', html)
    if fence_match:
        html = fence_match.group(1).strip()
    # Ensure we have a valid HTML document
    if not html.startswith("<!DOCTYPE") and not html.startswith("<html"):
        # Wrap partial HTML
        html = f"<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n<title>{ctx.title}</title>\n</head>\n<body>\n{html}\n</body>\n</html>"

    # Inject fishbone.js into <head> for fishbone diagram rendering
    fishbone_path = Path(__file__).parent.parent / "report" / "templates" / "fishbone.js"
    if fishbone_path.exists():
        fishbone_js = fishbone_path.read_text(encoding="utf-8")
        fishbone_tag = f"<script>{fishbone_js}</script>"
        if "</head>" in html:
            html = html.replace("</head>", f"{fishbone_tag}\n</head>")

    # Sanitize Mermaid blocks for Mermaid 11.x compatibility
    generator = ReportGenerator(output_dir=pm.project_dir(project_id) / "exports")
    html = generator._sanitize_mermaid_html(html)

    report_content = raw  # Keep original for reference

    return {
        "report_content": report_content,
        "html": safe_report_html(html),
        "project_id": project_id,
        "title": ctx.title,
    }


class SaveReportRequest(BaseModel):
    html: str = Field(max_length=500000)


@router.post("/{project_id}/save-report")
def save_report(project_id: str, req: SaveReportRequest, request: Request):
    """Save confirmed report HTML. No LLM call."""
    pm = get_user_project_manager(request)
    ctx = pm.load_context(project_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Project context not found")

    html = req.html

    # Inject fishbone.js
    fishbone_path = Path(__file__).parent.parent / "report" / "templates" / "fishbone.js"
    if fishbone_path.exists():
        fishbone_js = fishbone_path.read_text(encoding="utf-8")
        fishbone_tag = f"<script>{fishbone_js}</script>"
        if "</head>" in html:
            html = html.replace("</head>", f"{fishbone_tag}\n</head>")

    backup_path = pm.save_report(project_id, safe_report_html(html))

    return {
        "status": "ok",
        "backup_path": backup_path,
        "title": ctx.title,
    }
