"""评测集本身的测试：id 唯一、字段齐、条数、取值合法。"""
import json
from pathlib import Path

EVAL_SET = Path(__file__).resolve().parent.parent / 'eval' / 'eval_set.jsonl'

KNOWN_TOOLS = {
    'search_items', 'get_limits', 'screen_result', 'screen_batch', 'get_background_value',
}
KNOWN_TIERS = {
    'risk_ignorable', 'detailed_investigation', 'control_or_remediation', 'not_managed',
}


def load_cases():
    cases = []
    with open(EVAL_SET, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            case['_lineno'] = lineno
            cases.append(case)
    return cases


def test_ids_unique():
    cases = load_cases()
    ids = [c['id'] for c in cases]
    assert len(ids) == len(set(ids)), 'id 有重复'


def test_required_fields_present():
    for case in load_cases():
        where = '%s:%d' % (EVAL_SET.name, case['_lineno'])
        assert case.get('id'), where
        assert case.get('tool') in KNOWN_TOOLS, where
        assert isinstance(case.get('args'), dict), where
        assert case.get('why'), '%s 缺 why' % where
        has_expect = bool(case.get('expect')) or 'expect_error_contains' in case
        assert has_expect, '%s 既没有 expect 也没有 expect_error_contains' % where


def test_case_count_is_stable():
    """条数动了要有人改这里，而不是悄悄变。"""
    assert len(load_cases()) == 38


def test_tool_coverage():
    """五个工具都要有用例，否则那条 MCP 接口改了没人发现。"""
    used = {c['tool'] for c in load_cases()}
    assert used == KNOWN_TOOLS


def test_expected_tiers_are_valid():
    for case in load_cases():
        tier = case.get('expect', {}).get('tier')
        if tier is not None:
            assert tier in KNOWN_TIERS, '%s 档位名非法：%s' % (case['id'], tier)


def test_error_cases_have_a_substring():
    for case in load_cases():
        if 'expect_error_contains' in case:
            assert isinstance(case['expect_error_contains'], str)
            assert len(case['expect_error_contains']) >= 3
