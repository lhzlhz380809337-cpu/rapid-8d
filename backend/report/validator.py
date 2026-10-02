"""Anti-hallucination content validator for 8D reports.

Checks generated report content for signs of fabricated data before
presenting it to the user.
"""

import re

# Patterns that suggest unattributed data
NUMBER_PATTERNS = [
    (r"\d+\.?\d*\s*%", "百分比数字"),
    (r"\d+\s*件", "数量"),
    (r"\d+\s*元", "金额"),
    (r"\d+\s*批", "批次数量"),
    (r"\d+\.?\d*\s*mm|cm|m", "尺寸数据"),
    (r"\d+\.?\d*\s*g|kg|t", "重量数据"),
    (r"\d+-\d+-\d+", "日期"),
]

# Phrases that suggest model is drawing conclusions without user input
CONCLUSION_PATTERNS = [
    r"经分析",
    r"经确认",
    r"根本原因是",
    r"主要原因[是为]",
    r"经检测",
    r"数据显示",
    r"结果表[明确]",
]


class ContentValidator:
    def __init__(self, user_provided_messages: list[str] | None = None):
        """Initialize with what the user actually provided."""
        self.user_context = " ".join(user_provided_messages or []).lower()

    def validate(self, content: str) -> list[dict]:
        """Check content for potential hallucinations. Returns list of warnings."""
        warnings = []

        # Check for numbers that appear without user context support
        for pattern, label in NUMBER_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                # Simple heuristic: if the number isn't in user's messages, flag it
                if match.lower() not in self.user_context:
                    # Check if near a [待补充] or marked as user-provided
                    idx = content.find(match)
                    context_window = content[max(0, idx - 50):idx + 50]
                    if "[待补充]" not in context_window and "用户提供" not in context_window:
                        if "数据来源" not in context_window and "用户确认" not in context_window:
                            warnings.append({
                                "type": "unattributed_number",
                                "match": match,
                                "label": label,
                                "context": context_window.strip()[:80],
                            })

        # Check for conclusory language
        for pattern in CONCLUSION_PATTERNS:
            for m in re.finditer(pattern, content):
                idx = m.start()
                context_window = content[max(0, idx - 30):idx + 80]
                warnings.append({
                    "type": "conclusory_language",
                    "match": m.group(),
                    "context": context_window.strip()[:80],
                })

        return warnings

    def has_issues(self, content: str) -> bool:
        return len(self.validate(content)) > 0

    def get_warning_summary(self, content: str) -> str | None:
        warnings = self.validate(content)
        if not warnings:
            return None

        lines = ["[反幻觉检查] 以下内容请人工核实："]
        for w in warnings[:5]:  # cap at 5
            lines.append(f"  - {w['type']}: \"{w['match']}\" → {w['context']}")
        return "\n".join(lines)
