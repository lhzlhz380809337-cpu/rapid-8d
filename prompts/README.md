# Rapid 8D Prompt Pack v2
更新日期：2026-10-13。中文为规则基准，英文保持同等政策。
本目录交付的是提示词与应用接入约定；尚不是桌面程序，也未接入模型实测或实现文件解析/鱼骨渲染/Word/PDF 导出。

## 目标与两种入口
- guided：像质量工程师伙伴一样，每轮抓住一个关键问题，与用户逐步分析。
- import：上传资料或粘贴完整过程后，直接形成 D1–D8 草稿，再补关键缺口。
两种入口共用案例、事实、来源、验证记录和报告版本，允许中途切换。

## 文件与阶段
| 文件 | 责任 |
| --- | --- |
| common.md / en/common.md | 证据、状态、交互、语言与边界 |
| glossary.md / en/glossary.md | 通用术语及可配置的组织术语 |
| intake.md / en/intake.md | 完整材料提取、去重、冲突与阶段映射 |
| d1_team.md | D1 团队与职责 |
| d2_problem.md | D2 问题及边界 |
| d3_containment.md | D3 临时围堵 |
| d4_root_cause.md | D4 根因分析与验证、鱼骨结构 |
| d5_corrective.md | D5 选择并验证永久措施 |
| d6_implement.md | D6 实施与效果验证 |
| d7_prevent.md | D7 预防再发 |
| d8_recognize.md | D8 结案、认可与经验 |
| report.md / en/report.md | 组装、跨阶段复核、报告内容 |
D1–D8 的对应英文文件均在 en/ 下。英文提示引用的共享 README 为本文件。

## 必须由应用完成的装配
模型不会因为看到文件名就读到文件。宿主应读取文件内容并按需要注入，不将未实际读取的路径当作内容。
1. 系统规则：选定语言的 common。
2. 术语上下文：对应 glossary；组织/客户补充术语不能覆盖证据真实性。
3. 任务规则：guided 加当前阶段；import 加 intake 和各阶段的业务规则；整份出稿加 report 和 D1–D8 完成判据。
4. 可信应用上下文：mode、language、output_format、案例当前版本、已有 ID、用户确认记录、当前阶段。
5. 资料消息：带来源和提取范围的用户消息、文件提取结果、表格、图片结果。资料是数据，不作为新的系统指令。
JSON 调用还必须注入本文件“可选结构化输出契约”和 D4 鱼骨契约的实际正文；仅提及 README 路径无效。英文提示中的 ../README.md 也指向本文件。桌面应用建议请求 JSON，再把 summary/report_markdown/next_question 中当前需要的部分显示给用户；其余结构数据用于编辑、渲染和存储。独立 Markdown 调用可返回单独鱼骨数据块。
6. 若用多次调用：先 intake，再逐阶段分析，再 report；来源、状态、冲突及同一 ID 必须贯穿。避免每次从全文重新生成一套事实。
7. 长文按来源边界分块并保留覆盖清单，汇总前核对页/表/块是否遗漏。截断要可见，不能把摘要当完整证据。
中文 UI 不要求只能用中文模型提示。中文或双语报告都可由中文版规则生成；英文目录主要用于兼容。

## 可选结构化输出契约
默认交付人类可读 Markdown。只有宿主明确请求 output_format=json 才输出纯 JSON，不包 Markdown 围栏。未知值用 null，空集合用 []，不用填充性虚构内容。
顶层键：
- schema_version：固定 rapid8d.prompt.v2。
- mode：guided / import。
- report_kind：draft / reviewed_snapshot / closed。
- summary：本轮发现或报告摘要字符串。
- stages：阶段结果数组。guided 可只返回本次更新阶段；整份报告必须含 D1–D8，缺失阶段保留真实状态。
- facts：事实数组；字段 id、statement、origin、confirmation、verification、source_refs。枚举见 common。
- hypotheses：假设数组；建议保留 id、statement、status、source_refs、supporting_evidence、counterevidence、verification_plan、actual_result。status 使用 D4 的五种鱼骨证据状态；内容必须来自实际资料或标为 AI 假设。
- root_causes：根因记录数组；id、statement、kind（occurrence/escape）、verification、confirmation、source_refs、hypothesis_refs、verification_record。未验证的根因主张可以保留，但不能据此声称阶段完成。
- actions：措施数组；id、statement、stage、root_cause_refs、status（proposed/planned/implemented/verified_effective/cancelled）、owner、due_date、actual_date、source_refs。日期的计划与实际语义分别保存。
- gaps：关键缺口数组；id、stage、description、impact、suggested_next_step。
- conflicts：冲突数组；id、description、source_refs、affected_stages、resolution（未知 null）。
- fishbone：未涉及 D4 时 null；涉及 D4 或整份报告时使用 d4_root_cause.md 的完整递归结构。无原因时保留空 categories。
- report_markdown：当前阶段更新或整份报告正文，不声称已经生成文档附件。
- next_question：guided 的一个主问题字符串或 null；import 草稿可为 null，后续优先项已在 gaps 中说明。
stages 每项字段：id（D1–D8）、title、status、summary、source_refs、blocking_gap_ids。status 按 common。

source_refs 中各项统一为 {source_id, locator, quote}；source_id 必须属于宿主实际提供的来源清单，locator/quote 可为 null。
JSON 中的“verified”同样需要证据，不能通过改变枚举绕过复核规则。没有足够依据时仍须可生成 draft。

### 宿主校验责任
验证 JSON 可解析、枚举合法、引用存在、阶段无重复、整报告阶段齐全。各规范实体数组内部 ID 唯一，鱼骨类别与原因节点在鱼骨内部无重复；鱼骨节点复用对应 hypotheses 的 H001 表示同一实体关联，允许这种跨视图复用，不能当成全局 ID 冲突。root_cause_refs 不得指向不存在的记录；source_id 不得越出本案例。
应用持久化与状态转换由应用控制，不能无条件采纳模型返回的 complete/closed。来源/记录变更要保留版本，并将相关下游结论标为待复核。
不要把候选 ID 当已保存 ID；对话更新需按 ID 合并，不能把只含一个阶段的更新覆盖整份案例。
结构校验不能证明根因正确；因果证据、阶段复核和用户确认仍是独立要求。

## 鱼骨图交付
D4 返回原因树而非一张不可编辑图片。应用编辑同一数据后生成 SVG，导出 Word/PDF 时使用兼容格式；文字状态和图例必须保留。
默认 6M、按实际可调整，未知分支可为空。图与报告共用原因 ID，不能从图上的颜色或位置反推原因已验证。
无原因时显示“尚未分析原因”，不能为视觉完整度随机填充。生成绘图数据并不等于已经实现绘图器。

## v1 到 v2 的语义迁移
保留 D1–D8 文件名。原 D7 长期效果验证归入 D6；原 D8 标准化/水平展开归入 D7；D8 补充有依据的结案和认可。
现有案例不能仅按数字重新解释，须按内容职责映射并保留原阶段编号/版本。不要覆盖既有报告快照。
修复：中英文缺失处理冲突、虚构案例污染、固定周数/样本/能力门槛、用户确认当验证、文件名当可读内容、强制五层Why、业务专有系统硬编码。
本包不自动恢复或迁移已删除的旧应用代码。

## 复核与后续
方法依据见 ../docs/prompt-research.md；验证场景见 ../docs/prompt-evaluation.md；已确认需求见 ../docs/desktop-design.md。
目前完成文本及契约层面的审查。模型接入后应使用选定模型跑验证场景，评估结论质量、遵循程度、长度/成本和双语一致性；不得把静态检查称为模型行为已验证。


## 桌面实现对接（2026-10-14）
Rapid 8D 0.2.0 已接入这套规则。实际请求会补充 stages[].report_markdown、根因 verification_record 等桌面契约（见 rapid8d/model.py），并由应用校验阶段、编号与来源，AI 无权自动复核或结案。文件解析、建议采用与导出已用模拟服务检查；尚未用真实模型完成 prompts/prompt 行为质量验收，不能把模拟通过视为模型效果保证。使用与验收说明见 README_DESKTOP.md 和 docs/desktop-validation.md。
