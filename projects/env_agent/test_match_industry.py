# -*- coding: utf-8 -*-
"""_match_industry 的行业名匹配用例

在 projects/env_agent 下跑：
    python -m pytest test_match_industry.py -q

测的是 tools.py 里的行业名归一化：用户嘴里说的「印染厂」「某印染有限公司」
都要落到 5 个已知行业之一，而「化工机械」「化工设备厂」这类**主体是别的行当**的
说法不能被当成化工行业，否则后面的排放因数和执行标准全错。

后缀表是启发式的，不是完备的中文行业词法。漏掉的后缀会造成误命中，
新遇到一个就加一条。
"""
import pytest

from tools import EMISSION_FACTORS, _match_industry

# (输入, 期望) —— None 表示不该落到任何已知行业
CASES = [
    # 精确命中
    ("印染", "印染"),
    ("化工", "化工"),
    ("造纸", "造纸"),
    ("钢铁", "钢铁"),
    ("污水处理厂", "污水处理厂"),
    # 关键字在尾部，后面跟通用后缀：命中
    ("印染厂", "印染"),
    ("某印染有限公司", "印染"),
    ("广州示例造纸股份有限公司", "造纸"),
    ("化工企业", "化工"),
    ("石油化工有限公司", "化工"),
    ("钢铁冶炼", "钢铁"),
    ("钢铁集团", "钢铁"),
    ("xx市污水处理厂", "污水处理厂"),
    # 长关键字优先：两个关键字都在，主体是长的那个
    ("化工园区污水处理厂", "污水处理厂"),
    # 关键字只是修饰语，主体是别的行当：不该命中
    ("化工机械", None),
    ("化工机械制造", None),
    ("化工设备", None),
    ("化工设备厂", None),
    ("化工贸易公司", None),
    ("化工检测", None),
    ("造纸设备厂", None),
    ("钢铁物流", None),
    ("污水处理厂设计院", None),
    # 根本不在表里
    ("食品加工", None),
    ("电子", None),
    ("", None),
]


@pytest.mark.parametrize("industry,expected", CASES, ids=[c[0] or "<empty>" for c in CASES])
def test_match_industry(industry, expected):
    assert _match_industry(industry) == expected


def test_returns_only_known_keys():
    """匹配结果要么是 None，要么必须是 EMISSION_FACTORS 里的键，不能是输入原文。"""
    for industry, _ in CASES:
        got = _match_industry(industry)
        assert got is None or got in EMISSION_FACTORS


def test_case_regression():
    """专门盯住简历里点名的那一对：化工机械不能被当成化工。"""
    assert _match_industry("化工") == "化工"
    assert _match_industry("化工机械") is None
    assert _match_industry("化工机械制造") is None
