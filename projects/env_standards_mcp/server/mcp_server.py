"""GB 36600-2018 标准查询 MCP server。

起服务（stdio 传输，Claude Code / Claude Desktop 当作 MCP server 挂上）：

    python server/mcp_server.py

对外五个工具，全部是确定性查表与定档，没有模型参与：

| 工具 | 干什么 |
|---|---|
| `search_items` | 按名字片段找出标准里的项目名（Agent 先对齐名字再查限值） |
| `get_limits` | 查某污染物在某类用地下的筛选值 / 管制值 |
| `screen_result` | 给一个测值定档：可忽略 / 需详细调查 / 需管控或修复 |
| `screen_batch` | 一次给一批测值，逐条定档并汇总最严重的一档 |
| `get_background_value` | 查附录 A 的土壤环境背景值（砷、钒、钴） |

判据口径见 `server/rules.py` 的条款对照表；语料抽取口径见 `corpus/SOURCE.md`。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 两种跑法都要能起来：`python server/mcp_server.py` 与 `python -m server.mcp_server`。
# 前者 sys.path[0] 是 server/ 目录，找不到 server 包，这里把项目根补上。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from server import rules
from server.corpus import load_corpus

CORPUS = load_corpus()

mcp = FastMCP(
    'env-standards',
    instructions=(
        '本 server 提供 GB 36600-2018《土壤环境质量 建设用地土壤污染风险管控标准》的'
        '筛选值、管制值与风险筛查判定。所有判定都是确定性规则，引用结论时请带上条款号。'
    ),
)


def _resolve(land_type):
    land, why = rules.resolve_land_type(land_type)
    return land, why


def _background_for(item, soil_type, background_value):
    """背景值来源：调用方直接给的 > 附录 A 查到的。"""
    if background_value is not None:
        return float(background_value), '调用方给定的本地块背景值'
    if item['name'] in rules.BACKGROUND_ELEMENTS and soil_type:
        value, source, _soils = CORPUS.background_for(item['name'], soil_type)
        if value is not None:
            return value, '%s（%s 土壤类型）' % (source, soil_type)
    return None, None


@mcp.tool()
def search_items(query: str, limit: int = 10) -> dict:
    """按名称片段查 GB 36600-2018 里的污染物项目。

    用来在查限值之前先对齐标准里的项目写法（例如「多氯联苯」会带出
    「多氯联苯（总量）」和几条具体 PCB）。返回候选项目，不做判定。
    """
    hits = CORPUS.search(query, limit)
    total = len(CORPUS.search(query, 10 ** 6))
    if not hits:
        return {
            'query': query,
            'count': 0,
            'total_matched': 0,
            'items': [],
            'hint': 'GB 36600-2018 表 1 / 表 2 未收录该项目。表 1 和表 2 未列入的污染物项目，'
                    '可依据 HJ 25.3 等标准开展风险评估，推导特定污染物的土壤污染风险筛选值（5.3.7）。',
        }
    return {
        'query': query,
        'count': len(hits),
        'total_matched': total,
        'truncated': total > len(hits),
        'items': [
            {
                'name': it['name'],
                'cas': it['cas'],
                'category': it['category'],
                'clause': it['clause'],
                'table': it['table'],
                'table_title': CORPUS.tables.get(str(it['table']), {}).get('title'),
                'table_role': CORPUS.tables.get(str(it['table']), {}).get('role'),
            }
            for it in hits
        ],
    }


@mcp.tool()
def get_limits(pollutant: str, land_type: str) -> dict:
    """查某污染物在某类用地下的风险筛选值与管制值。

    land_type 可以写「第一类用地」/「第二类用地」，也可以写 GB 36600-2018 4.1
    里的用地类别名（如 居住用地、工业用地）；规划用途不明确的按第一类（5.3.1）。
    """
    item, matched = CORPUS.find(pollutant)
    if item is None:
        return {
            'error': 'GB 36600-2018 表 1 / 表 2 未收录「%s」；表 1 和表 2 未列入的污染物项目，'
                     '可依据 HJ 25.3 等标准开展风险评估，推导特定污染物的土壤污染风险筛选值（5.3.7）。'
                     % pollutant,
            'hint': '换个写法试试：用 search_items 在表 1 / 表 2 的 85 个项目里找对应名字。',
            'suggestions': [it['name'] for it in CORPUS.search(pollutant, 5)],
        }
    land, why = _resolve(land_type)
    if land is None:
        return {'error': why, 'pollutant': item['name']}

    screening = item['screening'][land]
    control = item['control'][land]
    out = {
        'pollutant': item['name'],
        'matched_by': matched,
        'cas': item['cas'],
        'category': item['category'],
        'clause': item['clause'],
        'standard': '%s %s' % (CORPUS.standard_id, CORPUS.standard_name),
        'unit': CORPUS.unit,
        'land_type': land,
        'land_type_reason': why,
        'screening_value': screening,
        'control_value': control,
        'other_land_type': {
            'land_type': rules.SECOND if land == rules.FIRST else rules.FIRST,
            'screening_value': item['screening'][rules.SECOND if land == rules.FIRST else rules.FIRST],
            'control_value': item['control'][rules.SECOND if land == rules.FIRST else rules.FIRST],
        },
        'definition': rules.LAND_TYPE_DEFINITION[land],
    }
    notes = []
    for key, marker in item.get('value_notes', {}).items():
        notes.append('%s 带注%s：%s' % (key, marker, item['notes'].get(marker, '')))
    for marker in item.get('item_notes', []):
        notes.append('项目名带注%s：%s' % (marker, item['notes'].get(marker, '')))
    if notes:
        out['notes'] = notes
    return out


@mcp.tool()
def screen_result(
    pollutant: str,
    measured: float,
    land_type: str,
    soil_type: str | None = None,
    background_value: float | None = None,
) -> dict:
    """给一个污染物的实测值定档：可忽略 / 需详细调查 / 需管控或修复。

    判定依据 GB 36600-2018 的 5.3.2 / 5.3.3 / 5.3.4 / 5.3.5。
    给了土壤类型且该元素在附录 A 里有背景值（砷、钒、钴）时，会再判一次注①：
    超过筛选值但不超过背景值的，不纳入污染地块管理。
    """
    item, matched = CORPUS.find(pollutant)
    if item is None:
        return {
            'error': 'GB 36600-2018 表 1 / 表 2 未收录「%s」；表 1 和表 2 未列入的污染物项目，'
                     '可依据 HJ 25.3 等标准开展风险评估，推导特定污染物的土壤污染风险筛选值（5.3.7）。'
                     % pollutant,
            'hint': '换个写法试试：用 search_items 在表 1 / 表 2 的 85 个项目里找对应名字。',
            'suggestions': [it['name'] for it in CORPUS.search(pollutant, 5)],
        }
    land, why = _resolve(land_type)
    if land is None:
        return {'error': why, 'pollutant': item['name']}

    background, background_source = _background_for(item, soil_type, background_value)
    result = rules.screen(item, float(measured), land,
                           background_value=background, background_source=background_source)
    result['matched_by'] = matched
    result['land_type_reason'] = why
    if soil_type and background is None and background_value is None:
        result.setdefault('notes', []).append(
            '未给背景值：GB 36600-2018 附录 A 只给了砷、钒、钴的背景值，'
            '其余元素要按 3.6 由本地块自行确定，注①的豁免没法在这里判。')
    return result


@mcp.tool()
def screen_batch(
    results: list[dict[str, Any]],
    land_type: str,
    soil_type: str | None = None,
) -> dict:
    """一次判一批测值。

    results 每项形如 {"pollutant": "镉", "measured": 60}。
    逐条定档，并汇总最严重的一档和超限项目数。
    """
    land, why = _resolve(land_type)
    if land is None:
        return {'error': why}
    verdicts = []
    for entry in results:
        pollutant = entry.get('pollutant')
        measured = entry.get('measured')
        if measured is None:
            verdicts.append({'pollutant': pollutant, 'error': '这条没有 measured'})
            continue
        verdicts.append(screen_result(pollutant, float(measured), land, soil_type=soil_type))

    ok = [v for v in verdicts if 'tier' in v]
    worst = None
    if ok:
        worst = max(ok, key=lambda v: rules.TIER_RANK[v['tier']])
    counts = {}
    for v in ok:
        counts[v['tier']] = counts.get(v['tier'], 0) + 1
    return {
        'standard': '%s %s' % (CORPUS.standard_id, CORPUS.standard_name),
        'land_type': land,
        'land_type_reason': why,
        'unit': CORPUS.unit,
        'count': len(verdicts),
        'verdicts': verdicts,
        'worst_tier': worst['tier'] if worst else None,
        'worst_tier_label': rules.TIER_LABEL[worst['tier']] if worst else None,
        'worst_pollutant': worst['pollutant'] if worst else None,
        'tier_counts': counts,
    }


@mcp.tool()
def get_background_value(element: str, soil_type: str) -> dict:
    """查附录 A 的土壤环境背景值。

    附录 A 只给了砷、钒、钴三个元素，按主要类型土壤分档。
    其他元素的背景值要按 3.6 由本地块自行确定。
    """
    value, source, soils = CORPUS.background_for(element, soil_type)
    if value is None:
        return {
            'error': source,
            'element': element,
            'soil_type': soil_type,
            'available_elements': list(CORPUS.background_values.keys()),
        }
    tiers = []
    for v, s in CORPUS.background_values[element].items():
        tiers.append({'value': float(v), 'soil_types': s})
    return {
        'element': element,
        'soil_type': soil_type,
        'background_value': value,
        'source': source,
        'all_soil_types_for_this_value': soils,
        'tiers': tiers,
        'unit': CORPUS.unit,
        'clause': 'GB 36600-2018 附录 A（表 A.%s）；背景值定义见 3.6' % (
            {'砷': '1', '钒': '3', '钴': '2'}.get(element, '1')),
    }


@mcp.resource('env-standards://gb36600/limits')
def gb36600_limits() -> str:
    """GB 36600-2018 全部限值的 JSON 原件。"""
    import json
    return json.dumps(CORPUS.doc, ensure_ascii=False, indent=2)


def main():
    mcp.run(transport='stdio')


if __name__ == '__main__':
    main()
