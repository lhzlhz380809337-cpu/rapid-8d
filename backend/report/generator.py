"""8D Report generator — assembles context data into formatted reports with validation."""

from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from backend.project.context import ProjectContext
from backend.report.validator import ContentValidator
from backend.i18n import t as i18n_t


STEPS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

def get_step_labels(lang: str = "zh") -> dict[str, str]:
    labels = i18n_t(lang, "step_labels")
    return labels if isinstance(labels, dict) else i18n_t("zh", "step_labels")


class ReportGenerator:
    def __init__(self, output_dir=None):
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)
        from backend.storage import data_root
        self.output_dir = output_dir or (data_root() / "exports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _extract_step_content(self, ctx: ProjectContext, lang: str = "zh") -> dict[str, str]:
        """Extract confirmed AI output per step. Never fall back to chat history."""
        result = {}
        for step in STEPS:
            content = ctx.step_states[step].ai_output.strip()
            if content:
                result[step] = content
            else:
                result[step] = i18n_t(lang, "unfilled_ai_output")
        return result

    def _sanitize_mermaid_html(self, html: str) -> str:
        """Replace chars inside <pre class="mermaid"> that confuse Mermaid 11.x parser."""
        import re

        def _sanitize_block(match):
            code = match.group(1)
            code = re.sub(r'\[([^\]]*)\]', lambda m: '[' + m.group(1).replace('(', '（').replace(')', '）').replace('"', '＂') + ']', code)
            return f'<pre class="mermaid">{code}</pre>'

        return re.sub(
            r'<pre class="mermaid">([\s\S]*?)</pre>',
            _sanitize_block,
            html
        )

    def _md_to_html(self, content: str) -> str:
        """Convert markdown content to HTML."""
        import re
        html = content

        # Mermaid code blocks
        html = re.sub(
            r'```mermaid\s*([\s\S]*?)```',
            r'<pre class="mermaid">\1</pre>',
            html
        )

        # Other code blocks
        html = re.sub(
            r'```(\w*)\s*([\s\S]*?)```',
            r'<pre><code class="language-\1">\2</code></pre>',
            html
        )

        # Headers
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # Images
        html = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            r'<img alt="\1" src="\2" style="max-width:100%">',
            html
        )

        # Links
        html = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            r'<a href="\2">\1</a>',
            html
        )

        # Tables
        html = self._convert_tables(html)
        return self._wrap_paragraph_blocks(html)

    def _wrap_paragraph_blocks(self, html: str) -> str:
        """Wrap plain-text blocks in paragraphs without disturbing block tags."""
        block_prefixes = ("<h1", "<h2", "<h3", "<h4", "<pre", "<table", "<img", "<p", "<ul", "<ol", "<blockquote")
        result = []
        text_lines: list[str] = []
        raw_lines = html.split("\n")
        in_block = False

        def flush_text_lines():
            nonlocal text_lines
            if not text_lines:
                return
            paragraph = " ".join(line.strip() for line in text_lines if line.strip())
            if paragraph:
                result.append(f"<p>{paragraph}</p>")
            text_lines = []

        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                flush_text_lines()
                if not in_block and (not result or result[-1] != ""):
                    result.append("")
                continue

            if in_block:
                result.append(line)
                if (
                    stripped.startswith("</pre>")
                    or stripped.startswith("</table>")
                    or stripped.startswith("</ul>")
                    or stripped.startswith("</ol>")
                    or stripped.startswith("</blockquote>")
                ):
                    in_block = False
                continue

            if stripped.startswith(block_prefixes):
                flush_text_lines()
                result.append(line)
                if (
                    stripped.startswith("<pre")
                    and "</pre>" not in stripped
                ) or (
                    stripped.startswith("<table")
                    and "</table>" not in stripped
                ) or (
                    stripped.startswith("<ul")
                    and "</ul>" not in stripped
                ) or (
                    stripped.startswith("<ol")
                    and "</ol>" not in stripped
                ) or (
                    stripped.startswith("<blockquote")
                    and "</blockquote>" not in stripped
                ):
                    in_block = True
                continue

            text_lines.append(line)

        flush_text_lines()
        return "\n".join(result)

    def generate_html(
        self, ctx: ProjectContext, company_name: str = "", doc_number: str = "", lang: str = "zh"
    ) -> str:
        template = self.env.get_template("report.html")
        step_contents = self._extract_step_content(ctx, lang)

        user_messages = [m.content for m in ctx.messages if m.role == "user"]

        labels = get_step_labels(lang)
        tbd = i18n_t(lang, "placeholder_tbd")

        steps = []
        warnings_all = []
        for step_name in STEPS:
            content = step_contents.get(step_name, "")

            validator = ContentValidator(user_messages)
            validation_warnings = validator.validate(content)
            if validation_warnings:
                for w in validation_warnings:
                    w["step"] = step_name
                warnings_all.extend(validation_warnings)

            if not content.strip():
                content = tbd

            rendered = self._sanitize_mermaid_html(self._md_to_html(content))

            steps.append({
                "name": step_name,
                "label": labels.get(step_name, step_name),
                "content": rendered,
                "has_warnings": len(validation_warnings) > 0,
            })

        doc_labels = i18n_t(lang, "doc_labels")
        cover_title = i18n_t(lang, "report_cover_title")

        return template.render(
            title=ctx.title,
            date=datetime.now().strftime("%Y-%m-%d"),
            company_name=company_name or tbd,
            doc_number=doc_number,
            steps=steps,
            warnings=warnings_all,
            doc_labels=doc_labels,
            cover_title=cover_title,
        )

    def wrap_html(self, title: str, markdown_content: str) -> str:
        """Wrap LLM-generated markdown content in a simple HTML page."""
        html_content = self._sanitize_mermaid_html(self._md_to_html(markdown_content))

        css_path = Path(__file__).parent / "templates" / "report_styles.css"
        styles = ""
        if css_path.exists():
            styles = f"<style>{css_path.read_text(encoding='utf-8')}</style>"

        fishbone_path = Path(__file__).parent / "templates" / "fishbone.js"
        fishbone_js = ""
        if fishbone_path.exists():
            fishbone_js = f"<script>{fishbone_path.read_text(encoding='utf-8')}</script>"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://unpkg.com/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:'default', securityLevel:'loose'}});</script>
{fishbone_js}
{styles}
<style>
  body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 900px; margin: 0 auto; padding: 40px 20px; color: #333; line-height: 1.8; }}
  h1 {{ color: #1a5276; border-bottom: 2px solid #2980b9; padding-bottom: 8px; }}
  h2 {{ color: #1a5276; border-bottom: 1px solid #ddd; padding-bottom: 6px; }}
  h3 {{ color: #2980b9; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #2980b9; color: #fff; }}
  tr:nth-child(even) {{ background: #f8f8f8; }}
  pre.mermaid {{ background: #f5f5f5; padding: 12px; border-radius: 4px; }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""

    def _convert_tables(self, html: str) -> str:
        """Convert markdown tables to HTML tables."""
        lines = html.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('|') and line.endswith('|'):
                # Start of a table
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1

                if len(table_lines) >= 2:
                    # Header row
                    header_cells = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                    # Skip separator row (|---|---|)
                    data_rows = []
                    for tl in table_lines[1:]:
                        cells = [c.strip() for c in tl.split('|')[1:-1]]
                        if cells and not all(c.replace('-', '').replace(':', '') == '' for c in cells):
                            data_rows.append(cells)

                    html_table = '<table>\n<thead>\n<tr>\n'
                    for cell in header_cells[:len(data_rows[0])] if data_rows else header_cells:
                        html_table += f'<th>{cell}</th>\n'
                    html_table += '</tr>\n</thead>\n<tbody>\n'
                    for row in data_rows:
                        html_table += '<tr>\n'
                        for cell in row[:len(header_cells)]:
                            html_table += f'<td>{cell}</td>\n'
                        html_table += '</tr>\n'
                    html_table += '</tbody>\n</table>'
                    result.append(html_table)
                    continue
            result.append(lines[i])
            i += 1
        return '\n'.join(result)

    def generate_docx(
        self, ctx: ProjectContext, company_name: str = "", lang: str = "zh"
    ) -> str:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()
        doc.core_properties.comments = "AI 辅助生成内容，请由责任人核实后使用。"
        doc.core_properties.keywords = "AI-assisted, Rapid 8D"
        doc.add_paragraph("AI 辅助生成内容 · 请由责任人核实事实、数据和措施后使用。")
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Microsoft YaHei"
        font.size = Pt(11)

        cover_title = i18n_t(lang, "report_cover_title")
        tbd = i18n_t(lang, "placeholder_tbd")
        labels = get_step_labels(lang)

        # Cover page
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title_para.add_run(cover_title)
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x1A, 0x52, 0x76)

        subtitle = doc.add_paragraph()
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle.add_run(ctx.title).font.size = Pt(14)

        date_label = i18n_t(lang, "doc_labels").get("date", "Date")
        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        meta.add_run(f"{date_label}: {datetime.now().strftime('%Y-%m-%d')}").font.size = Pt(10)

        doc.add_page_break()

        step_contents = self._extract_step_content(ctx, lang)
        for step_name in STEPS:
            content = step_contents.get(step_name, "")
            heading = doc.add_heading(labels.get(step_name, step_name), level=2)
            for run in heading.runs:
                run.font.color.rgb = RGBColor(0x1A, 0x52, 0x76)

            text = content.strip() if content.strip() else tbd
            self._render_markdown_to_docx(doc, text)

        path = self.output_dir / "report.docx"
        doc.save(str(path))
        return str(path)

    def _render_markdown_to_docx(self, doc, markdown_text: str):
        """Render markdown text into python-docx elements (headings, tables, lists, code)."""
        import re
        from docx.shared import Pt, RGBColor, Inches

        lines = markdown_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            # Code block
            if stripped.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                i += 1  # skip closing ```
                for cl in code_lines:
                    if cl.strip():
                        p = doc.add_paragraph()
                        p.paragraph_format.left_indent = Inches(0.3)
                        run = p.add_run(cl)
                        run.font.name = 'Courier New'
                        run.font.size = Pt(9)
                        run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
                continue

            # Table — collect consecutive |...| lines
            if stripped.startswith('|') and stripped.endswith('|'):
                table_lines = []
                while i < len(lines):
                    s = lines[i].strip()
                    if s.startswith('|') and s.endswith('|'):
                        table_lines.append(s)
                        i += 1
                    else:
                        break
                self._render_table_to_docx(doc, table_lines)
                continue

            # Heading
            if stripped.startswith('#'):
                level = 0
                for ch in stripped:
                    if ch == '#':
                        level += 1
                    else:
                        break
                heading_text = stripped[level:].strip()
                heading_text = re.sub(r'\s+#+\s*$', '', heading_text)
                h = doc.add_heading(heading_text, level=min(level, 4))
                for run in h.runs:
                    run.font.color.rgb = RGBColor(0x1A, 0x52, 0x76)
                i += 1
                continue

            # Unordered list
            list_match = re.match(r'^[-*]\s+(.+)', stripped)
            if list_match:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                self._add_inline_runs(p, '• ' + list_match.group(1))
                i += 1
                continue

            # Numbered list
            num_match = re.match(r'^(\d+)\.\s+(.+)', stripped)
            if num_match:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(0.3)
                self._add_inline_runs(p, num_match.group(1) + '. ' + num_match.group(2))
                i += 1
                continue

            # Regular paragraph
            self._add_inline_runs(doc.add_paragraph(), stripped)
            i += 1

    def _render_table_to_docx(self, doc, table_lines: list):
        """Convert markdown table lines to a python-docx table with formatting."""
        from docx.shared import Pt, RGBColor
        if len(table_lines) < 2:
            return
        header_cells = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        data_rows = []
        for tl in table_lines[1:]:
            cells = [c.strip() for c in tl.split('|')[1:-1]]
            if cells and not all(c.replace('-', '').replace(':', '').replace(' ', '') == '' for c in cells):
                data_rows.append(cells)
        if not data_rows:
            return
        ncols = max(len(header_cells), len(data_rows[0]) if data_rows else 1)
        table = doc.add_table(rows=1 + len(data_rows), cols=ncols)
        table.style = 'Light Grid Accent 1'
        # Header
        for j, cell_text in enumerate(header_cells[:ncols]):
            cell = table.rows[0].cells[j]
            cell.text = ''
            run = cell.paragraphs[0].add_run(cell_text)
            run.font.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        # Data rows
        for row_idx, row_data in enumerate(data_rows):
            for j, cell_text in enumerate(row_data[:ncols]):
                cell = table.rows[row_idx + 1].cells[j]
                cell.text = ''
                run = cell.paragraphs[0].add_run(cell_text)
                run.font.size = Pt(10)

    def _add_inline_runs(self, para, text: str):
        """Add runs to a paragraph with inline formatting (**bold**, *italic*, `code`, [links])."""
        import re
        from docx.shared import Pt, RGBColor

        pattern = r'(!\[([^\]]*)\]\(([^)]+)\)|\*\*(.+?)\*\*|`(.+?)`|\[([^\]]+)\]\(([^)]+)\)|\*(.+?)\*)'
        last_end = 0
        has_match = False
        for m in re.finditer(pattern, text):
            has_match = True
            if m.start() > last_end:
                run = para.add_run(text[last_end:m.start()])
                run.font.size = Pt(11)
            if m.group(1).startswith('!['):
                # Image → placeholder
                run = para.add_run(f'[Image: {m.group(2)}]')
                run.font.italic = True
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
            elif m.group(1).startswith('**'):
                run = para.add_run(m.group(4))
                run.font.bold = True
                run.font.size = Pt(11)
            elif m.group(1).startswith('`'):
                run = para.add_run(m.group(5))
                run.font.name = 'Courier New'
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0xC7, 0x25, 0x4E)
            elif m.group(1).startswith('['):
                run = para.add_run(m.group(6))
                run.font.underline = True
                run.font.color.rgb = RGBColor(0x29, 0x80, 0xB9)
                run.font.size = Pt(11)
            elif m.group(8):
                run = para.add_run(m.group(8))
                run.font.italic = True
                run.font.size = Pt(11)
            last_end = m.end()
        if last_end < len(text):
            run = para.add_run(text[last_end:])
            run.font.size = Pt(11)
        if not has_match:
            run = para.add_run(text)
            run.font.size = Pt(11)

    def generate_pdf(
        self, ctx: ProjectContext, company_name: str = "", lang: str = "zh"
    ) -> str:
        """Generate a PDF from the HTML report via system browser headless mode."""
        import subprocess
        import tempfile

        html = self.generate_html(ctx, company_name=company_name, lang=lang)
        doc_labels = i18n_t(lang, "doc_labels")
        cover_title = i18n_t(lang, "report_cover_title")
        page_title = f"{cover_title} - {ctx.title}"

        css_path = Path(__file__).parent / "templates" / "report_styles.css"
        styles = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

        full_html = f"""<!DOCTYPE html>
<html lang="{'zh-CN' if lang == 'zh' else 'en'}">
<head>
<meta charset="utf-8">
<title>{page_title}</title>
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{
    font-family: 'Microsoft YaHei', 'SimSun', sans-serif;
    max-width: 100%;
    margin: 0 auto;
    color: #333;
    line-height: 1.8;
    font-size: 12px;
  }}
  h1 {{ color: #1a5276; border-bottom: 2px solid #2980b9; padding-bottom: 8px; }}
  h2 {{ color: #1a5276; border-bottom: 1px solid #ddd; padding-bottom: 6px; }}
  h3 {{ color: #2980b9; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 11px; }}
  th {{ background: #2980b9; color: #fff; }}
  tr:nth-child(even) {{ background: #f8f8f8; }}
  pre.mermaid {{
    background: #f5f5f5; padding: 12px; border-radius: 4px;
    font-family: 'Courier New', monospace; font-size: 10px;
    white-space: pre-wrap; border: 1px solid #ddd;
  }}
  .cover-title {{ text-align: center; font-size: 24px; font-weight: bold; color: #1a5276; margin-top: 100px; }}
  .cover-subtitle {{ text-align: center; font-size: 16px; margin-top: 20px; }}
  .cover-date {{ text-align: center; font-size: 12px; color: #666; margin-top: 10px; }}
  .warning {{ background: #fef9e7; border: 1px solid #f9e79f; padding: 8px; border-radius: 4px; margin: 8px 0; }}
  p {{ margin: 6px 0; }}
  {styles}
</style>
</head>
<body>
<div class="cover-title">{cover_title}</div>
<div class="cover-subtitle">{ctx.title}</div>
<div class="cover-date">{doc_labels.get('date', 'Date')}: {datetime.now().strftime('%Y-%m-%d')}</div>
<div style="page-break-before: always;"></div>
{html}
</body>
</html>"""

        path = self.output_dir / "report.pdf"

        from backend.report.safety import safe_report_html
        safe_html = safe_report_html(full_html)
        try:
            from weasyprint import HTML
        except (ImportError, OSError):
            from backend.report.pdf_fallback import write_text_pdf
            write_text_pdf(safe_html, str(path))
            return str(path)
        def deny_network(url, *args, **kwargs):
            raise ValueError("External resources are disabled in PDF export")
        HTML(string=safe_html, url_fetcher=deny_network).write_pdf(str(path))
        return str(path)
