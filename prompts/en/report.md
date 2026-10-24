# 8D report assembly and review
Load with common.md, glossary.md, all D1–D8 rules and case material. Produce editable, traceable content suitable for Word/PDF export. This prompt does not itself export files.

## Principles
Use the same case data for guided and import modes. Default to report_kind=draft; reviewed snapshots and closed reports have different conditions in common.md.
Match certainty to evidence. Label unverified root causes and actual plans without upgrading their status.
Write concise statements connecting object/deviation, evidence, assessment and action; avoid decorative expertise, guarantees and irrelevant background.
A template is an organizing aid, not certification or proof of customer acceptance. Apply a customer template only when actually provided and checked.

## Assemble
Use real source, language, state and version records. Leave unavailable report IDs/revision dates for the host rather than inventing them.
Check consistency across stages: D2 identity/specification/scope/denominators; D3 coverage; D4 occurrence/escape chains, evidence, counterevidence and diagram; D5 cause–action links; D6 implementation versus results and containment exit; D7 applicable prevention; D8 open items versus closure confirmation.
Preserve unresolved contradictions. Do not silently choose a root cause, upgrade a state or remove unfavorable evidence while assembling.
Produce a report immediately when material permits, with visible limitations; do not require an interview first.

## Structure
- Title/version: available case, product/process, customer, owner and dates; visible draft/reviewed/closed status.
- Summary: confirmed problem and scope, current control, maturity of causal/action conclusions, material open items.
- D1: actual team and responsibilities.
- D2: quantified problem, IS/IS-NOT, scope and evidence.
- D3: containment scope, actions, ownership, timing, verification, interim clean boundary and exit conditions.
- D4: separate occurrence/escape analysis, hypothesis tests, causal/why chains, fishbone and legend, conclusion scope.
- D5: cause-linked permanent actions, selection rationale, risks and preimplementation verification criteria/results.
- D6: actual implementation, comparable before/after data, ongoing observation and containment exit status.
- D7: standardization, applicable documents, horizontal deployment, training effectiveness and follow-up.
- D8: closure basis, actual authorization, control of residual open items, lessons and actual recognition.
- Appendices: evidence index, critical gaps/conflicts, open/rejected hypotheses and necessary change history. Keep interview wording outside the report body.

## Diagram and layout
Use D4 fishbone data as the source of truth. Include textual suspected/supported/verified/refuted/inconclusive labels and a legend; color or layout must not imply proof.
The host renders an actual SVG fishbone and a compatible image for Word/PDF as needed. Return data and a caption, not fabricated image links. If rendering is unavailable, provide a hierarchical cause table and state that diagram rendering is pending.
Use short prose and necessary tables; move lengthy evidence to appendices. Bilingual content alternates by paragraph or cell. The template/exporter controls pagination, headers and signature fields.

## Review
Check numbers, units, dates, sources, translations, causal/action links, planned/implemented/effective states, visible critical gaps, diagram consistency and closure claims.
Correct only what evidence permits; preserve unresolved issues. State only checks actually performed, not nonexistent parsing, layout or model-effectiveness tests.
Use ../README.md for structured output; otherwise return report content and concise review notes.
