"""Reports are untrusted documents. Keep content, remove executable/external resources."""
from html.parser import HTMLParser
import bleach
import json
import re
from html import escape


class ContentOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "iframe", "object"}:
            self.skip += 1
        elif not self.skip:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in {"script", "style", "iframe", "object"}:
            self.skip = max(0, self.skip - 1)
        elif not self.skip:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def handle_entityref(self, name):
        if not self.skip:
            self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if not self.skip:
            self.parts.append(f"&#{name};")


def safe_report_html(source: str) -> str:
    def fishbone_table(match):
        try:
            value = json.loads(match.group(1))
            rows = "".join("<tr><th>" + escape(str(item.get("name", ""))) + "</th><td>" + escape("；".join(map(str,item.get("causes", [])))) + "</td></tr>" for item in value.get("categories", []))
            return "<h3>根因分析：" + escape(str(value.get("problem", ""))) + "</h3><table>" + rows + "</table>"
        except (ValueError, TypeError, AttributeError):
            return "<p>根因图数据无法解析，请核对原始内容。</p>"
    source = re.sub(r'<script\b[^>]*class=["\']fishbone-data["\'][^>]*>(.*?)</script>', fishbone_table, source, flags=re.I | re.S)
    source = source.replace('<p class="ai-notice">AI 辅助生成内容 · 请由责任人核实事实、数据和措施后使用。</p>', '')
    parser = ContentOnly()
    parser.feed(source)
    content = bleach.clean("".join(parser.parts), tags={
        "h1", "h2", "h3", "h4", "p", "br", "div", "span", "section", "article",
        "strong", "b", "em", "i", "u", "ul", "ol", "li", "blockquote", "pre", "code",
        "table", "thead", "tbody", "tfoot", "tr", "th", "td", "hr", "sup", "sub"
    }, attributes={"*": ["class", "lang"], "td": ["colspan", "rowspan"], "th": ["colspan", "rowspan"]}, strip=True)
    return '''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="generator" content="Rapid 8D — AI assisted">
    <style>body{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;margin:24px;color:#263849;line-height:1.8}
    table{border-collapse:collapse;width:100%;margin:12px 0}td,th{border:1px solid #ccd6df;padding:8px;text-align:left}
    th{background:#edf3f8}h1,h2,h3{color:#1a5276}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6f8;padding:12px}
    .ai-notice{font-size:12px;color:#5b6875;border-bottom:1px solid #ccd6df;padding-bottom:8px}</style></head><body>
    <p class="ai-notice">AI 辅助生成内容 · 请由责任人核实事实、数据和措施后使用。</p>''' + content + "</body></html>"
