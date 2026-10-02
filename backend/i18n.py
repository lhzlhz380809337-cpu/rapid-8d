"""I18n strings for backend — interface language (zh/en)."""

LANG = {
    "zh": {
        "step_labels": {
            "D1": "D1 — 组建团队",
            "D2": "D2 — 问题描述",
            "D3": "D3 — 短期措施",
            "D4": "D4 — 根本原因分析",
            "D5": "D5 — 制定长期措施",
            "D6": "D6 — 实施长期措施",
            "D7": "D7 — 措施有效性验证",
            "D8": "D8 — 标准化与预防",
        },
        "fallback_focus": "## {step} 阶段\n请参考 8D 标准流程进行。",
        "chat_role": "你是 8D 质量工程师助手，当前处于 {step} 阶段。",
        "chat_documents": "## 文档分析能力\n- 用户可能会上传文档（txt/pdf/docx/xlsx/json/csv等），系统会自动提取文本内容并以 [已从文件中提取文本内容：文件名] 格式显示\n- 如果看到此类标记，说明用户上传了文档，请基于文档内容进行分析和建议\n- 如果信息不足，可以主动建议用户上传相关文档（如检测报告、数据表、SOP、FMEA、控制计划等）\n- 如果用户提到文档内容无法读取（如扫描件），请告诉用户可以口述关键信息",
        "chat_principles": "## 核心原则\n- 只在用户提供的信息严重不足、无法进行任何有效分析时才提问\n- 优先基于已有信息给出实质性分析和建议\n- 如果信息不足但有部分信息，先基于已有信息给出初步分析，再指出缺失项\n- 适当时使用 Mermaid 图表语法（flowchart/graph/gantt）和 Markdown 表格提升表达质量\n- 不要编造任何数据、数字、人名、日期",
        "chat_focus_label": "## 当前阶段参考",
        "chat_focus_tail": "请基于上述内容，专注协助用户完成 {step} 阶段的工作。",
        "output_gen_role": "你是 8D 质量工程师，请为 {step} 阶段生成正式报告内容。",
        "output_gen_label1": "## 阶段要求",
        "output_gen_label2": "## 用户提供的上下文（已经过检查）",
        "output_gen_ctx_empty": "（用户尚未填写上下文）",
        "output_gen_requirements": [
            "将用户的白话/草稿转为正式书面语言",
            "适当时使用 Markdown 表格整理数据",
            "根因分析(D4)、流程分析等场景使用 Mermaid 图表：鱼骨刺图/因果分析：flowchart LR、5Why 分析树：graph TD、对策时间线：gantt、流程图：flowchart/graph",
            "仅基于用户已提供的信息生成内容。严禁在 output 中描述或评价未提供的信息（禁止出现'未填写''未实施''不明确''尚未提供''无相关信息'等负面描述），缺失信息只放在 suggestions 中说明，output 只呈现已确认的正面事实",
            "严禁编造数据",
            "如果用户信息不完整，在 suggestions 字段中给出 2-3 条具体补充建议，以对话式语气写出，引导用户与 AI 对话补全。如信息已充足，suggestions 返回空数组 []",
        ],
        "output_gen_format": "## 输出格式\n请按以下 JSON 格式返回（不要包含其他内容）：\n```json\n{{\n  \"output\": \"阶段报告内容（Markdown 格式，可含 Mermaid 代码块和表格）\",\n  \"suggestions\": [\"建议补充的具体内容1\", \"建议补充的具体内容2\"]\n}}\n```",
        "review_role": "你是 8D 质量工程师。请检查 {step} 阶段的上下文是否有重大问题，对照下方所有阶段的数据进行审查。",
        "review_rules": [
            "只基于已提供的信息分析，严禁编造",
            "不确定的不要说",
            "建议必须简洁，一句话说清，不要长篇大论",
        ],
        "review_points": [
            "逻辑缺陷：上下文推理是否有漏洞或跳跃？",
            "信息矛盾：上下文是否与其它阶段有冲突？",
            "关键遗漏：其它阶段已有的重要信息是否漏掉了？",
            "数据不一致：同一数据在不同阶段是否数值不同？",
        ],
        "review_output_format": "## 输出格式\n只返回 JSON，每个 finding 用一句话表达问题和建议：\n```json\n{{\n  \"findings\": [\n    {{\n      \"type\": \"flaw|contradiction|missing|inconsistent\",\n      \"summary\": \"一句话：什么问题 + 怎么改\"\n    }}\n  ]\n}}\n```\n如果没有发现问题，返回 {{\"findings\": []}}。",
        "review_type_labels": {
            "flaw": "逻辑缺陷",
            "contradiction": "信息矛盾",
            "missing": "关键遗漏",
            "inconsistent": "数据不一致",
        },
        "review_title": "## 上下文检查",
        "review_footer": "请根据以上建议修改上下文，或与 AI 进一步讨论。",
        "unfilled_ai_output": "[该阶段暂无 AI 输出内容，请先在对应步骤中生成 AI 输出]",
        "placeholder_tbd": "[待补充]",
        "placeholder_tbd_empty": "[待补充 — 该步骤 AI 输出为空]",
        "default_title": "未命名 8D 报告",
        "report_default_requirements": "1. 使用正式 8D 报告书面语言\n2. 使用 HTML 表格整理数据（<table>标签，带边框样式）\n3. 适当使用 Mermaid 图表（鱼骨图/流程图/甘特图），用 <pre class=\"mermaid\"> 包裹\n4. 仅基于已有信息生成报告内容，缺失部分自然留白，不添加占位符\n5. 严禁编造数据",
        "doc_labels": {
            "doc_number": "文档编号",
            "date": "编制日期",
            "company": "公司名称",
            "drafted_by": "编制 / 日期",
            "reviewed_by": "审核 / 日期",
            "approved_by": "批准 / 日期",
        },
        "report_cover_title": "8D 问题解决报告",
    },
    "en": {
        "step_labels": {
            "D1": "D1 — Build Team",
            "D2": "D2 — Describe Problem",
            "D3": "D3 — Short Term Action",
            "D4": "D4 — Root Cause Analysis",
            "D5": "D5 — Define Long Term Action",
            "D6": "D6 — Implement Long Term Action",
            "D7": "D7 — Proof of Effectiveness",
            "D8": "D8 — Prevention",
        },
        "fallback_focus": "## {step} Phase\nPlease follow the standard 8D process.",
        "chat_role": "You are an 8D quality engineer assistant, currently in the {step} phase.",
        "chat_documents": "## Document Analysis Capability\n- Users may upload documents (txt/pdf/docx/xlsx/json/csv etc.). The system will automatically extract text and display it as [Text extracted from file: filename]\n- When you see such markers, it means the user has uploaded a document — base your analysis and suggestions on its content\n- If information is insufficient, proactively suggest the user upload relevant documents (e.g., inspection reports, data sheets, SOPs, FMEA, Control Plans)\n- If the user mentions that a document cannot be read (e.g., scanned PDF), tell them they can describe the key information verbally",
        "chat_principles": "## Core Principles\n- Only ask questions when the user has provided severely insufficient information for meaningful analysis\n- Prioritize giving substantive analysis and suggestions based on available information\n- If information is insufficient but partial, give preliminary analysis first, then point out gaps\n- Use Mermaid diagram syntax (flowchart/graph/gantt) and Markdown tables where appropriate to improve quality\n- Never fabricate any data, numbers, names, or dates",
        "chat_focus_label": "## Current Phase Reference",
        "chat_focus_tail": "Based on the above, focus on assisting the user to complete the {step} phase.",
        "output_gen_role": "You are an 8D quality engineer. Generate the formal report content for the {step} phase.",
        "output_gen_label1": "## Phase Requirements",
        "output_gen_label2": "## User-Provided Context (reviewed)",
        "output_gen_ctx_empty": "(User has not filled in any context yet)",
        "output_gen_requirements": [
            "Convert user's plain-language/draft into formal written language",
            "Use Markdown tables to organize data where appropriate",
            "For root cause analysis (D4), process analysis, etc., use Mermaid diagrams: fishbone/causal analysis: flowchart LR, 5Why tree: graph TD, action timeline: gantt, process flow: flowchart/graph",
            "Only generate content based on information the user has provided. Never describe or comment on missing information in the output (forbidden: 'not provided', 'not implemented', 'unclear', 'not yet', 'no information', etc.). Output presents only confirmed positive facts. All missing information goes into suggestions only",
            "Never fabricate data",
            "If user information is incomplete, provide 2-3 specific suggestions in the suggestions field, written in a conversational tone to invite the user to chat with AI for completion. If information is sufficient, return empty array []",
        ],
        "output_gen_format": "## Output Format\nReturn in the following JSON format (nothing else):\n```json\n{{\n  \"output\": \"Phase report content (Markdown format, may include Mermaid code blocks and tables)\",\n  \"suggestions\": [\"Specific suggestion 1\", \"Specific suggestion 2\"]\n}}\n```",
        "review_role": "You are an 8D quality engineer. Review the {step} phase context for major issues against data from all phases below.",
        "review_rules": [
            "Only analyze based on provided information, never fabricate",
            "If unsure, say nothing",
            "Suggestions must be concise — one sentence, no long paragraphs",
        ],
        "review_points": [
            "Logic flaws: Are there gaps or leaps in the context reasoning?",
            "Information contradictions: Does the context conflict with other phases?",
            "Critical omissions: Is important information from other phases missing?",
            "Data inconsistency: Does the same data have different values across phases?",
        ],
        "review_output_format": "## Output Format\nReturn JSON only, each finding as a one-sentence summary of problem + suggestion:\n```json\n{{\n  \"findings\": [\n    {{\n      \"type\": \"flaw|contradiction|missing|inconsistent\",\n      \"summary\": \"One sentence: what's wrong + how to fix\"\n    }}\n  ]\n}}\n```\nIf no issues found, return {{\"findings\": []}}.",
        "review_type_labels": {
            "flaw": "Logic Flaw",
            "contradiction": "Contradiction",
            "missing": "Missing",
            "inconsistent": "Inconsistent",
        },
        "review_title": "## Context Review",
        "review_footer": "Please revise the context based on the suggestions above, or discuss further with the AI.",
        "unfilled_ai_output": "[No AI output yet for this phase. Please generate AI output first.]",
        "placeholder_tbd": "[TBD]",
        "placeholder_tbd_empty": "[TBD — No AI output for this phase]",
        "default_title": "Untitled 8D Report",
        "report_default_requirements": "1. Use formal 8D report language\n2. Use HTML tables to organize data (<table> tags with border styles)\n3. Use Mermaid diagrams where appropriate (fishbone/flowchart/Gantt), wrapped in <pre class=\"mermaid\">\n4. Only generate report content based on available information, omit missing parts naturally without placeholders\n5. Never fabricate data",
        "doc_labels": {
            "doc_number": "Document No.",
            "date": "Date",
            "company": "Company",
            "drafted_by": "Prepared by / Date",
            "reviewed_by": "Reviewed by / Date",
            "approved_by": "Approved by / Date",
        },
        "report_cover_title": "8D Problem Solving Report",
    },
}


def get_lang_str(lang: str) -> dict:
    """Get language strings dict, falling back to zh."""
    return LANG.get(lang, LANG["zh"])


def t(lang: str, key: str, **kwargs) -> str:
    """Get a translated string by key, with optional format kwargs."""
    strings = get_lang_str(lang)
    val = strings.get(key, LANG["zh"].get(key, key))
    if kwargs:
        return val.format(**kwargs)
    return val
