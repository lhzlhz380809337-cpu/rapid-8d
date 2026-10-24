"""Editable Word and deterministic PDF with Chinese glyphs and complete evidence notes."""
import html,io,re,textwrap,os
from pathlib import Path
from .domain import LABELS,now
from .fishbone import png,flatten
def blocks(markdown):
    lines=str(markdown).splitlines(); i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if "|" in line and i+1<len(lines) and re.match(r"^\s*\|?\s*:?-{3,}",lines[i+1]):
            rows=[[x.strip() for x in line.strip("|").split("|")]]; i+=2
            while i<len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([x.strip() for x in lines[i].strip().strip("|").split("|")]); i+=1
            yield "table",rows; continue
        if line.startswith("#"): yield "heading",line.lstrip("# ")
        else: yield "text",line
        i+=1
def clean(text): return str(text).replace("**","").replace(chr(96),"")
def sections(case):
    for s in case["stages"]:
        body=s.get("report_markdown") or "尚未填写。"
        yield f'{s["id"]} {s["title"]}  ·  {LABELS[s["status"]]}',list(blocks(body)),s
def appendix(case):
    rows=[]
    for src in case["sources"]:
        rows.append([src["id"],src["name"],src.get("coverage",""),"；".join(src.get("warnings",[]))])
    return rows
def root_rows(case):
    names={"unverified":"未验证","supported":"有支持","verified":"已验证","refuted":"已排除","inconclusive":"不确定"}
    return [[r["id"],("产生" if r["kind"]=="occurrence" else "逃逸")+" / "+names.get(r["verification"],r["verification"]),r["statement"],r.get("verification_record") or "待补验证记录","；".join(x["source_id"]+(" / "+str(x.get("locator")) if x.get("locator") else "") for x in r.get("source_refs",[]))] for r in case["root_causes"]]
def cause_rows(case):
    names={"suspected":"待验证","supported":"有支持","verified":"已验证","refuted":"已排除","inconclusive":"不确定"}
    return [[n["id"],c["label"],n["label"],names[n["status"]]] for c in case["fishbone"]["categories"] for n,d in flatten(c["causes"])]
def widths(rows,total):
    n=max(len(r) for r in rows)
    if rows[0][0]=="编号": ratios=[.13,.17,.50,.20] if n==4 else [.12,.16,.27,.30,.15]
    elif rows[0][0]=="来源": ratios=[.16,.27,.25,.32]
    else:
        weights=[max(5,min(35,max(len(str(r[i])) if i<len(r) else 0 for r in rows)))**.55 for i in range(n)]
        ratios=[w/sum(weights) for w in weights]
    return [total*x for x in ratios]
def export(case,kind):
    return make_docx(case) if kind=="docx" else make_pdf(case)
def make_docx(case):
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc=Document()
    sec=doc.sections[0]; sec.page_width=Inches(8.27);sec.page_height=Inches(11.69)
    sec.top_margin=sec.bottom_margin=Inches(.7); sec.left_margin=sec.right_margin=Inches(.7)
    for name in ("Normal","Title","Subtitle","Heading 1","Heading 2","Heading 3"):
        st=doc.styles[name]; st.font.name="Microsoft YaHei";st.font.color.rgb=RGBColor(0,0,0)
        st.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"),"Microsoft YaHei")
    # Remove template/theme title borders; they are visible only after Word renders.
    for node in doc.styles.element.xpath(".//w:pBdr"):
        node.getparent().remove(node)
    for node in doc.element.xpath(".//w:pBdr"):
        node.getparent().remove(node)
    doc.styles["Normal"].font.size=Pt(10)
    doc.styles["Normal"].paragraph_format.space_after=Pt(6)
    doc.styles["Title"].font.size=Pt(24);doc.styles["Heading 1"].font.size=Pt(15)
    doc.add_paragraph("8D 质量问题解决报告","Title")
    doc.add_paragraph(case["title"],"Subtitle")
    state={"draft":"草稿","reviewed_snapshot":"阶段复核报告","closed":"已结案"}[case["report_kind"]]
    doc.add_paragraph(f'{state}  |  案例 {case["id"]}  |  版本 {case["revision"]}  |  导出 {now()[:10]}')
    doc.add_paragraph("本报告汇总问题描述、调查证据、纠正措施与验证状态。各阶段的状态和关键开放项用于判断当前进展。")
    def table(rows):
        cols=max(len(r) for r in rows); t=doc.add_table(rows=0,cols=cols); t.style="Table Grid";t.autofit=False
        sizes=widths(rows,6.85)
        for i,width in enumerate(sizes):t.columns[i].width=Inches(width)
        borders=OxmlElement("w:tblBorders")
        for edge in ("top","left","bottom","right","insideH","insideV"):
            node=OxmlElement("w:"+edge);node.set(qn("w:val"),"single");node.set(qn("w:sz"),"4");node.set(qn("w:color"),"D9D9D9");borders.append(node)
        t._tbl.tblPr.append(borders)
        for ri,row in enumerate(rows):
            cells=t.add_row().cells
            for i,cell in enumerate(cells):cell.width=Inches(sizes[i])
            for ci,value in enumerate(row):
                cells[ci].text=clean(value)
                if ri==0:
                    for run in cells[ci].paragraphs[0].runs: run.bold=True
            if ri==0:
                repeat=OxmlElement("w:tblHeader"); t.rows[0]._tr.get_or_add_trPr().append(repeat)
            for cell in cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(3)
                    for run in p.runs: run.font.size=Pt(9)
        doc.add_paragraph()
    for heading,parts,s in sections(case):
        doc.add_heading(heading,1)
        for typ,content in parts:
            if typ=="table": table(content)
            elif typ=="heading": doc.add_heading(clean(content),2)
            else: doc.add_paragraph(clean(content))
        if s["id"]=="D4":
            doc.add_paragraph("鱼骨图（原因状态见图例，完整原因见下表）")
            img=png(case["fishbone"])
            from PIL import Image as PI
            iw,ih=PI.open(io.BytesIO(img)).size; scale=min(6.85/iw,7.5/ih)
            doc.add_picture(io.BytesIO(img),width=Inches(iw*scale),height=Inches(ih*scale))
            nodes=cause_rows(case)
            if nodes: table([["编号","分类","原因","状态"]]+nodes)
            if case["root_causes"]: table([["编号","类型 / 状态","根因","实际验证记录","来源"]]+root_rows(case))
        if s.get("review"): doc.add_paragraph("复核："+s["review"]["by"]+" / "+s["review"]["at"][:10]+"；"+s["review"]["note"])
    doc.add_heading("关键缺口与冲突",1)
    gaps=[g for g in case["gaps"] if not g.get("resolved")]
    if not gaps and not case["conflicts"]: doc.add_paragraph("当前记录中没有未解决的关键缺口；仍以各阶段复核状态为准。")
    for g in gaps: doc.add_paragraph(f'{g.get("stage","")} {g.get("description","")} — {g.get("suggested_next_step","")}')
    for c in case["conflicts"]: doc.add_paragraph(c.get("description","")+"；处理："+str(c.get("resolution") or "待核实"))
    doc.add_heading("证据索引",1)
    if case["sources"]: table([["来源","名称","提取范围","限制"]]+appendix(case))
    else: doc.add_paragraph("尚未录入来源资料。")
    footer=sec.footer.paragraphs[0]; footer.alignment=2
    footer.add_run("Rapid 8D  ·  ")
    field=OxmlElement("w:fldSimple");field.set(qn("w:instr"),"PAGE");footer._p.append(field)
    result=io.BytesIO();doc.save(result);return result.getvalue()
def make_pdf(case):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    fontpath=Path(os.environ.get("WINDIR",r"C:\Windows"))/"Fonts"/"msyh.ttc"
    if not fontpath.exists():fontpath=fontpath.with_name("simsun.ttc")
    if "RapidCJK" not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont("RapidCJK",str(fontpath),subfontIndex=0))
    styles=getSampleStyleSheet()
    for name in ("Normal","Title","Heading1","Heading2"):
        styles[name].fontName="RapidCJK";styles[name].wordWrap="CJK";styles[name].textColor=colors.black
    styles["Heading1"].keepWithNext=True;styles["Heading2"].keepWithNext=True
    styles["Normal"].fontSize=10;styles["Normal"].leading=16
    styles["Heading1"].fontSize=15;styles["Heading1"].leading=21
    small=ParagraphStyle("SmallCJK",parent=styles["Normal"],fontSize=8,leading=12)
    def p(text,style="Normal"): return Paragraph(html.escape(clean(text)).replace("\n","<br/>"),styles[style])
    story=[p("8D 质量问题解决报告","Title"),p(case["title"],"Heading1")]
    state={"draft":"草稿","reviewed_snapshot":"阶段复核报告","closed":"已结案"}[case["report_kind"]]
    story.extend([p(f'{state} | {case["id"]} | 版本 {case["revision"]} | {now()[:10]}'),Spacer(1,12),
        p("本报告汇总问题描述、调查证据、纠正措施与验证状态。各阶段状态和关键开放项反映当前进展。"),Spacer(1,10)])
    def table(rows):
        cols=max(len(r) for r in rows); data=[]
        for row in rows:
            data.append([Paragraph(html.escape(clean(row[c] if c<len(row) else "")),small) for c in range(cols)])
        t=Table(data,colWidths=widths(rows,490),repeatRows=1,hAlign="LEFT",splitInRow=1)
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#edf3f2")),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#c7d4d2")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story.extend([t,Spacer(1,10)])
    for heading,parts,s in sections(case):
        story.append(p(heading,"Heading1"))
        for typ,content in parts:
            if typ=="table": table(content)
            else: story.extend([p(content,"Heading2" if typ=="heading" else "Normal"),Spacer(1,5)])
        if s["id"]=="D4":
            raw=png(case["fishbone"])
            from PIL import Image as PI
            im=PI.open(io.BytesIO(raw)); w,h=im.size; scale=min(490/w,540/h)
            story.extend([KeepTogether([p("鱼骨图 原因状态见图例"),Image(io.BytesIO(raw),width=w*scale,height=h*scale)]),Spacer(1,10)])
            nodes=cause_rows(case)
            if nodes: table([["编号","分类","原因","状态"]]+nodes)
            if case["root_causes"]: table([["编号","类型 / 状态","根因","实际验证记录","来源"]]+root_rows(case))
        if s.get("review"): story.append(p("复核："+s["review"]["by"]+"；"+s["review"]["note"]))
    story.append(p("关键缺口与冲突","Heading1"))
    gaps=[g for g in case["gaps"] if not g.get("resolved")]
    if not gaps and not case["conflicts"]: story.append(p("当前记录中没有未解决的关键缺口；仍以各阶段复核状态为准。"))
    for g in gaps: story.append(p(f'{g.get("stage","")} {g.get("description","")} — {g.get("suggested_next_step","")}'))
    for c in case["conflicts"]: story.append(p(c.get("description","")+"；处理："+str(c.get("resolution") or "待核实")))
    story.append(p("证据索引","Heading1"))
    if case["sources"]: table([["来源","名称","提取范围","限制"]]+appendix(case))
    else: story.append(p("尚未录入来源资料。"))
    output=io.BytesIO()
    def footer(canvas,doc):
        canvas.setFont("RapidCJK",9);canvas.setFillColor(colors.HexColor("#60716c"));canvas.drawRightString(545,26,f"Rapid 8D · {doc.page}")
    SimpleDocTemplate(output,pagesize=A4,leftMargin=52,rightMargin=52,topMargin=42,bottomMargin=42,title=case["title"],author="Rapid 8D").build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()
