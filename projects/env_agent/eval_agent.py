# -*- coding: utf-8 -*-
"""env_agent 端到端评测：工具选择 + 追问约束

在 projects/env_agent 下跑：
    python eval_agent.py                       # 全部用例跑一遍
    python eval_agent.py --repeat 3            # 跑 3 遍看逐遍波动
    python eval_agent.py --only calc_vague     # 只跑指定用例

判据：每条用例给 want（会话中必须出现的工具）和 avoid（必须不出现的工具）。
want 是「至少」，多调了不在 avoid 里的工具不算错。

两个指标：
  1. 工具选择正确率 —— want 全中且 avoid 全不中，才算这条用例通过
  2. 单问约束违规 —— prompt.md 要求「每轮只做一件事、只问一个问题」，
     机检口径是：单轮回复里问号 >= 2 或出现列表符号

产出：终端表格 + eval_results/eval_<时间戳>.json
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from langchain_core.messages import HumanMessage

ALL_TOOLS = [
    "lookup_regulation",
    "calculate_emission",
    "calculate_air_emission",
    "fill_form",
    "generate_report",
]

# 一条消息里问号 >= 2 或出现列表符号，就记一次违规
LIST_RE = re.compile(r"^\s*(?:[-*•]|\d+[.、)])", re.M)
Q_RE = re.compile(r"[？?]")

# ── 用例 ──
# turns: 依次发给 agent 的用户消息（单轮用例就是长度 1 的列表）
# want:  会话中必须出现的工具（至少）
# avoid: 会话中必须不出现的工具
CASES = [
    {
        "id": "regulation_cod",
        "note": "问排放限值，该走法规检索",
        "turns": ["造纸行业的 COD 排放限值是多少？"],
        "want": ["lookup_regulation"],
        "avoid": [],
    },
    {
        "id": "regulation_validity",
        "note": "问许可证有效期，同样是法规检索",
        "turns": ["排污许可证有效期届满前多久要申请延续？"],
        "want": ["lookup_regulation"],
        "avoid": [],
    },
    {
        "id": "calc_ww_with_treatment",
        "note": "行业与水量齐全，该算废水",
        "turns": ["我们厂是印染厂，每天排 500 吨废水，有配套污水处理站，帮我算排放量"],
        "want": ["calculate_emission"],
        "avoid": [],
    },
    {
        "id": "calc_ww_no_treatment",
        "note": "没提处理设施，也照样能算",
        "turns": ["化工企业，日排放废水 800 吨，没有污水处理设施，算一下排放量"],
        "want": ["calculate_emission"],
        "avoid": [],
    },
    {
        "id": "calc_air",
        "note": "给的是风量，该走废气",
        "turns": ["钢铁厂，废气排放量 50000 立方米每小时，算一下废气排放量"],
        "want": ["calculate_air_emission"],
        "avoid": [],
    },
    {
        "id": "calc_vague",
        "note": "笼统说算排放，应追问废水还是废气，不能自己挑一个",
        "turns": ["帮我算一下排放量"],
        "want": [],
        "avoid": ["calculate_emission", "calculate_air_emission"],
    },
    {
        "id": "empty_start",
        "note": "开局一句话，应追问而不是调工具",
        "turns": ["我想办排污许可证"],
        "want": [],
        "avoid": ALL_TOOLS,
    },
    {
        # prompt.md 第二步要求 7 项信息齐全才生成材料，所以这条必须一次给全，
        # 少给一项模型就会按规则继续追问（第一版少给 3 项，判成 FAIL 是判据的错）
        "id": "form_ready",
        "note": "7 项信息一次给全，该直接出表",
        "turns": [
            "企业名称广州示例印染有限公司，联系人张三，行业印染，首次申请，"
            "废水日排放量 500 吨、排入市政管网，有污水处理设施，"
            "废气排放量 20000 立方米每小时、排气筒 1 根 15 米高，"
            "环评批复已经拿到了，帮我生成申报表"
        ],
        "want": ["fill_form"],
        "avoid": [],
    },
    {
        "id": "report_ready",
        "note": "7 项信息一次给全，该直接出报告",
        "turns": [
            "企业名称广州示例造纸有限公司，联系人李四，行业造纸，延续申请，"
            "废水日排放量 300 吨、排入市政管网，无污水处理设施，"
            "废气排放量 15000 立方米每小时、排气筒 2 根 12 米高，"
            "环评批复已经拿到了，帮我出申报报告"
        ],
        "want": ["generate_report"],
        "avoid": [],
    },
    {
        # 这条测的是 prompt 内部的一处冲突：第二步说「按顺序逐项追问」，
        # 第三步说「行业和日排放量已确认时调 calculate_emission」。
        # 前两项齐全时模型到底算还是继续追问，两种结果都记下来看
        "id": "calc_when_info_partial",
        "note": "行业+水量已给但其余未收集，观察是算还是继续追问",
        "turns": [
            "我们厂印染，日排 500 吨废水，有污水站",
            "帮我算排放量",
        ],
        "want": [],
        "avoid": [],
    },
    {
        "id": "off_topic",
        "note": "跑题问题，不该调任何工具",
        "turns": ["今天广州天气怎么样？"],
        "want": [],
        "avoid": ALL_TOOLS,
    },
    {
        "id": "flow_collect_then_form",
        "note": "多轮逐项补齐信息后出表，中途不该抢跑",
        "turns": [
            "我想办排污许可证",
            "印染",
            "首次申请",
            "每天排 500 吨废水，排入市政管网",
            "有配套的污水处理站",
            "废气 20000 立方米每小时",
            "公司是广州示例印染有限公司，联系人张三",
            "环评批复已经拿到了",
            "帮我生成申报表",
        ],
        "want": ["fill_form"],
        "avoid": ["calculate_air_emission", "generate_report"],
    },
]


def count_questions(text):
    return len(Q_RE.findall(text))


def find_violations(text):
    """返回这条回复违反「每次只问一个问题、禁列清单」的原因列表，空列表表示没违规。

    列表只在「追问」语境里算违规：法规答复会整段引标准条文，天然带换行和编号，
    拿它当违规会一路误报（实测 regulation_cod 就这样误报过一次）。
    """
    out = []
    n = count_questions(text)
    if n >= 2:
        out.append(f"{n} 个问号")
    if n >= 1 and LIST_RE.search(text):
        out.append("追问里带列表")
    return out


def run_case(agent, case):
    """跑一条用例，返回结果 dict。"""
    msgs = []
    calls = []
    replies = []
    error = None

    for turn in case["turns"]:
        msgs.append(HumanMessage(content=turn))
        prev = len(msgs)
        state = agent.invoke({"messages": msgs})
        full = [m for m in state["messages"] if m.type != "system"]
        new = full[prev:]
        msgs = full
        for m in new:
            if m.type != "ai":
                continue
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    calls.append(name)
            text = m.content if isinstance(m.content, str) else ""
            if text.strip():
                replies.append(text)

    called = set(calls)
    missing = [t for t in case.get("want", []) if t not in called]
    forbidden = [t for t in case.get("avoid", []) if t in called]
    extra = sorted(called - set(case.get("want", [])))

    violations = []
    for i, text in enumerate(replies, 1):
        for why in find_violations(text):
            violations.append({"reply_index": i, "reason": why, "excerpt": text[:300]})

    return {
        "id": case["id"],
        "note": case["note"],
        "turns": len(case["turns"]),
        "calls": calls,
        "want": case.get("want", []),
        "avoid": case.get("avoid", []),
        "missing": missing,
        "forbidden": forbidden,
        "extra": extra,
        "passed": (not missing) and (not forbidden) and error is None,
        "reply_count": len(replies),
        "replies": [t[:400] for t in replies],
        "violations": violations,
        "error": error,
    }


def run_suite(agent, cases):
    results = []
    for case in cases:
        t0 = time.time()
        try:
            r = run_case(agent, case)
        except Exception as e:
            r = {
                "id": case["id"],
                "note": case["note"],
                "turns": len(case["turns"]),
                "calls": [],
                "want": case.get("want", []),
                "avoid": case.get("avoid", []),
                "missing": case.get("want", []),
                "forbidden": [],
                "extra": [],
                "passed": False,
                "reply_count": 0,
                "violations": [],
                "error": f"{type(e).__name__}: {e}",
            }
        r["elapsed_s"] = round(time.time() - t0, 1)
        results.append(r)
        flag = "PASS" if r["passed"] else "FAIL"
        print(f"  [{flag}] {r['id']:<26} calls={r['calls']} {r['elapsed_s']}s")
        if r["error"]:
            print(f"         error: {r['error']}")
        if r["missing"]:
            print(f"         missing: {r['missing']}")
        if r["forbidden"]:
            print(f"         forbidden called: {r['forbidden']}")
        for v in r["violations"]:
            print(f"         violation: {v['reason']} -- {v['excerpt']}")
    return results


def summarize(results):
    n = len(results)
    passed = sum(1 for r in results if r["passed"])
    forbidden_hits = sum(len(r["forbidden"]) for r in results)
    total_replies = sum(r["reply_count"] for r in results)
    by_reason = {}
    for r in results:
        for v in r["violations"]:
            by_reason[v["reason"]] = by_reason.get(v["reason"], 0) + 1
    return {
        "cases": n,
        "passed": passed,
        "tool_selection": f"{passed}/{n}",
        "forbidden_hits": forbidden_hits,
        "replies": total_replies,
        "violations": sum(by_reason.values()),
        "violations_by_reason": by_reason,
        "one_question": f"{sum(by_reason.values())}/{total_replies}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeat", type=int, default=1, help="整套跑几遍（看逐遍波动）")
    ap.add_argument("--only", nargs="*", help="只跑这些用例 id")
    ap.add_argument("--out", default="eval_results", help="结果 JSON 目录")
    args = ap.parse_args()

    cases = CASES
    if args.only:
        wanted = set(args.only)
        cases = [c for c in CASES if c["id"] in wanted]
        if not cases:
            sys.exit(f"没有匹配的用例 id。可选：{[c['id'] for c in CASES]}")

    from agent import build_agent

    print(f"构建 agent（{len(cases)} 条用例，跑 {args.repeat} 遍）...")
    agent = build_agent()

    runs = []
    for i in range(1, args.repeat + 1):
        print(f"\n=== run {i}/{args.repeat} ===")
        results = run_suite(agent, cases)
        runs.append({"run": i, "results": results, "summary": summarize(results)})

    print("\n===== 汇总 =====")
    for r in runs:
        s = r["summary"]
        print(
            f"run {r['run']}: 工具选择 {s['tool_selection']} | "
            f"禁用工具被调 {s['forbidden_hits']} 次 | "
            f"单问违规 {s['one_question']} 轮 {s['violations_by_reason']}"
        )
    print(
        "\n注意：单问违规是机检口径（问号 >= 2 或追问里带列表），"
        "「A？还是 B？」这种一个问题带选项的写法会被数成两个，是已知误报"
    )

    if args.repeat > 1:
        picks = [r["summary"]["passed"] for r in runs]
        print(f"工具选择逐遍: {picks}  波动 {min(picks)}~{max(picks)}")
        by_id = {}
        for r in runs:
            for res in r["results"]:
                by_id.setdefault(res["id"], []).append(res["passed"])
        flaky = {k: v for k, v in by_id.items() if len(set(v)) > 1}
        if flaky:
            print("逐遍结果不一致的用例:")
            for k, v in flaky.items():
                print(f"  {k}: {['PASS' if x else 'FAIL' for x in v]}")
        else:
            print("所有用例逐遍结果一致")

    os.makedirs(args.out, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(args.out, f"eval_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": stamp,
                "model": "deepseek-chat",
                "temperature": 0.3,
                "repeat": args.repeat,
                "runs": runs,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n结果已写入 {path}")


if __name__ == "__main__":
    main()
