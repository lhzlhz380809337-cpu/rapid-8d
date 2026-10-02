/** I18n strings for frontend UI — interface language (zh/en). */

const FOCUS_ZH: Record<string, string> = {
  D1: `**目标**：组建跨职能团队，明确各成员角色和职责。

**关注点**：
- 识别需要哪些职能（质量、生产、工程、采购等）
- 确定团队负责人（8D Champion）
- 明确每个成员的职责
- 记录团队名单和联系方式

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D2: `**目标**：用数据化语言精确描述问题，使用 5W2H 框架和 IS/IS-NOT 表界定问题边界。

**基本信息**：
- 不良现象是否完整描述？（优先度 / 车号 / 车型 / 颜色 / 选装代码）
- 是否已在 SFMd 中上传相关照片？

**5W2H 框架**：
- **What** — 具体的不良现象是什么？缺陷名称？
- **When** — 首次发现的时间？（日期 / 班次）
- **Where** — 在哪个位置发现？（Sensor / 产线 / 工位）
- **Who** — 谁发现的？（操作员？检验员？Sensor？）
- **How** — 问题是否可测量？使用了什么测量或分析工具？
- **How Much** — 不良数量/不良率/涉及批次？

**IS / IS-NOT 表** — 界定问题边界，不确定的维度留空

**影响范围** — 问题是否可能涉及其他产线/工位？

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D3: `**目标**：在根因找到之前立即采取短期措施，控制问题影响范围，防止问题继续影响客户。

**时效性**：
- 是否在 24 个生产小时内按要求的反应计划实施？
- 如未能实施，是否有合理理由说明？

**追溯范围**：
- 缺陷起始点（dirt point）和措施生效点（clean point）是否已明确？
- dirt point 到 clean point 之间的所有产品是否已排查/返工？

**具体措施**：
- 各位置（产线/仓库/在途/客户）的问题品处置方案
- 短期措施是否合规且已验证有效？
- 是否已在 SFMd 中上传措施证明？

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D4: `**D4 是 8D 中最关键的步骤** — 本阶段 AI 将使用较复杂的分析提示词，以资深工程师的角色协助你进行系统性根因分析。

**六步分析法**：
1. **建立信息基线** — 收集问题时间、频率、来源；欢迎上传检测报告、SPC、机台参数等文件，AI 会主动解读
2. **变更点分析** — 回顾问题出现前 2-4 周，人机料法环测六维度是否发生过变化
3. **假设驱动分析** — 建立 2-4 个假设，逐一验证并排除
4. **5Why 分析** — 逐层追问，找到产生根因（process issue / part issue）
5. **逃逸点分析** — 独立分析为什么缺陷未被检测就流出
6. **结论确认** — 确保根因可追溯、可指导后续长期措施

**铁律**：所有分析必须基于实际数据，严禁编造。AI 会保持批判性思维，温和质疑缺乏证据的结论。

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D5: `**目标**：针对根本原因制定长期措施，确保从源头解决问题。

**关注点**：
- 针对根本原因提出多个候选长期措施方案
- 方案可行性评估（成本/周期/风险/可实施性）
- 方案验证方法和判定标准
- 确定最终长期措施方案及实施计划

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D6: `**目标**：按计划实施长期措施，确保方案在现场落地执行。

**关注点**：
- 长期措施详细实施计划和甘特图
- 实施过程中的监控数据和关键节点
- 现场执行确认（人员/设备/物料到位）
- 实施完成的初步确认

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D7: `**目标**：通过长期数据跟踪验证长期措施的实际效果，确保问题不再复发。

**关注点**：
- 收集长期措施实施后的关键指标数据（至少覆盖一个完整生产周期）
- 对比改善前后数据，量化改善效果
- 使用统计方法验证改善的显著性（如 Cpk、P 值等）
- 如未达预期效果，回退至 D4/D5 重新分析
- 整理措施有效性验证报告，作为项目关闭依据

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,

  D8: `**目标**：通过文件标准化、现场落地和水平展开，系统化防止同类问题再次发生。

**关注点**：
- 更新 FMEA / 控制计划 / 作业指导书等受控文件
- 将 PCA 标准化为现场操作规范，确保产线落地执行
- 水平展开：排查其他产品/产线是否存在类似风险并同步改善
- 制定培训计划，确保相关人员掌握新标准
- 建立定期审计和回顾机制，确保持续合规

如有更多关注点，请与 AI 对话讨论或直接输入上下文。`,
};

const FOCUS_EN: Record<string, string> = {
  D1: `**Objective**: Build a cross-functional team with clearly defined roles and responsibilities for each member.

**Focus Areas**:
- Identify which functions are needed (Quality, Production, Engineering, Purchasing, etc.)
- Appoint a team leader (8D Champion)
- Define each member's responsibilities
- Record team roster and contact information

For additional focus areas, discuss with the AI or directly enter context.`,

  D2: `**Objective**: Describe the problem precisely using data-driven language, applying the 5W2H framework and IS/IS-NOT table to define the problem boundary.

**Basic Information**:
- Is the fault clearly defined and fully described? (Priority / vehicle number(s) / model series / color / option codes)
- Are supporting photos uploaded in SFMd?

**5W2H Framework**:
- **What** — What is the specific defect? Defect name?
- **When** — Time of first occurrence? (Date / shift)
- **Where** — Where was it found? (Sensor / line / station)
- **Who** — Who discovered it? (Operator? Inspector? Sensor?)
- **How** — Is the fault measurable? What measurement or analysis tools were used?
- **How Much** — Defect quantity/defect rate/affected batches?

**IS / IS-NOT Table** — Define the problem boundary; leave uncertain dimensions empty

**Impact Scope** — Are the impacts and any potential involvement of other lines/stations clearly described?

For additional focus areas, discuss with the AI or directly enter context.`,

  D3: `**Objective**: Take short term actions to contain the problem before the root cause is found, preventing it from continuing to affect the customer.

**Timeliness**:
- Was a short term action implemented per the required reaction plan within 24 production hours?
- If not, was it reasonably justified?

**Traceability**:
- Are the dirt point and clean point clearly defined?
- Were all products between dirt point and clean point inspected/reworked?

**Specific Actions**:
- Disposition plan for affected products at each location (line/warehouse/transit/customer)
- Does the short term action comply with the reaction plan and has effectiveness been verified?
- Are proofs uploaded in SFMd Attachment?

For additional focus areas, discuss with the AI or directly enter context.`,

  D4: `**D4 is the most critical step in the 8D process** — The AI will use a sophisticated analysis prompt and act as a senior engineer to guide you through systematic root cause analysis.

**Six-Step Analysis Method**:
1. **Information Baseline** — Collect problem timing, frequency, source; upload inspection reports, SPC charts, machine logs — the AI will proactively interpret them
2. **Change Point Analysis** — Review the 2-4 weeks before the problem for changes across all 6 dimensions (Man, Machine, Material, Method, Environment, Measurement)
3. **Hypothesis-Driven Analysis** — Build 2-4 hypotheses and verify/eliminate them one by one
4. **5Why Analysis** — Drill down layer by layer to find the occurrence root cause (process issue / part issue)
5. **Escape Point Analysis** — Independent analysis of why the defect was not detected before escaping
6. **Conclusion Confirmation** — Ensure root causes are traceable and actionable for D5/D6

**Golden Rule**: All analysis must be data-driven; never fabricate. The AI will maintain critical thinking and gently challenge unsupported conclusions.

For additional focus areas, discuss with the AI or directly enter context.`,

  D5: `**Objective**: Define long term actions targeting the root cause to fundamentally eliminate the problem.

**Focus Areas**:
- Propose multiple candidate long term action solutions targeting the root cause
- Feasibility assessment (cost/timeline/risk/implementability)
- Verification method and acceptance criteria
- Final long term action selection and implementation plan

For additional focus areas, discuss with the AI or directly enter context.`,

  D6: `**Objective**: Implement the long term actions as planned and ensure on-site execution.

**Focus Areas**:
- Detailed long term action implementation plan and Gantt chart
- Monitoring data and key milestones during implementation
- On-site execution confirmation (personnel/equipment/materials in place)
- Preliminary confirmation of implementation completion

For additional focus areas, discuss with the AI or directly enter context.`,

  D7: `**Objective**: Verify through long-term data tracking that the long term actions are truly effective and the problem will not recur.

**Focus Areas**:
- Collect key metric data after long term action implementation (covering at least one full production cycle)
- Compare before/after data to quantify the improvement
- Use statistical methods to validate significance (e.g., Cpk, P-value)
- If targets are not met, return to D4/D5 for re-analysis
- Compile an effectiveness verification report as project closure evidence

For additional focus areas, discuss with the AI or directly enter context.`,

  D8: `**Objective**: Systematically prevent recurrence through document standardization, on-site implementation, and horizontal deployment.

**Focus Areas**:
- Update controlled documents: FMEA / Control Plan / Work Instructions
- Standardize PCA into on-site operating procedures and ensure shop floor implementation
- Horizontal deployment: investigate whether other products/lines have similar risks and apply improvements
- Develop a training plan to ensure relevant personnel master the new standards
- Establish a periodic audit and review mechanism to ensure ongoing compliance

For additional focus areas, discuss with the AI or directly enter context.`,
};

export const UI: Record<string, Record<string, string>> = {
  zh: {
    focus: "阶段关注点",
    context: "阶段上下文",
    upload: "上传文件",
    docParsed: "已从文件中提取文本内容：",
    docEmpty: "该文件无法提取文字内容（可能为扫描件或图片），请口述关键信息",
    docUnsupported: "暂不支持此文件格式",
    uploading: "上传中...",
    contextPlaceholder: "在此输入本阶段的上下文信息（白话即可）...",
    contextHint: "可将内容复制到右侧 AI 对话框中，获取建议和讨论",
    reviewContext: "检查上下文",
    reviewing: "检查中...",
    aiOutput: "AI 输出",
    confirmed: "已确认",
    outputEmpty: "点击下方按钮，AI 将根据上下文生成该阶段的报告内容",
    outputGenerating: "AI 正在生成报告内容...",
    expandPanel: "全屏展开",
    collapsePanel: "退出全屏",
    fontSizeUp: "放大字体",
    fontSizeDown: "缩小字体",
    generate: "生成输出",
    regenerate: "重新生成",
    regenerateAI: "重新AI生成",
    editOutput: "编辑输出",
    confirmOutput: "确认输出",
    unlockEdit: "解锁编辑",
    confirmEdit: "确认修改",
    cancel: "取消",
    // Settings
    settings: "设置",
    backToEdit: "← 返回编辑",
    save: "保存设置",
    saved: "已保存",
    interfaceLang: "界面语言",
    reportLang: "报告输出语言",
    langZh: "中文",
    langEn: "English",
    langBoth: "中英双语",
    // Chat
    chatPlaceholder: "输入消息...按 Enter 发送",
    send: "发送",
    aiChat: "AI 对话",
    typing: "正在输入...",
    addToContext: "+ 加入上下文",
    crossCheckWarning: "跨阶段检查发现问题：",
    chatEmptyHint: "在 {step} 阶段与 AI 对话，针对当前阶段进行深入讨论。",
    // History
    newProject: "新建项目",
    history: "历史记录",
    historyProjects: "历史项目",
    historyBack: "← 返回编辑",
    deleteProject: "删除项目",
    deleteConfirm: "确定要删除这个项目吗？删除后所有历史记录和报告都将永久丢失，不可恢复。",
    stepsCompleted: "{done}/{total} 步骤完成",
    latest: "最新:",
    versionsCount: "{n} 个版本",
    snapshotsCount: "{n} 个日期快照",
    reportsCount: "{n} 份报告",
    noHistoryHint: "开始第一个 8D 项目",
    errorLoadProjects: "加载项目列表失败，请检查后端服务是否启动",
    versionHistory: "版本历史",
    noHistoryVersion: "暂无历史版本",
    snapshotHistory: "日期快照",
    noSnapshotHistory: "暂无日期快照",
    // Report
    reportPreview: "报告预览及生成",
    generateAndPreview: "生成报告并预览",
    generating: "生成中...",
    confirmAndSave: "确认并保存",
    saving: "保存中...",
    reportRequirements: "报告生成要求",
    defaultRequirements: "系统默认要求",
    customRequirements: "自定义要求",
    loading: "加载中...",
    errorLoad: "加载报告要求失败：",
    // Nav
    navNew: "新建报告",
    navHistory: "历史报告",
    navSettings: "设置",
    welcomeTitle: "欢迎使用 8D Agent 报告系统",
    welcomeHint: "请点击顶部「新建报告」开始",
    // Dialog
    dialogNewTitle: "新建 8D 报告",
    dialogCancel: "取消",
    dialogOk: "确定",
    dialogInputPlaceholder: "输入报告名称",
    // Settings
    settingsTitle: "设置",
    glossaryTitle: "自定义 AI 上下文",
    glossaryHelp: "此 Markdown 内容会在 AI 对话和输出生成时作为额外上下文注入。可填写术语对照、公司规范、输出风格要求等。",
    glossaryLoadFailed: "加载术语表失败",
    glossarySaved: "术语表已保存",
    aboutTitle: "关于",
    aboutTestVersion: "本软件为测试版本，如有问题请邮件联系：",
    langSettings: "语言设置",
    interfaceLangLabel: "界面语言",
    interfaceLangHelp: "控制 UI 文字、AI 对话和阶段关注点的语言",
    reportLangLabel: "报告输出语言",
    reportLangHelp: "控制最终 8D 报告的输出语言",
    // Report
    reportFullTitle: "AI报告生成",
    aiGenerateMode: "AI 生成模式",
    reportPromptSection: "报告生成要求",
    systemDefaults: "系统默认要求",
    customReqs: "自定义要求",
    customReqsPlaceholder: "在此输入额外要求，例如：\n\n• 生成纯 HTML 格式\n• 鱼骨图使用彩色主题\n• 嵌入上下文中的图片\n• 每阶段添加小结摘要\n• 表格使用斑马条纹样式",
    finalPromptPreview: "最终 Prompt 预览",
    previewEmpty: "点击左侧\"生成报告并预览\"按钮生成并预览报告",
    aiGenerating: "AI 正在生成报告...",
    generateFailed: "生成失败：",
    confirmFailed: "确认失败：",
    networkError: "网络错误",
    // Chat
    inputPlaceholder: "输入消息... 按 Enter 发送",
    // History
    historyTitle: "历史报告",
    noHistory: "暂无历史报告，去创建一个吧",
  },
  en: {
    focus: "Phase Focus",
    context: "Phase Context",
    upload: "Upload File",
    docParsed: "Text extracted from file:",
    docEmpty: "Unable to extract text from this file (may be a scanned document or image). Please describe the key information verbally.",
    docUnsupported: "File format not supported",
    uploading: "Uploading...",
    contextPlaceholder: "Enter context for this phase (plain language is fine)...",
    contextHint: "Copy your content to the AI chat panel on the right for suggestions and discussion",
    reviewContext: "Review Context",
    reviewing: "Reviewing...",
    aiOutput: "AI Output",
    confirmed: "Confirmed",
    outputEmpty: "Click the button below. AI will generate report content based on the context.",
    outputGenerating: "AI is generating report content...",
    expandPanel: "Expand",
    collapsePanel: "Collapse",
    fontSizeUp: "Increase font size",
    fontSizeDown: "Decrease font size",
    generate: "Generate Output",
    regenerate: "Regenerate",
    regenerateAI: "Regenerate AI",
    editOutput: "Edit Output",
    confirmOutput: "Confirm Output",
    unlockEdit: "Unlock Editing",
    confirmEdit: "Confirm Changes",
    cancel: "Cancel",
    // Settings
    settings: "Settings",
    backToEdit: "← Back",
    save: "Save Settings",
    saved: "Saved",
    interfaceLang: "Interface Language",
    reportLang: "Report Output Language",
    langZh: "中文",
    langEn: "English",
    langBoth: "Bilingual (ZH+EN)",
    // Chat
    chatPlaceholder: "Type a message... Press Enter to send",
    send: "Send",
    aiChat: "AI Chat",
    typing: "Typing...",
    addToContext: "+ Add to Context",
    crossCheckWarning: "Cross-phase issues found:",
    chatEmptyHint: "Chat with AI in the {step} phase for in-depth discussion.",
    // History
    newProject: "New Project",
    history: "History",
    historyProjects: "Report History",
    historyBack: "← Back",
    deleteProject: "Delete Project",
    deleteConfirm: "Are you sure you want to delete this project? All history, records, and reports will be permanently lost and cannot be recovered.",
    stepsCompleted: "{done}/{total} steps completed",
    latest: "Latest:",
    versionsCount: "{n} versions",
    snapshotsCount: "{n} snapshots",
    reportsCount: "{n} reports",
    noHistoryHint: "Create your first 8D project",
    errorLoadProjects: "Failed to load project list. Please check that the backend service is running.",
    versionHistory: "Version History",
    noHistoryVersion: "No history versions",
    snapshotHistory: "Date Snapshots",
    noSnapshotHistory: "No date snapshots",
    // Report
    reportPreview: "Report Preview & Generation",
    generateAndPreview: "Generate & Preview",
    generating: "Generating...",
    confirmAndSave: "Confirm & Save",
    saving: "Saving...",
    reportRequirements: "Report Requirements",
    defaultRequirements: "System Default Requirements",
    customRequirements: "Custom Requirements",
    loading: "Loading...",
    errorLoad: "Failed to load requirements: ",
    // Nav
    navNew: "New Report",
    navHistory: "History",
    navSettings: "Settings",
    welcomeTitle: "Welcome to 8D Agent Report System",
    welcomeHint: "Click 'New Report' at the top to get started",
    // Dialog
    dialogNewTitle: "New 8D Report",
    dialogCancel: "Cancel",
    dialogOk: "OK",
    dialogInputPlaceholder: "Enter report name",
    // Settings
    settingsTitle: "Settings",
    glossaryTitle: "Custom AI Context",
    glossaryHelp: "This Markdown content is injected into AI chat and output generation as additional context. Add term mappings, company conventions, output style requirements, etc.",
    glossaryLoadFailed: "Failed to load glossary",
    glossarySaved: "Glossary saved",
    aboutTitle: "About",
    aboutTestVersion: "This is a test version. If you encounter any issues, please contact:",
    langSettings: "Language Settings",
    interfaceLangLabel: "Interface Language",
    interfaceLangHelp: "Controls UI text, AI conversation, and phase focus language",
    reportLangLabel: "Report Output Language",
    reportLangHelp: "Controls the language of the final 8D report",
    // Report
    reportFullTitle: "AI Report Generation",
    aiGenerateMode: "AI Generation Mode",
    reportPromptSection: "Report Generation Requirements",
    systemDefaults: "System Default Requirements",
    customReqs: "Custom Requirements",
    customReqsPlaceholder: "Enter additional requirements here, e.g.:\n\n• Pure HTML format\n• Colorful fishbone theme\n• Embed images from context\n• Add summary for each phase\n• Zebra-striped table styles",
    finalPromptPreview: "Final Prompt Preview",
    previewEmpty: "Click \"Generate & Preview\" on the left to generate and preview the report",
    aiGenerating: "AI is generating the report...",
    generateFailed: "Generation failed: ",
    confirmFailed: "Confirmation failed: ",
    networkError: "Network error",
    // Chat
    inputPlaceholder: "Type a message... Press Enter to send",
    // History
    historyTitle: "Report History",
    noHistory: "No reports yet. Create one to get started.",
  },
};

export function t(key: string, lang?: string): string {
  const l = lang || (typeof localStorage !== "undefined" && localStorage.getItem("interface_lang")) || "zh";
  return UI[l]?.[key] || UI.zh[key] || key;
}

export function getFocus(step: string, lang?: string): string {
  const l = lang || (typeof localStorage !== "undefined" && localStorage.getItem("interface_lang")) || "zh";
  const map = l === "en" ? FOCUS_EN : FOCUS_ZH;
  return map[step] || "";
}
