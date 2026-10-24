"""One diagram geometry shared by SVG preview and high-resolution report image."""
import html,io,math,os,textwrap
from pathlib import Path
COLORS={"suspected":"#b67b2f","supported":"#29749a","verified":"#207257","refuted":"#869099","inconclusive":"#875c9c"}
WORDS={"suspected":"待验证","supported":"有支持","verified":"已验证","refuted":"已排除","inconclusive":"不确定"}
def flatten(nodes,depth=0):
    for n in nodes:
        yield n,depth
        yield from flatten(n.get("children",[]),depth+1)
def layout(tree):
    cats=tree.get("categories",[]); cols=max(1,math.ceil(len(cats)/2)); width=max(1100,cols*430+360)
    maxrows=max([len(list(flatten(c.get("causes",[])))) for c in cats]+[1])
    half=max(250,maxrows*70+100); height=half*2+100; mid=half+25
    items=[]
    def line(x1,y1,x2,y2,color="#9dafb1",weight=2): items.append(("line",(x1,y1,x2,y2,color,weight)))
    def text(x,y,value,size=19,color="#223c43"): items.append(("text",(x,y,str(value),size,color)))
    line(35,mid,width-250,mid,"#2d6262",4)
    line(width-266,mid-9,width-250,mid,"#2d6262",4); line(width-266,mid+9,width-250,mid,"#2d6262",4)
    for j,c in enumerate(cats):
        col=j//2; sign=-1 if j%2==0 else 1
        base=160+col*430; end=base+150
        line(base,mid,end,mid+sign*(half-35),"#487b7a",3)
        text(base+75,mid+sign*(half-10),c.get("label","分类"),24,"#154f50")
        for k,(node,depth) in enumerate(flatten(c.get("causes",[]))):
            y=mid+sign*(55+k*70)
            bx=base+(abs(y-mid)/(half-35))*150
            line(bx,y,bx+225,y,COLORS.get(node.get("status"),"#9dafb1"))
            label=("  "*min(depth,3))+node.get("label","")
            label=label[:22]+("…" if len(label)>22 else "")
            for off,part in enumerate(textwrap.wrap(label,11)[:2] or [""]):
                text(bx+10,y-38+off*23,part,19,COLORS.get(node.get("status"),"#334"))
            text(bx+15,y+6,f'{node["id"]} · {WORDS.get(node.get("status"),"待验证")}',15,COLORS.get(node.get("status"),"#334"))
    problem=tree.get("problem_statement") or "问题待定义"
    for i,part in enumerate(textwrap.wrap(problem,9)[:6]): text(width-232,mid-65+i*27,part,23,"#154f50")
    legend="   ".join(WORDS[x] for x in COLORS)
    text(36,height-30,"原因状态  "+legend,18)
    if not cats: text(120,mid-45,"尚未分析原因 · 从资料与证据开始",26)
    return width,height,items
def svg(tree):
    w,h,items=layout(tree)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="鱼骨图"><rect width="100%" height="100%" fill="#fff"/>']
    for kind,args in items:
        if kind=="line":
            x1,y1,x2,y2,c,sw=args; out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}"/>')
        else:
            x,y,t,size,c=args; out.append(f'<text x="{x}" y="{y}" dominant-baseline="hanging" font-family="Microsoft YaHei,Arial,sans-serif" font-size="{size}" fill="{c}">{html.escape(t)}</text>')
    return "".join(out)+"</svg>"
def png(tree):
    from PIL import Image,ImageDraw,ImageFont
    w,h,items=layout(tree); scale=1.5
    image=Image.new("RGB",(int(w*scale),int(h*scale)),"white"); draw=ImageDraw.Draw(image)
    fontpath=Path(os.environ.get("WINDIR",r"C:\Windows"))/"Fonts"/"msyh.ttc"
    if not fontpath.exists(): fontpath=Path(os.environ.get("WINDIR",r"C:\Windows"))/"Fonts"/"simsun.ttc"
    fonts={}
    for kind,args in items:
        if kind=="line":
            x1,y1,x2,y2,c,sw=args; draw.line((x1*scale,y1*scale,x2*scale,y2*scale),fill=c,width=max(1,int(sw*scale)))
        else:
            x,y,t,size,c=args
            if size not in fonts: fonts[size]=ImageFont.truetype(str(fontpath),int(size*scale))
            draw.text((x*scale,y*scale),t,font=fonts[size],fill=c)
    output=io.BytesIO(); image.save(output,format="PNG")
    return output.getvalue()
