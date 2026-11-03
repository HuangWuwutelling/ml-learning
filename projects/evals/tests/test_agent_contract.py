"""env_agent（环保申报 Agent）的契约测试。

只读 `eval_agent.py` 的用例定义与 `tools.py` 的工具清单，不跑模型
（跑模型要 DEEPSEEK_API_KEY 和网络，那是 `eval_agent.py` 的活）。
"""
from conftest import (AGENT_DIR, decorated_functions, module_functions,
                      module_literal, read_text)

EVAL = AGENT_DIR / "eval_agent.py"
TOOLS = AGENT_DIR / "tools.py"

EXPECTED_TOOLS = {
    "lookup_regulation",
    "calculate_emission",
    "calculate_air_emission",
    "fill_form",
    "generate_report",
}


def test_twelve_cases_with_unique_ids():
    """12 条用例，id 唯一。"""
    cases = module_literal(EVAL, "CASES")
    assert len(cases) == 12
    ids = [c["id"] for c in cases]
    assert len(set(ids)) == 12


def test_case_fields_are_complete():
    """每条用例都有 note、turns、want、avoid，且 turns 不空。"""
    for case in module_literal(EVAL, "CASES"):
        cid = case["id"]
        assert case["note"].strip(), f'{cid} 缺 note'
        assert isinstance(case["turns"], list) and case["turns"], f'{cid} 缺 turns'
        assert all(t.strip() for t in case["turns"]), f'{cid} 有空 turns'
        assert isinstance(case["want"], list), f'{cid} 的 want 不是列表'
        assert isinstance(case["avoid"], list), f'{cid} 的 avoid 不是列表'
        assert not set(case["want"]) & set(case["avoid"]), f'{cid} 的 want 与 avoid 打架'


def test_cases_only_reference_real_tools():
    """用例里出现的工具名必须在 tools.py 里真实存在。"""
    cases = module_literal(EVAL, "CASES")
    for case in cases:
        for tool in list(case["want"]) + list(case["avoid"]):
            assert tool in EXPECTED_TOOLS, f'{case["id"]} 引用了不存在的工具 {tool}'


def test_tool_list_matches_tools_py():
    """eval_agent.py 里的 ALL_TOOLS 与 tools.py 里的 @tool 函数一一对应。"""
    assert set(module_literal(EVAL, "ALL_TOOLS")) == EXPECTED_TOOLS
    assert decorated_functions(TOOLS, "tool") == EXPECTED_TOOLS


def test_ambiguous_cases_forbid_all_tools():
    """信息不足或跑题时应追问，不该调工具：这三条一个工具都不许碰。"""
    cases = {c["id"]: c for c in module_literal(EVAL, "CASES")}
    for cid in ("calc_vague", "empty_start", "off_topic"):
        assert cases[cid]["want"] == [], f'{cid} 不该有必须调用的工具'
        assert cases[cid]["avoid"], f'{cid} 缺禁止调用的工具清单'


def test_observation_only_case_has_no_constraint():
    """calc_when_info_partial 是观察题：算还是追问两种结果都记，不设硬约束。"""
    cases = {c["id"]: c for c in module_literal(EVAL, "CASES")}
    assert cases["calc_when_info_partial"]["want"] == []
    assert cases["calc_when_info_partial"]["avoid"] == []


def test_multi_turn_case_forbids_running_ahead():
    """flow_collect_then_form 中途不许抢跑：不能提前算废气、不能提前出报告。"""
    cases = {c["id"]: c for c in module_literal(EVAL, "CASES")}
    flow = cases["flow_collect_then_form"]
    assert flow["want"] == ["fill_form"]
    assert set(flow["avoid"]) == {"calculate_air_emission", "generate_report"}
    assert len(flow["turns"]) >= 5, '多轮用例的轮次被改了'


def test_eval_agent_entrypoints_exist():
    """eval_agent.py 的命令行入口还在（--only / --repeat 是复现评测的入口）。"""
    assert "main" in module_functions(EVAL)
    src = read_text(EVAL)
    assert "--only" in src and "--repeat" in src
