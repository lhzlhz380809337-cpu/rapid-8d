"""Tests for JSON parsing methods on ConversationEngine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from backend.config import Config
from backend.conversation.engine import ConversationEngine

engine = ConversationEngine(Config())


def test_parse_output_json_normal():
    out, warnings, suggestions = engine._parse_output_json(
        '{"output": "D1 report", "suggestions": ["add more detail"]}'
    )
    assert out == "D1 report"
    assert warnings == []
    assert suggestions == ["add more detail"]


def test_parse_output_json_fenced():
    out, warnings, suggestions = engine._parse_output_json(
        '好的，以下是输出：\n```json\n{"output": "hello", "suggestions": ["a", "b"]}\n```\n希望对你有帮助！'
    )
    assert out == "hello"
    assert suggestions == ["a", "b"]


def test_parse_output_json_no_output_key():
    out, warnings, suggestions = engine._parse_output_json('{"suggestions": ["x"]}')
    assert "suggestions" in out
    assert suggestions == ["x"]


def test_parse_output_json_no_suggestions_key():
    out, warnings, suggestions = engine._parse_output_json('{"output": "ok"}')
    assert out == "ok"
    assert suggestions == []


def test_parse_output_json_plain_text():
    raw = "抱歉，我无法生成JSON格式的输出。"
    out, warnings, suggestions = engine._parse_output_json(raw)
    assert out == raw
    assert suggestions == []


def test_parse_output_json_empty():
    out, warnings, suggestions = engine._parse_output_json("")
    assert out == ""
    assert suggestions == []


def test_parse_output_json_fenced_no_json_keyword():
    # Bare ``` fence (no 'json' tag) is NOT stripped, so raw is not valid JSON
    # Falls back to returning raw text as output
    raw = '```\n{"output": "bare fence"}\n```'
    out, _, suggestions = engine._parse_output_json(raw)
    assert out == raw  # raw text returned as-is
    assert suggestions == []


def test_parse_output_json_warnings_field():
    raw = '{"output": "ok", "warnings": ["incomplete"], "suggestions": ["s1"]}'
    out, warnings, suggestions = engine._parse_output_json(raw)
    assert out == "ok"
    assert warnings == ["incomplete"]
    assert suggestions == ["s1"]


# ─── _parse_findings_json ────────────────────────────────────────────


def test_parse_findings_normal():
    findings = engine._parse_findings_json(
        '{"findings": [{"type": "missing", "summary": "no team list"}]}'
    )
    assert len(findings) == 1
    assert findings[0]["type"] == "missing"


def test_parse_findings_empty():
    findings = engine._parse_findings_json('{"findings": []}')
    assert findings == []


def test_parse_findings_no_key():
    findings = engine._parse_findings_json('{"other": "data"}')
    assert findings == []


def test_parse_findings_fenced():
    findings = engine._parse_findings_json(
        '```json\n{"findings": [{"type": "contradiction", "summary": "conflict"}]}\n```'
    )
    assert len(findings) == 1
    assert findings[0]["type"] == "contradiction"


def test_parse_findings_plain_text():
    findings = engine._parse_findings_json("not json at all")
    assert findings == []


def test_parse_findings_empty_string():
    findings = engine._parse_findings_json("")
    assert findings == []


if __name__ == "__main__":
    import traceback

    tests = [
        fn for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"  PASS  {test_fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {test_fn.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed, {len(tests)} total")
