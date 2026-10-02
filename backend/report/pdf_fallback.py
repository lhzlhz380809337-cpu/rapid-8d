"""Portable text PDF when the OS lacks Pango. No URLs or executable HTML are loaded."""
import re
from html import escape
from html.parser import HTMLParser
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

class TextReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in {"style", "script"}: self.skip = True
        if tag in {"p", "div", "br", "tr", "li", "h1", "h2", "h3"}: self.parts.append("\n")
        if tag in {"td", "th"}: self.parts.append(" | ")
    def handle_endtag(self, tag):
        if tag in {"style", "script"}: self.skip = False
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

def write_text_pdf(html: str, path: str):
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    style = ParagraphStyle("Chinese", fontName="STSong-Light", fontSize=10, leading=17, wordWrap="CJK")
    parser = TextReader(); parser.feed(html)
    story = [Paragraph("Rapid 8D · 文字版报告（图表以源文本呈现）", style), Spacer(1, 12)]
    for line in "".join(parser.parts).splitlines():
        line = line.strip()
        if line:
            story.append(Paragraph(escape(line), style))
            story.append(Spacer(1, 4))
    SimpleDocTemplate(path, pagesize=A4, title="Rapid 8D — AI assisted report").build(story)
