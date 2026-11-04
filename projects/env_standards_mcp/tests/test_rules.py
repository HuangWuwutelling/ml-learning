"""判定规则的测试：用地类型归类、三档边界、注①豁免。"""
from server import rules
from server.corpus import load_corpus

CORPUS = load_corpus()


def _item(name):
    item, _ = CORPUS.find(name)
    assert item is not None, name
    return item


# --- 用地类型（4.1.1 / 4.1.2 / 5.3.1）---

def test_land_type_aliases():
    assert rules.resolve_land_type('第一类用地')[0] == rules.FIRST
    assert rules.resolve_land_type('第二类')[0] == rules.SECOND
    assert rules.resolve_land_type('一类')[0] == rules.FIRST
    assert rules.resolve_land_type('二类')[0] == rules.SECOND


def test_land_type_unclear_purpose_is_first():
    """5.3.1：规划用途不明确的，适用第一类用地的筛选值和管制值。"""
    assert rules.resolve_land_type('规划用途不明确')[0] == rules.FIRST
    assert rules.resolve_land_type('用途不明确')[0] == rules.FIRST


def test_land_type_keywords():
    assert rules.resolve_land_type('居住用地')[0] == rules.FIRST
    assert rules.resolve_land_type('中小学用地')[0] == rules.FIRST
    assert rules.resolve_land_type('社区公园')[0] == rules.FIRST
    assert rules.resolve_land_type('工业用地')[0] == rules.SECOND
    assert rules.resolve_land_type('物流仓储用地')[0] == rules.SECOND


def test_land_type_unknown_is_not_guessed():
    """认不出来就返回 None，不能猜——用错列整套限值都错。"""
    land, why = rules.resolve_land_type('公园')
    assert land is None
    assert '用地类型' in why
    assert rules.resolve_land_type('')[0] is None


# --- 三档边界（5.3.2 / 5.3.3 / 5.3.4 / 5.3.5）---

def test_classify_boundaries():
    """等于筛选值算可忽略，等于管制值还走风险评估。"""
    assert rules.classify(20, 20, 47) == rules.TIER_IGNORABLE
    assert rules.classify(19.99, 20, 47) == rules.TIER_IGNORABLE
    assert rules.classify(20.01, 20, 47) == rules.TIER_INVESTIGATE
    assert rules.classify(47, 20, 47) == rules.TIER_INVESTIGATE
    assert rules.classify(47.01, 20, 47) == rules.TIER_CONTROL


def test_screen_ignorable():
    out = rules.screen(_item('镉'), 20, rules.FIRST)
    assert out['tier'] == rules.TIER_IGNORABLE
    assert out['screening_value'] == 20
    assert out['control_value'] == 47
    assert any('5.3.2' in a for a in out['actions'])


def test_screen_investigate_lists_both_clauses():
    out = rules.screen(_item('镉'), 30, rules.FIRST)
    assert out['tier'] == rules.TIER_INVESTIGATE
    assert any('5.3.3' in a for a in out['actions'])
    assert any('5.3.4' in a for a in out['actions'])


def test_screen_control_lists_both_clauses():
    out = rules.screen(_item('镉'), 60, rules.FIRST)
    assert out['tier'] == rules.TIER_CONTROL
    assert any('5.3.5' in a for a in out['actions'])
    assert any('5.3.6' in a for a in out['actions'])


def test_screen_land_type_switches_the_numbers():
    """同一个测值换用地类型，筛选值与结论都要跟着换列。"""
    first = rules.screen(_item('镉'), 30, rules.FIRST)
    second = rules.screen(_item('镉'), 30, rules.SECOND)
    assert first['screening_value'] == 20 and first['control_value'] == 47
    assert second['screening_value'] == 65 and second['control_value'] == 172
    assert first['tier'] != second['tier']


# --- 注① 背景值豁免 ---

def test_exemption_applies_when_below_background():
    """砷 25 mg/kg，水稻土背景值 40：超筛选值 20 但不超背景值，不纳入污染地块管理。"""
    out = rules.screen(_item('砷'), 25, rules.FIRST,
                       background_value=40, background_source='GB 36600-2018 附录 A')
    assert out['tier'] == rules.TIER_NOT_MANAGED
    assert out['tier_without_exemption'] == rules.TIER_INVESTIGATE
    assert 'exemption' in out


def test_exemption_does_not_apply_above_background():
    out = rules.screen(_item('砷'), 45, rules.FIRST,
                       background_value=40, background_source='GB 36600-2018 附录 A')
    assert out['tier'] == rules.TIER_INVESTIGATE
    assert 'exemption' not in out


def test_no_background_means_no_exemption():
    """没给背景值就不能判豁免，只能按 5.3.3 与 5.3.4 走。"""
    out = rules.screen(_item('砷'), 25, rules.FIRST)
    assert out['tier'] == rules.TIER_INVESTIGATE
    assert out['background_value'] is None


def test_tier_rank_orders_by_severity():
    assert rules.TIER_RANK[rules.TIER_CONTROL] > rules.TIER_RANK[rules.TIER_INVESTIGATE]
    assert rules.TIER_RANK[rules.TIER_INVESTIGATE] > rules.TIER_RANK[rules.TIER_IGNORABLE]
    assert rules.TIER_RANK[rules.TIER_NOT_MANAGED] == rules.TIER_RANK[rules.TIER_IGNORABLE]
