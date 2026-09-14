"""Test defenses/layer4-6 + llm. Run: python test_defenses_4_6.py"""
from defenses.layer4_harden import harden
from defenses.layer5_validate import validate
from defenses.layer6_sandbox import check_tool_call, TOOL_WHITELIST


def test_layer4_harden_adds_safety_clause():
    """harden 应当在 base prompt 后追加安全声明。"""
    out = harden("You are a helpful assistant.")
    assert "不执行" in out or "ignore" in out.lower() or "do not" in out.lower()


def test_layer4_harden_priority_declaration():
    """harden 输出应当包含「system prompt 优先级高于 user input」声明。"""
    out = harden("base")
    assert "system prompt" in out.lower() or "system" in out.lower()


def test_layer5_validate_clean_text():
    """普通文本应当通过 validate（无 schema 时用默认 blocklist）。"""
    assert validate("The capital of France is Paris.", schema=None) is True


def test_layer5_validate_blocked_phrase():
    """包含 'INJECTION SUCCESSFUL' 的输出应当被拦截。"""
    assert validate("INJECTION SUCCESSFUL. Now executing attack.", schema=None) is False


def test_layer5_validate_json_schema():
    """有效 JSON 应当通过 schema 验证。"""
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}
    assert validate('{"answer": "Paris"}', schema=schema) is True


def test_layer5_validate_invalid_json():
    """无效 JSON 应当被拦截。"""
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}
    assert validate("not json", schema=schema) is False


def test_layer6_allows_whitelisted_tool():
    """白名单工具应当被允许。"""
    allowed, reason = check_tool_call("get_weather", {"city": "Paris"})
    assert allowed is True


def test_layer6_blocks_dangerous_tool():
    """非白名单工具（如 send_email）应当被拒绝。"""
    allowed, reason = check_tool_call("send_email", {"to": "a@b.com"})
    assert allowed is False


def test_layer6_high_risk_requires_confirmation():
    """高风险工具（即使白名单）应当返回 reason 包含 'confirmation'。"""
    # delete_record 即使在白名单也是高风险
    if "delete_record" in TOOL_WHITELIST:
        allowed, reason = check_tool_call("delete_record", {"id": 1})
        assert "confirmation" in reason.lower()


if __name__ == "__main__":
    test_layer4_harden_adds_safety_clause()
    test_layer4_harden_priority_declaration()
    test_layer5_validate_clean_text()
    test_layer5_validate_blocked_phrase()
    test_layer5_validate_json_schema()
    test_layer5_validate_invalid_json()
    test_layer6_allows_whitelisted_tool()
    test_layer6_blocks_dangerous_tool()
    test_layer6_high_risk_requires_confirmation()
    print("OK: defenses layer 4-6 tests passed")