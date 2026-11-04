"""GB 36600-2018 的判定规则：把一个测值判成三档结论之一。

**这里没有模型，也不该有模型。** 限值、条款、边界（等于 / 大于）全部来自标准原文，
写成确定性规则才能被逐条复核；交给模型算，出来的数字没人敢拿去写报告。

条款对照（GB 36600-2018）：

| 条款 | 原文要点 | 本模块对应 |
|---|---|---|
| 4.1.1 / 4.1.2 | 建设用地分两类 | `resolve_land_type` 的关键词表 |
| 5.3.1 | 一类用地用一类限值，二类用地用二类限值；规划用途不明确的按第一类 | `resolve_land_type` |
| 5.3.2 | 含量等于或低于筛选值的，风险一般可以忽略 | `risk_ignorable` |
| 5.3.3 | 高于筛选值的，开展详细调查 | `detailed_investigation` |
| 5.3.4 | 等于或低于管制值的，开展风险评估 | `detailed_investigation` |
| 5.3.5 | 高于管制值的，采取风险管控或修复措施 | `control_or_remediation` |
| 5.3.6 | 修复目标应低于风险管制值 | `control_or_remediation` 的行动项 |
| 5.3.7 | 表 1 / 表 2 未列入的项目，按 HJ 25.3 推导筛选值 | 查不到条目时的提示 |
| 表 1 / 表 2 注① | 超过筛选值但不超过土壤环境背景值（3.6）的，不纳入污染地块管理 | `not_managed` |
"""
from __future__ import annotations

# --- 三档结论 ---

TIER_IGNORABLE = 'risk_ignorable'
TIER_INVESTIGATE = 'detailed_investigation'
TIER_CONTROL = 'control_or_remediation'
TIER_NOT_MANAGED = 'not_managed'

# 批次汇总时按严重程度排序用的名次
TIER_RANK = {
    TIER_IGNORABLE: 0,
    TIER_NOT_MANAGED: 0,
    TIER_INVESTIGATE: 1,
    TIER_CONTROL: 2,
}

TIER_LABEL = {
    TIER_IGNORABLE: '风险一般情况下可以忽略',
    TIER_INVESTIGATE: '需开展详细调查与风险评估',
    TIER_CONTROL: '需采取风险管控或修复措施',
    TIER_NOT_MANAGED: '不纳入污染地块管理',
}

# 每档要做什么，文字取自标准原文
TIER_ACTIONS = {
    TIER_IGNORABLE: [
        '建设用地土壤污染风险一般情况下可以忽略（5.3.2）',
    ],
    TIER_INVESTIGATE: [
        '依据 HJ 25.1、HJ 25.2 等标准及相关技术要求开展详细调查（5.3.3）',
        '依据 HJ 25.3 等标准及相关技术要求开展风险评估，确定风险水平，判断是否需要采取风险管控或修复措施（5.3.4）',
    ],
    TIER_CONTROL: [
        '对人体健康通常存在不可接受风险，应当采取风险管控或修复措施（5.3.5）',
        '修复目标应当依据 HJ 25.3、HJ 25.4 等标准确定，且应当低于风险管制值（5.3.6）',
    ],
    TIER_NOT_MANAGED: [
        '具体地块土壤中污染物检测含量超过筛选值，但等于或者低于土壤环境背景值水平的，不纳入污染地块管理（表 1 / 表 2 注①）',
    ],
}

# --- 用地类型（4.1.1 / 4.1.2 / 5.3.1）---

FIRST = '第一类用地'
SECOND = '第二类用地'

# 直接写明的别名
_LAND_ALIASES = {
    '第一类用地': FIRST,
    '第一类': FIRST,
    '一类用地': FIRST,
    '一类': FIRST,
    '第二类用地': SECOND,
    '第二类': SECOND,
    '二类用地': SECOND,
    '二类': SECOND,
    # 5.3.1：规划用途不明确的，适用第一类用地
    '规划用途不明确': FIRST,
    '用途不明确': FIRST,
    '不明确': FIRST,
}

# 关键词表，词都取自 4.1.1 / 4.1.2 原文，先匹配第一类
_LAND_KEYWORDS = (
    (FIRST, ('居住用地', '住宅用地', '中小学用地', '医疗卫生用地',
             '社会福利设施用地', '社会福利', '社区公园', '儿童公园')),
    (SECOND, ('工业用地', '物流仓储用地', '物流仓储', '商业服务业用地', '商业服务业',
              '道路与交通设施用地', '道路与交通', '公用设施用地', '公用设施',
              '公共管理与公共服务用地', '公共管理与公共服务', '绿地与广场用地', '绿地与广场')),
)

LAND_TYPE_DEFINITION = {
    FIRST: '居住用地（R）、中小学用地（A33）、医疗卫生用地（A5）、社会福利设施用地（A6）、'
           '公园绿地（G1）中的社区公园或儿童公园用地等（4.1.1）',
    SECOND: '工业用地（M）、物流仓储用地（W）、商业服务业设施用地（B）、道路与交通设施用地（S）、'
            '公用设施用地（U）、公共管理与公共服务用地（A）（A33、A5、A6 除外）、'
            '绿地与广场用地（G）（G1 中的社区公园或儿童公园用地除外）等（4.1.2）',
}

# 附录 A 只给了这三个元素的背景值
BACKGROUND_ELEMENTS = ('砷', '钒', '钴')


def resolve_land_type(land_type):
    """把用户给的用地描述归到第一类 / 第二类。

    返回 (用地类型, 依据)。认不出来时返回 (None, 提示语)，
    不猜——用地类型选错会整套限值用错列。
    """
    if not land_type:
        return None, '未给用地类型'
    raw = str(land_type).strip()
    key = raw.replace(' ', '').replace('　', '')
    if key in _LAND_ALIASES:
        land = _LAND_ALIASES[key]
        return land, '调用方直接指定（5.3.1）'
    for land, words in _LAND_KEYWORDS:
        for w in words:
            if w in key:
                return land, '按 GB 36600-2018 4.1.1 / 4.1.2 的用地分类归类：%s' % LAND_TYPE_DEFINITION[land]
    return None, (
        '认不出用地类型「%s」。请写「第一类用地」/「第二类用地」，'
        '或写 GB 36600-2018 4.1 里的用地类别名（如 居住用地 / 工业用地）。'
        '分类定义：\n第一类：%s\n第二类：%s' % (raw, LAND_TYPE_DEFINITION[FIRST], LAND_TYPE_DEFINITION[SECOND])
    )


def classify(measured, screening, control):
    """按 5.3.2 / 5.3.5 分档。不含注①豁免。"""
    if measured <= screening:
        return TIER_IGNORABLE
    if measured <= control:
        return TIER_INVESTIGATE
    return TIER_CONTROL


def screen(item, measured, land_type, background_value=None, background_source=None):
    """给一个污染物项目的一个测值定档。

    参数:
        item: corpus.Corpus 里的条目
        measured: 测值（mg/kg）
        land_type: '第一类用地' / '第二类用地'，已经过 resolve_land_type 归一
        background_value: 本地块的背景值（mg/kg）；给了就用它
        background_source: 背景值的来源说明
    """
    screening = item['screening'][land_type]
    control = item['control'][land_type]

    base_tier = classify(measured, screening, control)

    # 注①：超过筛选值但不超过土壤环境背景值的，不纳入污染地块管理
    exemption = None
    if base_tier != TIER_IGNORABLE and background_value is not None:
        if measured <= background_value:
            exemption = '测值 %g 未超过土壤环境背景值 %g mg/kg（来源：%s）' % (
                measured, background_value, background_source or '未注明来源')

    tier = TIER_NOT_MANAGED if exemption else base_tier

    notes = []
    for key, marker in item.get('value_notes', {}).items():
        notes.append('%s 带注%s：%s' % (key, marker, item.get('notes', {}).get(marker, '')))
    for marker in item.get('item_notes', []):
        notes.append('项目名带注%s：%s' % (marker, item.get('notes', {}).get(marker, '')))

    out = {
        'pollutant': item['name'],
        'cas': item['cas'],
        'category': item['category'],
        'clause': item['clause'],
        'land_type': land_type,
        'measured': measured,
        'unit': 'mg/kg',
        'screening_value': screening,
        'control_value': control,
        'background_value': background_value,
        'background_source': background_source,
        'tier': tier,
        'tier_label': TIER_LABEL[tier],
        'tier_without_exemption': base_tier,
        'tier_without_exemption_label': TIER_LABEL[base_tier],
        'actions': list(TIER_ACTIONS[tier]),
    }
    if exemption:
        out['exemption'] = exemption
    if notes:
        out['notes'] = notes
    return out
