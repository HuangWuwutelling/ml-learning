"""评测入口：把评测集跑一遍，出一张账。

    python eval/run_eval.py            # 跑全部用例
    python eval/run_eval.py -v         # 逐条打印

**用例走的是真的 MCP 通道**：起 server、连客户端、用 `call_tool` 发请求，
不是直接调 Python 函数。这样测到的是 Agent 实际会用到的那一面。

**判定口径写在代码里，不写在评测集里**（评测集只放期望值）：
- `expect` 里的键逐一跟工具返回比，值必须完全相等（列表按顺序、字典按键）
- `names_include`：search_items 的返回里必须出现这些项目名
- `expect_error_contains`：返回里必须有 `error` 字段，且包含该子串

退出码：0 全过 / 1 有用例没过 / 2 一条都没跑起来（环境问题，不算判失败）。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_SET = Path(__file__).resolve().parent / 'eval_set.jsonl'

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# MCP SDK 自己打的 INFO 日志会盖住评测账，评测时压掉
logging.getLogger('mcp').setLevel(logging.WARNING)


def load_cases(path=EVAL_SET):
    cases = []
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            case = json.loads(line)
            if 'id' not in case or 'tool' not in case:
                raise ValueError('%s:%d 缺 id 或 tool' % (path, lineno))
            cases.append(case)
    return cases


def check_corpus():
    """语料自检：条数、表内分布、四个值齐不齐、交叉核验有没有漏网的。"""
    from server.corpus import load_corpus

    problems = []
    corpus = load_corpus()
    t1 = sum(1 for it in corpus.items if it['table'] == 1)
    t2 = sum(1 for it in corpus.items if it['table'] == 2)
    if len(corpus.items) != 85:
        problems.append('条目数 %d，应为 85' % len(corpus.items))
    if t1 != 45 or t2 != 40:
        problems.append('表 1 / 表 2 条数 %d / %d，应为 45 / 40' % (t1, t2))
    for it in corpus.items:
        for kind in ('screening', 'control'):
            for land in ('第一类用地', '第二类用地'):
                if it[kind].get(land) is None:
                    problems.append('%s 缺 %s %s' % (it['name'], kind, land))
        if not it['name']:
            problems.append('表 %d 第 %d 项 没有名字' % (it['table'], it['no']))
    failed = corpus.doc.get('cross_check', {}).get('failed', [])
    if failed:
        problems.append('交叉核验没过的条目 %d 条：%s' % (len(failed), failed))
    if set(corpus.background_values) != {'砷', '钒', '钴'}:
        problems.append('附录 A 元素应为 砷/钒/钴，实为 %s' % list(corpus.background_values))
    return problems, {
        'items': len(corpus.items),
        'table1': t1,
        'table2': t2,
        'background_elements': list(corpus.background_values),
        'cross_check_failed': len(failed),
    }


async def run_cases(cases, verbose=False):
    """跑用例，返回 [(case, 通过与否, 失败原因)]。"""
    from mcp.shared.memory import create_connected_server_and_client_session
    from server import mcp_server

    results = []
    server = mcp_server.mcp._mcp_server
    async with create_connected_server_and_client_session(server) as session:
        await session.initialize()
        for case in cases:
            try:
                resp = await session.call_tool(case['tool'], case.get('args', {}))
            except Exception as exc:                       # noqa: BLE001
                results.append((case, False, '调用 %s 抛异常：%s' % (case['tool'], exc)))
                continue

            payload = {}
            for block in resp.content:
                if getattr(block, 'type', None) == 'text':
                    try:
                        payload = json.loads(block.text)
                    except json.JSONDecodeError:
                        payload = {'_raw': block.text}
                    break

            problem = compare(case, payload)
            results.append((case, problem is None, problem))
            if verbose:
                mark = 'PASS' if problem is None else 'FAIL'
                print('  [%s] %s %s %s' % (mark, case['id'], case['tool'], case.get('args', {})))
                if problem:
                    print('         %s' % problem)
    return results


def compare(case, payload):
    """返回 None 表示通过，否则返回失败原因。"""
    if 'expect_error_contains' in case:
        needle = case['expect_error_contains']
        err = payload.get('error')
        if not err:
            return '期望有 error 字段，实际没有（返回键：%s）' % sorted(payload)
        if needle not in err:
            return 'error 里没有「%s」，实际是：%s' % (needle, err)
        return None

    expect = case.get('expect', {})
    for key, want in expect.items():
        if key == 'names_include':
            names = [i.get('name') for i in payload.get('items', [])]
            missing = [n for n in want if n not in names]
            if missing:
                return '返回里缺这些项目名：%s（实际：%s）' % (missing, names)
            continue
        if key not in payload:
            return '返回里没有键 %s（返回键：%s）' % (key, sorted(payload))
        got = payload[key]
        if got != want:
            return '%s 期望 %r，实际 %r' % (key, want, got)
    return None


def main():
    ap = argparse.ArgumentParser(description='GB 36600-2018 MCP server 评测')
    ap.add_argument('-v', '--verbose', action='store_true', help='逐条打印')
    args = ap.parse_args()

    cases = load_cases()
    print('评测集：%d 条用例' % len(cases))

    problems, stats = check_corpus()
    print('\n--- 语料自检 ---')
    print('  条目 %d（表 1 %d / 表 2 %d），附录 A 元素 %s，交叉核验未通过 %d 条'
          % (stats['items'], stats['table1'], stats['table2'],
             '/'.join(stats['background_elements']), stats['cross_check_failed']))
    for p in problems:
        print('  [FAIL] %s' % p)

    print('\n--- 用例 ---')
    results = asyncio.run(run_cases(cases, args.verbose))

    by_tool = {}
    for case, ok, _problem in results:
        slot = by_tool.setdefault(case['tool'], [0, 0])
        slot[0] += 1
        if ok:
            slot[1] += 1

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed

    print('\n========== 汇总 ==========')
    for tool in sorted(by_tool):
        total, ok = by_tool[tool]
        print('  %-24s %d/%d' % (tool, ok, total))
    print('\n用例 %d 条，通过 %d，失败 %d；语料自检问题 %d 条'
          % (len(results), passed, failed, len(problems)))

    if failed or problems:
        print('\n未过的用例：')
        for case, ok, problem in results:
            if not ok:
                print('  %s %s %s' % (case['id'], case['tool'], problem))
                print('     %s' % case.get('why', ''))
        return 1
    print('\n全部通过。')
    return 0


if __name__ == '__main__':
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.exit(main())
