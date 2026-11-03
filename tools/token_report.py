"""会话 token 报告：看清前最贵的东西是「反复重读上下文」，不是生成。

Usage:
    python tools/token_report.py              # 最近 8 个会话
    python tools/token_report.py --last 3     # 只看最近 3 个
    python tools/token_report.py --prefix     # 只看当前的静态前缀（开新会话后跑最准）

读的是 Claude Code 的会话记录 ~/.claude/projects/<slug>/*.jsonl 里的 usage 字段：
  input_tokens                每次都按全价计的部分
  cache_read_input_tokens     每轮重读的上下文大小（prefix + 全部历史 + 工具输出）
  output_tokens               真正生成的字数

关键口径：cache_read 的「均值」就是这一轮平均背着多大的上下文；
新会话第 1 次调用的 input_tokens 就是静态前缀（系统提示 + 工具 schema + CLAUDE.md + MEMORY.md + skills）。
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def project_dir():
    slug = str(REPO_ROOT).replace(':', '-').replace('\\', '-').replace('/', '-')
    return Path.home() / '.claude' / 'projects' / slug


def scan(path):
    """返回 (调用次数, input, cache_read, output, 每次调用的上下文大小列表)。"""
    calls = 0
    inp = cr = out = 0
    ctx = []
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if '"usage"' not in line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            msg = rec.get('message') or {}
            u = msg.get('usage') or rec.get('usage')
            if not isinstance(u, dict) or 'input_tokens' not in u:
                continue
            calls += 1
            inp += u.get('input_tokens') or 0
            r = u.get('cache_read_input_tokens') or 0
            cr += r
            out += u.get('output_tokens') or 0
            ctx.append(u.get('input_tokens', 0) + r)
    return calls, inp, cr, out, ctx


def main():
    ap = argparse.ArgumentParser(description='会话 token 报告')
    ap.add_argument('--last', type=int, default=8, help='看最近几个会话（默认 8）')
    ap.add_argument('--prefix', action='store_true', help='只报静态前缀')
    args = ap.parse_args()

    d = project_dir()
    if not d.is_dir():
        print(f'SKIP: {d} 不存在')
        return 1
    files = sorted(glob.glob(str(d / '*.jsonl')), key=os.path.getmtime)[-args.last:]
    if not files:
        print(f'SKIP: {d} 下没有会话记录')
        return 1

    if args.prefix:
        calls, inp, cr, out, ctx = scan(files[-1])
        if calls:
            print(f'static prefix: {ctx[0]:,} tokens  ({Path(files[-1]).name[:8]})')
        return 0

    print(f'{"file":<9} {"turns":>6} {"prefix":>8} {"peak":>9} {"mean":>9} '
          f'{"cache_read":>13} {"output":>11} {"out%":>5}')
    for f in files:
        calls, inp, cr, out, ctx = scan(f)
        if not calls:
            continue
        peak = max(ctx)
        mean = sum(ctx) // calls
        pct = 100 * out / (cr + out) if (cr + out) else 0
        print(f'{Path(f).name[:8]:<9} {calls:6d} {ctx[0]:8,} {peak:9,} {mean:9,} '
              f'{cr:13,} {out:11,} {pct:4.1f}%')

    print()
    print('prefix  = context of the 1st call (system prompt + tool schemas + CLAUDE.md + MEMORY.md + skills)')
    print('peak    = context peak; past 150k you should /clear at a natural boundary')
    print('out%    = share of generated tokens; under 5% means the cost is all context re-reading')
    print('baseline (measured 2026-11-02, before memory rewrite): '
          'prefix 32,079 / peak 166,528 / mean 101,984 / out 1.2%')
    return 0


if __name__ == '__main__':
    sys.exit(main())
