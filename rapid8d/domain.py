"""Case integrity and review rules; no model response can silently close a case."""
from __future__ import annotations
import copy, datetime, json, uuid, re

TITLES = ["团队与职责", "问题描述", "临时围堵", "根因分析", "永久措施", "实施与验证", "预防再发", "结案与认可"]
FILES = ["d1_team", "d2_problem", "d3_containment", "d4_root_cause", "d5_corrective", "d6_implement", "d7_prevent", "d8_recognize"]
STATES = {"not_started", "in_progress", "blocked", "ready_for_review", "complete"}
EVIDENCE = {"suspected", "supported", "verified", "refuted", "inconclusive"}
LABELS = {"not_started":"未开始","in_progress":"进行中","blocked":"待补证据","ready_for_review":"待复核","complete":"已复核"}
CHECKS = {
"D1":["成员和职责是真实记录","负责人及必要授权已确认"],
"D2":["问题定义、范围、单位和分母已核对","关键矛盾已解决，未知边界已说明"],
"D3":["必要范围已围堵且有实施证据","检出能力和持续控制已核实"],
"D4":["产生与逃逸分析均已核对，或有合理的不适用说明","因果验证记录足够且已检查替代解释"],
"D5":["措施与已验证根因对应","选择理由及适用的验证结果已核对"],
"D6":["实施记录及效果数据已核对","验证范围和围堵退出条件有依据"],
"D7":["关键预防项及必要横向展开已完成","文件、现场执行和维护责任已核对"],
"D8":["所有关键阶段已复核且关键开放项已解决","有权人员已批准结案，必要客户接受已取得"]
}
class UserError(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status
def valid_id(value):
    return isinstance(value,str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}",value) is not None
def now(): return datetime.datetime.now().astimezone().isoformat(timespec="seconds")
def uid(prefix=""): return prefix + uuid.uuid4().hex[:12]
def new_case(title, mode="guided", language="zh"):
    title = str(title).strip()
    if not title: raise UserError("请输入案例名称。")
    if mode not in ("guided","import") or language not in ("zh","bilingual","en"): raise UserError("案例选项无效。")
    return dict(id=uid("C"), title=title[:160], mode=mode, language=language, revision=0,
        created_at=now(), updated_at=now(), report_kind="draft",
        stages=[dict(id=f"D{i+1}",title=t,status="not_started",report_markdown="",review=None,manual=False) for i,t in enumerate(TITLES)],
        sources=[],messages=[],facts=[],hypotheses=[],root_causes=[],actions=[],gaps=[],conflicts=[],
        fishbone=dict(problem_statement="",categories=[]), history_note="")
def stage(case, sid):
    for item in case["stages"]:
        if item["id"] == sid: return item
    raise UserError("阶段不存在。")
def invalidate(case, sid):
    start = int(sid[1:])-1
    affected = range(start,8) if sid in ("D2","D4") else [start,7]
    for i in set(affected):
        s = case["stages"][i]
        if s["status"] == "complete":
            s["status"] = "ready_for_review"
        s["review"] = None
    case["report_kind"]="draft"
def validate_refs(refs, source_ids):
    if not isinstance(refs,list): raise UserError("来源引用必须是数组。")
    for r in refs:
        if not isinstance(r,dict) or r.get("source_id") not in source_ids:
            raise UserError("包含不存在的来源引用，已阻止采用。")
        if r.get("locator") is not None and not isinstance(r["locator"],str): raise UserError("来源定位格式错误。")
        if r.get("quote") is not None and not isinstance(r["quote"],str): raise UserError("来源摘录格式错误。")
def validate_fishbone(tree, sources, roots=None):
    if not isinstance(tree,dict) or not isinstance(tree.get("categories"),list): raise UserError("鱼骨结构无效。")
    if len(tree["categories"])>12: raise UserError("鱼骨图最多12个分类，请拆分复杂问题。")
    ids=set(); count=0
    def walk(nodes,depth):
        nonlocal count
        if not isinstance(nodes,list) or depth>5: raise UserError("鱼骨层级过深或格式错误。")
        for n in nodes:
            count+=1
            if count>120: raise UserError("鱼骨原因超过120项，请分案例分析。")
            if not isinstance(n,dict) or not str(n.get("label","")).strip(): raise UserError("鱼骨原因名称不能为空。")
            if not valid_id(n.get("id")) or n["id"] in ids: raise UserError("鱼骨原因编号重复或缺失。")
            ids.add(n["id"])
            if n.get("status") not in EVIDENCE: raise UserError("原因状态无效。")
            validate_refs(n.get("source_refs",[]),sources)
            if roots is not None and any(x not in roots for x in n.get("root_cause_refs",[])): raise UserError("鱼骨图引用了不存在的根因。")
            if n.get("status")=="verified" and (not n.get("source_refs") or not (n.get("root_cause_refs") or str(n.get("verification_note") or "").strip())):
                raise UserError("已验证鱼骨原因需要来源和验证说明或关联根因。")
            walk(n.get("children",[]),depth+1)
    for c in tree["categories"]:
        if not isinstance(c,dict) or not valid_id(c.get("id")) or c["id"] in ids or not c.get("label"): raise UserError("鱼骨分类编号或名称无效。")
        ids.add(c["id"]); walk(c.get("causes",[]),0)
    return tree
def validate_proposal(data, case, mode, sid):
    if not isinstance(data,dict): raise UserError("模型没有返回可用的结构化结果，请重试或更换模型。")
    rows=data.get("stages")
    if not isinstance(rows,list) or not rows: raise UserError("模型未返回阶段内容，未修改原报告。")
    seen=set(); sources={x["id"] for x in case["sources"]}
    for row in rows:
        if not isinstance(row,dict) or row.get("id") not in {f"D{i}" for i in range(1,9)} or row["id"] in seen:
            raise UserError("模型返回了重复或无效阶段。")
        seen.add(row["id"])
        if not isinstance(row.get("report_markdown"),str): raise UserError("模型阶段正文缺失，原报告已保留。")
        if len(row["report_markdown"])>80000: raise UserError("单阶段输出过长。")
        if row.get("status","in_progress") not in STATES: raise UserError("模型阶段状态无效。")
        row["status"]="ready_for_review" if row.get("status")=="complete" else row.get("status","in_progress")
        validate_refs(row.get("source_refs",[]),sources)
    if mode=="import" and seen != {f"D{i}" for i in range(1,9)}: raise UserError("模型未返回完整D1–D8，请重试；现有报告未改变。")
    if mode=="guided" and sid not in seen: raise UserError("模型没有返回当前阶段。")
    for key in ("facts","hypotheses","root_causes","actions","gaps","conflicts"):
        values=data.setdefault(key,[])
        if not isinstance(values,list) or len(values)>500: raise UserError("模型记录格式无效："+key)
        identifiers=set()
        for record in values:
            if not isinstance(record,dict) or not valid_id(record.get("id")) or record["id"] in identifiers: raise UserError("模型记录缺少唯一编号："+key)
            identifiers.add(record["id"])
            if "source_refs" in record: validate_refs(record["source_refs"],sources)
            if key in ("facts","root_causes"): record["confirmation"]="unreviewed"
            if key=="gaps": record["resolved"]=False
    validate_roots(data["root_causes"],sources)
    roots={r["id"] for r in case["root_causes"]}|{r["id"] for r in data["root_causes"]}
    if data.get("fishbone") is not None: validate_fishbone(data["fishbone"],sources,roots)
    if "D4" in seen and data.get("fishbone") is None: raise UserError("D4缺少鱼骨图数据，请重试。")
    for a in data["actions"]:
        if a.get("stage") not in {f"D{i}" for i in range(1,9)}: raise UserError("措施缺少有效阶段。")
        if any(r not in roots for r in a.get("root_cause_refs",[])): raise UserError("措施引用了不存在的根因。")
    data["report_kind"]="draft"
    return data
def merge_by_id(old,new):
    result={x["id"]:copy.deepcopy(x) for x in old}
    for item in new: result[item["id"]]=copy.deepcopy(item)
    return list(result.values())
def apply_proposal(case, proposal, chosen):
    if proposal["base_revision"] != case["revision"]: raise UserError("报告已修改。请重新分析后再采用建议，避免覆盖最新内容。",409)
    data=proposal["data"]; offered={x["id"] for x in data["stages"]}
    if not chosen or not set(chosen)<=offered: raise UserError("请选择要采用的阶段。")
    result=copy.deepcopy(case)
    for row in data["stages"]:
        if row["id"] not in chosen: continue
        s=stage(result,row["id"]); s["report_markdown"]=row["report_markdown"]; s["status"]=row["status"]; s["manual"]=False
        invalidate(result,row["id"])
    # Shared records are additions, not wholesale replacement of case history.
    for key in ("facts","hypotheses"):
        result[key]=merge_by_id(result[key],data[key])
    if "D4" in chosen:
        result["root_causes"]=merge_by_id(result["root_causes"],data["root_causes"])
        result["fishbone"]=copy.deepcopy(data["fishbone"])
    result["actions"]=merge_by_id(result["actions"],[x for x in data["actions"] if x.get("stage") in chosen])
    result["gaps"]=merge_by_id(result["gaps"],[x for x in data["gaps"] if x.get("stage") in chosen or x.get("stage") is None])
    result["conflicts"]=merge_by_id(result["conflicts"],data["conflicts"])
    check_action_links(result)
    validate_fishbone(result["fishbone"],{x["id"] for x in result["sources"]},{x["id"] for x in result["root_causes"]})
    return result
def validate_roots(roots,sources):
    if not isinstance(roots,list) or len(roots)>100: raise UserError("根因记录格式无效或过多。")
    ids=set()
    for r in roots:
        if not isinstance(r,dict) or not valid_id(r.get("id")) or r["id"] in ids or r.get("kind") not in ("occurrence","escape"):
            raise UserError("根因编号或类型无效。")
        ids.add(r["id"])
        if not isinstance(r.get("statement"),str) or not r["statement"].strip(): raise UserError("根因陈述不能为空。")
        if r.get("verification") not in ("unverified","supported","verified","refuted","inconclusive"):
            raise UserError("根因验证状态无效。")
        record=r.get("verification_record")
        if record is not None and not isinstance(record,str): raise UserError("实际验证记录应为文字。")
        validate_refs(r.get("source_refs",[]),sources)
        if r.get("verification")=="verified" and (not r.get("source_refs") or not str(record or "").strip()):
            raise UserError("已验证根因必须填写来源与实际验证记录。")
    return roots
def check_action_links(case):
    roots={r["id"] for r in case["root_causes"]}
    for a in case["actions"]:
        missing=[r for r in a.get("root_cause_refs",[]) if r not in roots]
        gid="LINK-"+a["id"]
        if missing:
            gap=dict(id=gid,stage=a["stage"],description="措施 "+a["id"]+" 关联的根因已移除："+", ".join(missing),suggested_next_step="更新措施与根因对应关系，并在复核前确认。",resolved=False)
            case["gaps"]=merge_by_id(case["gaps"],[gap])
def review_stage(case, sid, reviewer, checks, note, roots_confirmed=False, na_escape=False):
    stage(case,sid)
    if not str(reviewer or "").strip() or not str(note or "").strip(): raise UserError("请填写复核人和证据/复核说明。")
    if checks != [True]*len(CHECKS[sid]): raise UserError("请逐项核对本阶段的完成条件。")
    s=stage(case,sid)
    if not s["report_markdown"].strip(): raise UserError("阶段正文为空，无法完成复核。")
    blockers=[x for x in case["gaps"] if not x.get("resolved") and x.get("stage") in (sid,None)]
    conflicts=[x for x in case["conflicts"] if not x.get("resolution") and (not x.get("affected_stages") or sid in x["affected_stages"])]
    if blockers or conflicts: raise UserError("请先处理本阶段的关键缺口和冲突。")
    if sid in ("D5","D6","D7") and stage(case,"D4")["status"]!="complete":
        raise UserError("D4根因尚未完成复核，可保留本阶段草稿。")
    if sid=="D4":
        roots=case["root_causes"]
        if not roots_confirmed or not roots or any(r.get("verification")!="verified" or not r.get("verification_record") or not r.get("source_refs") for r in roots):
            raise UserError("根因需要验证记录、来源和明确复核；可继续补充证据，保留草稿。")
        kinds={r.get("kind") for r in roots}
        if "occurrence" not in kinds or ("escape" not in kinds and not na_escape):
            raise UserError("请核对产生与逃逸分析；不适用需在复核说明中写明依据。")
        for r in roots: r["confirmation"]="confirmed"
    if sid=="D8" and any(x["status"]!="complete" for x in case["stages"][:7]):
        raise UserError("D1–D7尚未全部复核，不能结案。")
    s["status"]="complete"
    s["review"]=dict(by=str(reviewer).strip(),at=now(),note=note,checks=checks,na_escape=na_escape)
    case["report_kind"]="closed" if sid=="D8" else "reviewed_snapshot"
    return case
