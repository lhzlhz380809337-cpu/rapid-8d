"""Report exporter — handles PDF export via WeasyPrint."""

from pathlib import Path
from backend.report.generator import ReportGenerator


def export_pdf(title: str, steps_data: dict[str, str], company_name: str = "") -> str:
    try:
        from weasyprint import HTML
    except ImportError:
        raise ImportError("WeasyPrint is required for PDF export. Install it via: pip install weasyprint")

    generator = ReportGenerator()
    html_content = generator.generate_html(title, steps_data, company_name)

    output_dir = Path(__file__).parent.parent / "data" / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"8D_{title}.pdf"

    HTML(string=html_content).write_pdf(str(path))
    return str(path)
