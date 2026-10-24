# Prompt 优化依据与判断
核对日期：2026-10-13。只采用方法组织者/原始发布者资料，未将网上案例数据移植到用户报告。

## 原始资料
1. [ASQ：Eight Disciplines](https://asq.org/quality-resources/eight-disciplines-8d)
   用于核对 D1–D8 职责、D4 根因验证以及 D5/D6 的区别。其 D7 为预防再发、D8 为团队认可。
2. [ASQ：Fishbone](https://asq.org/quality-resources/fishbone)
   鱼骨用于分类组织可能原因；默认 6M 可按问题调整。采用结构化原因树，避免把图本身当作证据。
3. [Bosch：Booklet No.16 — Problem Solving](https://assets.bosch.com/media/global/bosch_group/purchasing_and_logistics/information_for_business_partners/downloads/quality_docs/general_regulations/bosch_publications/booklet-no16-problem-solving_en.pdf)
   手册正文标注 05.2013；不是当代所有客户统一要求。问题解决漏斗、因果分析及技术/系统原因帮助审视原提示的分析深度。其附录也区分 D5 选定验证、D6 跟踪效果、D7 预防及 D8 最终评审。
4. [ASQ：Root Cause Analysis](https://asq.org/quality-resources/root-cause-analysis)
   用于核对根因分析在完整问题解决过程中的位置，而非把某一种分析工具当作全部工作。

这些资料提供方法依据，不代表产品认证、客户批准或模型效果保证。本项目没有获得一个明确版本的“AIAG 报告模板”，已删除唯一模板式表述。

## 本次产品设计判断（不是外部标准原文）
- 用独立字段保存用户确认与客观验证，防止认可一个解释就被当作根因证明。
- 两种入口共用案例与来源；整段导入直接给草稿，不能以完整访谈作为前提。
- 工作区保留假设、冲突和调查过程；正文明确成熟度，关键缺口不能被“省略未知信息”隐藏。
- 使用原因树渲染鱼骨图，使图可编辑、可追溯、可导出；图的文字状态与原因证据一致。
- 取消统一 2–4 周、2–4 假设、30 天、能力阈值、固定五层和虚构 few-shot。方法深度由问题证据与风险决定。
- 明确文件提取覆盖、不可读材料和来源定位；不能在没有工具结果时声称读懂文件或导出附件。
- 重大根因/问题范围变化触发下游复核，保持报告版本和事实历史。

## 与原提示的主要映射
| 原问题 | 优化 |
| --- | --- |
| D7 效果验证、D8 标准化 | 验证归 D6，预防归 D7，D8 补结案和认可 |
| 中英 D6 对缺失信息相反 | 关键缺口可见，非关键缺失可省略 |
| 用户答案被视为真根因 | 陈述来源、用户复核、客观验证分开 |
| 完整虚构注塑案例 | 移除数字/因果污染风险，保留方法边界 |
| 所有情况强制先变更再五层Why | 可依据慢性/突发/间歇与数据选择分析路径 |
| 专有系统名作为默认条件 | 放入可配置术语，默认通用制造业 |
| 八个独立 Prompt | 增加共同规则、导入任务、装配任务与加载契约 |
