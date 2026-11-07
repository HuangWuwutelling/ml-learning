"""Scripts 命名规范检查器

按 CLAUDE.md 的「Scripts & Figures 命名规范」扫 `scripts/` 下所有 `gen_*.py`，
列出违规清单（含 `figure` 单数 / 缺少 series 前缀 / 缺少 NN 编号 / 位置错乱）。

Usage:
    python scripts/utility/check_naming.py          # 全量扫描
    python scripts/utility/check_naming.py env      # 只扫 scripts/env/
    python scripts/utility/check_naming.py --quiet  # 只列违规，不打印 OK 的
"""
import os
import re
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / 'scripts'

# 系列短码（按 CLAUDE.md）
SERIES_CODES = {'env', 'llm', 'ml', 'causal', 'eng', 'ai-hi', 'cover'}

# 合法 gen_ 前缀
GEN_PREFIXES = ('gen_fig_', 'gen_cover_', 'gen_notebook_', 'gen_figure_',
                'gen_avatar_', 'gen_architecture_')

# 命名规范（推荐）：gen_{fig|cover}_{series}_{NN}_{topic}.py
RECOMMENDED_RE = re.compile(
    r'^gen_(?P<kind>fig|cover|notebook)_'
    r'(?P<series>env|llm|ml|causal|eng|ai-hi|cover)_'
    r'(?P<nn>\d{2,3})_'
    r'.+\.py$'
)

# 例外系列：用 dayN 编号代替 NN（CLAUDE.md 明确）
DAY_NAMED_SERIES = {'ml'}

# 例外系列：用文章标题缩写代替 NN（ai-history 系列约定）
TITLE_NAMED_SERIES = {'ai-history'}

# 通用脚本例外：供多个 day 共用，无 NN 但带 topic
GENERIC_TOPIC_RE = re.compile(r'^gen_(?:fig|cover)_(?P<topic>[a-z0-9_]+)\.py$')

# scripts/cover/ 顶层系列：命名风格自由（avatar / architecture_diagram 等）
COVER_TOP_SERIES = 'cover'


def scan_series(series_dir: Path) -> list[dict]:
    """扫描单个 series 目录，返回违规清单。"""
    issues = []
    series = series_dir.name

    for py in sorted(series_dir.glob('*.py')):
        name = py.name
        # 1. 含 figure 单数（错位）
        if 'figure_' in name:
            issues.append({
                'file': str(py.relative_to(REPO_ROOT)),
                'rule': 'figure-singular',
                'detail': "文件名含 'figure_' 单数，应为 'fig_'",
            })
            continue
        # 2. 非 gen_ 开头：忽略（不是图生成脚本）
        if not name.startswith('gen_'):
            continue
        # 3. scripts/cover/ 顶层：自由风格（avatar / architecture / cover 等工具脚本）
        if series == COVER_TOP_SERIES:
            continue
        # 4. 不以已知前缀开头
        if not any(name.startswith(p) for p in GEN_PREFIXES):
            issues.append({
                'file': str(py.relative_to(REPO_ROOT)),
                'rule': 'unknown-prefix',
                'detail': f"未识别前缀；已知前缀: {GEN_PREFIXES}",
            })
            continue

        # 例外系列 (ml/dayN)：用 dayN 编号代替 NN
        if series in DAY_NAMED_SERIES:
            # 允许 dayN 编号
            if re.search(r'day\d+', name):
                continue
            # 允许通用脚本（gen_fig_cnn.py / gen_fig_word2vec.py 等无 NN 但带 topic）
            if GENERIC_TOPIC_RE.match(name):
                continue

        # 例外系列 (ai-history)：用文章标题缩写代替 NN（如 rlhf/scalinglaw/cv）
        if series in TITLE_NAMED_SERIES:
            # 含 NN 编号（ai_70 / ai_booms / ai_consumer 等）
            if re.search(r'_\d{2,3}', name):
                continue
            # 文章标题缩写：纯小写 + 下划线（如 rlhf/scalinglaw/cv/three_giants）
            if re.match(r'^gen_(?:fig|cover)_[a-z_]+\.py$', name):
                continue

        # 推荐格式检查
        m = RECOMMENDED_RE.match(name)
        if not m:
            # 接受任何位置出现 NN（如 causal_00 / ai_70 / llm_09 等）
            has_nn = bool(re.search(r'_\d{2,3}', name))
            has_series = any(f'_{s}_' in name or f'_{s}{sep}' in name
                             for s in SERIES_CODES
                             for sep in ('_', ''))
            if not has_nn:
                issues.append({
                    'file': str(py.relative_to(REPO_ROOT)),
                    'rule': 'missing-NN',
                    'detail': f"缺文章编号 (NN)；推荐: gen_*_{series}_NN_topic.py",
                })
            elif not has_series:
                issues.append({
                    'file': str(py.relative_to(REPO_ROOT)),
                    'rule': 'missing-series',
                    'detail': f"缺 series 前缀 ({series})；推荐: gen_*_{series}_NN_topic.py",
                })
    return issues


def main():
    args = sys.argv[1:]
    quiet = '--quiet' in args
    args = [a for a in args if not a.startswith('--')]

    targets = args if args else [
        d.name for d in SCRIPTS_DIR.iterdir()
        if d.is_dir() and d.name not in {'__pycache__', 'utility'}
    ]

    all_issues = []
    ok_count = 0
    for series in targets:
        series_dir = SCRIPTS_DIR / series
        if not series_dir.is_dir():
            print(f"WARN: scripts/{series}/ 不存在", file=sys.stderr)
            continue
        issues = scan_series(series_dir)
        py_count = sum(1 for _ in series_dir.glob('*.py'))
        ok_count += py_count - len(issues)
        all_issues.extend(issues)

    # 输出
    if not quiet:
        print(f"\n=== 命名合规扫描：scripts/ 下 {len(targets)} 个 series 目录 ===\n")
        for series in targets:
            series_dir = SCRIPTS_DIR / series
            n = sum(1 for _ in series_dir.glob('*.py'))
            print(f"  scripts/{series}/: {n} files")

    print(f"\n=== 违规清单（{len(all_issues)} 条）===\n")
    if not all_issues:
        print("  ✅ 所有脚本符合命名规范")
    else:
        # 按 series 分组
        by_file = {}
        for issue in all_issues:
            by_file.setdefault(issue['file'], []).append(issue)
        for fpath, items in by_file.items():
            print(f"  {fpath}")
            for it in items:
                print(f"    [{it['rule']}] {it['detail']}")

    # exit code
    sys.exit(1 if all_issues else 0)


if __name__ == '__main__':
    main()
