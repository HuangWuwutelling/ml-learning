"""统一检查入口：一条命令跑完全仓的静态一致性检查。

Usage:
    python tools/check_all.py                # 跑默认项（秒级）
    python tools/check_all.py --list         # 列出所有检查项及含义
    python tools/check_all.py --only rag,adr # 只跑指定项
    python tools/check_all.py --strict       # 把 WARN 升级为 FAIL

退出码 = FAIL 项数（0 表示全绿）。

设计约束：
- 只用标准库；Windows 11 + git bash + 系统 python，不依赖 make / just。
- 不 chdir，全部路径基于本文件位置定位仓库根。
- 缺依赖（articles/ 独立仓不在本机）时判 SKIP，不判 FAIL。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent

OK, FAIL, SKIP, WARN = 'OK', 'FAIL', 'SKIP', 'WARN'


# ── helpers ────────────────────────────────────────────────────────────────

def run(cmd, cwd=None, timeout=300):
    """跑一条命令，返回 (exit_code, stdout+stderr)。"""
    try:
        p = subprocess.run(cmd, cwd=cwd or REPO_ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except FileNotFoundError:
        return 127, f'command not found: {cmd[0]}'
    except subprocess.TimeoutExpired:
        return 124, f'timeout after {timeout}s'


def rel(path):
    try:
        return str(Path(path).relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


# ── checks ─────────────────────────────────────────────────────────────────

def check_naming():
    """scripts/ 下 gen_*.py 的命名规范。"""
    script = REPO_ROOT / 'scripts' / 'utility' / 'check_naming.py'
    if not script.is_file():
        return SKIP, 'scripts/utility/check_naming.py 不存在（scripts/ 是本机私有目录）'
    code, out = run([sys.executable, str(script), '--quiet'])
    if code == 0:
        return OK, '命名规范 0 违规'
    return FAIL, out.strip().splitlines()[-1] if out.strip() else 'check_naming.py 失败'


def check_article():
    """最新几篇已发文章的硬约束：破折号 / AI 腔禁词 / 图片与本地链接。"""
    script = REPO_ROOT / 'scripts' / 'utility' / 'check_article.py'
    articles = REPO_ROOT / 'articles'
    if not script.is_file():
        return SKIP, 'scripts/utility/check_article.py 不存在'
    if not articles.is_dir():
        return SKIP, 'articles/ 是独立仓，不在本机'
    files = sorted(articles.glob('*/*.md'), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    if not files:
        return SKIP, 'articles/ 下没有文章'
    code, out = run([sys.executable, str(script)] + [str(f) for f in files])
    if code == 0:
        return OK, f'{len(files)} 篇最新文章通过'
    return FAIL, out.strip().splitlines()[-1] if out.strip() else 'check_article.py 失败'


def check_glossary():
    """术语表：每个词条有 _Avoid_ 行，跨表不重名，MAP 的链接指向存在的文件。"""
    files = sorted(REPO_ROOT.glob('GLOSSARY-*.md'))
    if not files:
        return FAIL, '根目录没有任何 GLOSSARY-*.md'

    problems = []
    seen = {}
    for f in files:
        if f.name == 'GLOSSARY-MAP.md':
            continue
        text = f.read_text(encoding='utf-8')
        lines = text.splitlines()
        idxs = [i for i, ln in enumerate(lines) if re.match(r'^\*\*.+\*\*:', ln)]
        if not idxs:
            problems.append(f'{f.name}: 没有词条（`**Term**:` 行数为 0）')
            continue
        for n, i in enumerate(idxs):
            end = idxs[n + 1] if n + 1 < len(idxs) else len(lines)
            block = lines[i:end]
            term = re.match(r'^\*\*(.+?)\*\*:', block[0]).group(1)
            if not any(ln.startswith('_Avoid_:') for ln in block):
                problems.append(f'{f.name}: 词条「{term}」缺 _Avoid_ 行')
            if term in seen:
                problems.append(f'{f.name}: 词条「{term}」与 {seen[term]} 重名（一词一处）')
            else:
                seen[term] = f.name

    mapfile = REPO_ROOT / 'GLOSSARY-MAP.md'
    if not mapfile.is_file():
        problems.append('GLOSSARY-MAP.md 不存在')
    else:
        mtext = mapfile.read_text(encoding='utf-8')
        for target in re.findall(r'\]\((GLOSSARY[^)]*\.md)\)', mtext):
            if not (REPO_ROOT / target).is_file():
                problems.append(f'GLOSSARY-MAP.md 指向不存在的 {target}')

    if problems:
        return FAIL, '; '.join(problems[:5])
    return OK, f'{len(files) - 1} 份术语表，{len(seen)} 个词条，格式合规'


def check_adr():
    """ADR：编号连续、三段结构齐全、索引表列全。"""
    adr_dir = REPO_ROOT / 'docs' / 'adr'
    if not adr_dir.is_dir():
        return FAIL, 'docs/adr/ 不存在'
    files = sorted(p for p in adr_dir.glob('[0-9][0-9][0-9][0-9]-*.md'))
    if not files:
        return FAIL, 'docs/adr/ 下没有 ADR'

    problems = []
    nums = []
    for p in files:
        m = re.match(r'^(\d{4})-', p.name)
        if not m:
            continue
        nums.append(int(m.group(1)))
        text = p.read_text(encoding='utf-8')
        for section in ('## 约束', '## 裁定', '## 后果'):
            if section not in text:
                problems.append(f'{p.name}: 缺 {section} 节')
        if not text.lstrip().startswith('# ADR-'):
            problems.append(f'{p.name}: 首行不是 `# ADR-xxxx` 标题')
    if nums:
        expected = list(range(1, max(nums) + 1))
        if sorted(nums) != expected:
            gaps = sorted(set(expected) - set(nums))
            problems.append(f'编号不连续，缺 {gaps}')

    index = adr_dir / 'README.md'
    if not index.is_file():
        problems.append('docs/adr/README.md 不存在')
    else:
        itext = index.read_text(encoding='utf-8')
        for p in files:
            if p.name not in itext:
                problems.append(f'索引表漏了 {p.name}')

    if problems:
        return FAIL, '; '.join(problems[:5])
    return OK, f'{len(files)} 条 ADR，编号连续，三段齐全'


def _pytest(rel_path, cwd=None, python=None):
    d = REPO_ROOT / rel_path
    if not d.exists():
        return SKIP, f'{rel_path} 不存在'
    code, out = run([python or sys.executable, '-m', 'pytest', str(d), '-q'], cwd=cwd)
    tail = [ln for ln in out.strip().splitlines() if ln.strip()]
    summary = tail[-1] if tail else ''
    if code == 0:
        return OK, f'{rel_path}: {summary}'
    return FAIL, f'{rel_path}: {summary or out.strip()[-200:]}'


def check_rag():
    """env-rag 契约测试（只读产物，见 ADR-0015）。"""
    return _pytest('projects/evals/tests/test_rag_contract.py')


def check_agent():
    """env_agent 契约测试（只读产物，见 ADR-0015）。"""
    return _pytest('projects/evals/tests/test_agent_contract.py')


def check_lora():
    """lora_finetune 契约测试（只读产物，见 ADR-0015）。"""
    return _pytest('projects/evals/tests/test_lora_contract.py')


def check_agent_unit():
    """env_agent 的行业名匹配单测（文件在主项目里，只读不改）。"""
    return _pytest('projects/env_agent/test_match_industry.py',
                    cwd=REPO_ROOT / 'projects' / 'env_agent')


def check_envstd():
    """GB 36600 MCP server 的单测（语料层 / 规则层 / 评测集自身）。"""
    return _pytest('projects/env_standards_mcp/tests')


def check_qms_scoring():
    """QMS 评测判定口径的离线单测（不调 LLM / 不连 DB / 不碰向量库）。

    跑的是 QMS 项目自己的 tests/test_eval_scoring.py（13 条纯函数单测），
    守住 2026-11-03 那次「假指标」修复的判定口径不被改坏。
    项目自带 .venv/（NumPy 1.26.4，chromadb 才起得来）；没有 venv 时用当前解释器
    也能跑（这批是纯函数）。依赖没装全 → SKIP，不算失败。
    """
    proj = REPO_ROOT / 'projects' / 'quality_compliance_assistant'
    venv_py = proj / '.venv' / 'Scripts' / 'python.exe'
    if not venv_py.exists():
        venv_py = proj / '.venv' / 'bin' / 'python'
    python = str(venv_py) if venv_py.exists() else None
    rel_path = 'projects/quality_compliance_assistant/tests/test_eval_scoring.py'
    if not (REPO_ROOT / rel_path).exists():
        return SKIP, f'{rel_path} 不存在'
    code, out = run([python or sys.executable, '-m', 'pytest',
                     str(REPO_ROOT / rel_path), '-q'], cwd=proj)
    tail = [ln for ln in out.strip().splitlines() if ln.strip()]
    summary = tail[-1] if tail else ''
    if code == 0:
        return OK, f'{rel_path}: {summary}'
    if 'ModuleNotFoundError' in out or 'No module named' in out:
        return SKIP, f'{rel_path}: 依赖没装全（缺 langchain-community 等），跳过'
    return FAIL, f'{rel_path}: {summary or out.strip()[-200:]}'


def check_envstd_eval():
    """GB 36600 MCP server 的真实评测：起 server 走 MCP 通道跑 38 条用例。"""
    script = REPO_ROOT / 'projects' / 'env_standards_mcp' / 'eval' / 'run_eval.py'
    if not script.is_file():
        return SKIP, 'projects/env_standards_mcp/eval/run_eval.py 不存在'
    code, out = run([sys.executable, str(script)],
                    cwd=REPO_ROOT / 'projects' / 'env_standards_mcp')
    summary = ''
    for line in out.splitlines():
        if line.startswith('用例 '):
            summary = line.strip()
    if code == 0:
        return OK, summary or 'env_standards_mcp 评测通过'
    return FAIL, summary or out.strip()[-200:]


MEMORY_MAX_CHARS = 6000      # MEMORY.md 总长上限：它是每轮重读的前缀
MEMORY_LINE_MAX = 300        # 单条索引行上限
MEMORY_FILE_MAX = 12000      # 单个记忆文件上限（超了就该压缩，只报 WARN）
MEMORY_DESC_MAX = 200        # description 上限（召回靠它，太长没意义）

PLAN_MAX_CHARS = 30000       # plan.md 总长上限（字符，不是字节）
PLAN_ROW_MAX = 200           # plan.md 变更记录单行上限（字符）
PLAN_ENFORCE = True          # True = 超标判 FAIL；False = 只报 WARN


def memory_dir():
    """Claude Code 把记忆库放在 ~/.claude/projects/<仓库路径 slug>/memory/。"""
    slug = str(REPO_ROOT).replace(':', '-').replace('\\', '-').replace('/', '-')
    return Path.home() / '.claude' / 'projects' / slug / 'memory'


def check_memory():
    """记忆库体检：索引不能长成档案，链接要有效，每个文件要有 description。"""
    d = memory_dir()
    if not d.is_dir():
        return SKIP, f'{rel(d)} 不存在（记忆库跟 Claude Code 会话目录走，换机器就没有）'
    index = d / 'MEMORY.md'
    if not index.is_file():
        return FAIL, 'MEMORY.md 不存在'

    text = index.read_text(encoding='utf-8')
    problems = []

    if len(text) > MEMORY_MAX_CHARS:
        problems.append(f'MEMORY.md {len(text)} 字符 > 上限 {MEMORY_MAX_CHARS}')

    rows = [ln for ln in text.splitlines() if ln.startswith('- [')]
    over = sorted((len(ln), ln[:30]) for ln in rows if len(ln) > MEMORY_LINE_MAX)
    if over:
        problems.append(f'{len(over)} 条索引行 > {MEMORY_LINE_MAX} 字符，最长 {over[-1][0]}：{over[-1][1]}…')

    for target in re.findall(r'\]\(([^)]+\.md)\)', text):
        if not (d / target).is_file():
            problems.append(f'MEMORY.md 指向不存在的 {target}')

    warn = []
    worst = (0, '')
    for p in sorted(d.glob('*.md')):
        if p.name == 'MEMORY.md':
            continue
        body = p.read_text(encoding='utf-8')
        m = re.search(r'^description:\s*(.+)$', body, re.M)
        if not m:
            problems.append(f'{p.name} 缺 description')
        elif len(m.group(1)) > MEMORY_DESC_MAX:
            problems.append(f'{p.name} 的 description {len(m.group(1))} 字符 > {MEMORY_DESC_MAX}')
        if len(body) > worst[0]:
            worst = (len(body), p.name)
        if len(body) > MEMORY_FILE_MAX:
            warn.append(f'{p.name} {len(body)} 字符')

    if problems:
        return FAIL, '; '.join(problems[:5])
    if warn:
        return WARN, f'{len(warn)} 个记忆文件 > {MEMORY_FILE_MAX} 字符待压缩：{", ".join(warn[:3])}'
    return OK, f'MEMORY.md {len(text)} 字符 / {len(rows)} 条索引 / 最大文件 {worst[1]} {worst[0]} 字符'


def plan_changelog_rows(text):
    """抽出 plan.md 变更记录表里的数据行（以 | YYYY-MM-DD 开头的行）。

    只认 `## 项目变更记录` 这节里的行，别处同样以竖线开头的表格不算。
    """
    rows = []
    inside = False
    for ln in text.splitlines():
        if ln.startswith('## '):
            inside = '变更记录' in ln
            continue
        if inside and re.match(r'^\|\s*\d{4}-\d{2}-\d{2}', ln):
            rows.append(ln)
    return rows


def check_plan():
    """plan.md 当索引不当档案：总长与变更记录单行都有上限。

    `_local/` 是本机私有目录，不在这个仓的 git 里，换机器就没有这个文件，
    所以缺文件判 SKIP 不判 FAIL，跟 check_memory() 同一个套路。
    """
    p = REPO_ROOT / '_local' / 'plan.md'
    if not p.is_file():
        return SKIP, '_local/plan.md 不存在（plan.md 是本机私有文件）'

    text = p.read_text(encoding='utf-8')
    rows = plan_changelog_rows(text)
    warns = []

    if len(text) > PLAN_MAX_CHARS:
        warns.append(f'plan.md {len(text)} 字符 > 上限 {PLAN_MAX_CHARS}')
    over = [r for r in rows if len(r) > PLAN_ROW_MAX]
    if over:
        warns.append(f'变更记录 {len(over)} 行 > {PLAN_ROW_MAX} 字符，最长 {max(len(r) for r in over)}')

    if warns:
        return (FAIL if PLAN_ENFORCE else WARN), '; '.join(warns)
    return OK, f'plan.md {len(text)} 字符 / 变更记录 {len(rows)} 行'


def check_clean():
    """主仓工作区状态：只报告，不判失败（未跟踪的本地文件是常态）。"""
    code, out = run(['git', 'status', '--porcelain'])
    if code != 0:
        return SKIP, '不是 git 仓库或 git 不可用'
    lines = [ln for ln in out.strip().splitlines() if ln.strip()]
    if not lines:
        return OK, '主仓工作区干净'
    return WARN, f'主仓有 {len(lines)} 项改动或未跟踪文件'


# GitHub 公开集合（ADR-0024）。本地专属目录不许进跟踪集；scripts/ 只放行复现白名单。
PUBLISHED_SCRIPT_FILES = {
    'scripts/ai-history/measure_kv_cache.py',
    'scripts/ai-history/kv_cache_measure.json',
    'scripts/llm/ragas/probe_context_recall.py',
    'scripts/llm/ragas/requirements-ragas.txt',
    'scripts/llm/ragas/run_ragas_eval.py',
    'scripts/llm/ragas/testset.jsonl',
    'scripts/llm/ragas/testset_v2_30q.jsonl',
    'scripts/utility/check_article.py',
    'scripts/utility/check_naming.py',
    'scripts/utility/count_cjk.py',
    'scripts/build_commands.py',
}

LOCAL_ONLY_PATHS = (
    'articles',
    '_local',
    'docs/superpowers',
    'projects/quality_compliance_assistant',
    'projects/env_standards_mcp',
    'projects/power_bi_recall_dashboard',
    'projects/rust_dbscan',
    'projects/rust_pyo3_dbscan',
    'projects/rust_embedding_service',
)


def check_publish():
    """GitHub 公开边界：本地专属目录不许被跟踪，scripts/ 只认复现白名单。"""
    code, out = run(['git', 'ls-files'])
    if code != 0:
        return SKIP, 'git 不可用或不是 git 仓库'
    tracked = [ln.strip() for ln in out.splitlines() if ln.strip()]

    problems = []
    for path in LOCAL_ONLY_PATHS:
        prefix = path.rstrip('/') + '/'
        hits = [t for t in tracked if t == path or t.startswith(prefix)]
        if hits:
            problems.append(f'{prefix} 有 {len(hits)} 个文件被跟踪（本地专属，不上 GitHub）')

    extra = sorted(t for t in tracked
                   if t.startswith('scripts/') and t not in PUBLISHED_SCRIPT_FILES)
    if extra:
        problems.append(f'scripts/ 白名单外有 {len(extra)} 个文件：{", ".join(extra[:3])}')

    missing = sorted(f for f in PUBLISHED_SCRIPT_FILES if f not in tracked)
    if missing:
        problems.append(f'复现脚本白名单缺 {len(missing)} 个：{", ".join(missing[:3])}')

    if problems:
        return FAIL, '; '.join(problems[:5])
    return OK, (f'跟踪集 {len(tracked)} 个文件 / 本地专属目录 0 个 / '
                f'scripts/ 白名单 {len(PUBLISHED_SCRIPT_FILES)} 个')


CHECKS = [
    ('naming', 'scripts/ 下生成器脚本的命名规范', check_naming),
    ('article', '最新 3 篇已发文章的硬约束（破折号 / 禁词 / 图片与链接）', check_article),
    ('glossary', '术语表格式、跨表不重名、MAP 链接有效', check_glossary),
    ('adr', 'ADR 编号连续、三段结构、索引表齐全', check_adr),
    ('rag', 'env-rag 边界测试（pytest）', check_rag),
    ('agent', 'env_agent 边界测试（pytest）', check_agent),
    ('lora', 'lora_finetune 边界测试（pytest）', check_lora),
    ('agent_unit', 'env_agent 行业名匹配单测（pytest）', check_agent_unit),
    ('envstd', 'GB 36600 MCP server 单测（pytest）', check_envstd),
    ('envstd_eval', 'GB 36600 MCP server 真实评测（走 MCP 通道）', check_envstd_eval),
    ('qms', 'QMS 评测判定口径离线单测（pytest，不调 LLM）', check_qms_scoring),
    ('memory', '记忆库体检：MEMORY.md 当索引不当档案（长度 / 链接 / description）', check_memory),
    ('plan', 'plan.md 当索引不当档案（总长 / 变更记录单行上限）', check_plan),
    ('publish', 'GitHub 公开边界：本地专属目录未被跟踪 + scripts/ 白名单', check_publish),
    ('clean', '主仓工作区状态（只报告）', check_clean),
]


def main():
    ap = argparse.ArgumentParser(description='统一检查入口')
    ap.add_argument('--list', action='store_true', help='列出所有检查项')
    ap.add_argument('--only', help='只跑指定项，逗号分隔')
    ap.add_argument('--strict', action='store_true', help='把 WARN 升级为 FAIL')
    args = ap.parse_args()

    if args.list:
        print('检查项：')
        for name, desc, _ in CHECKS:
            print(f'  {name:<9} {desc}')
        return 0

    selected = CHECKS
    if args.only:
        want = {s.strip() for s in args.only.split(',') if s.strip()}
        unknown = want - {n for n, _, _ in CHECKS}
        if unknown:
            print(f'未知检查项: {sorted(unknown)}', file=sys.stderr)
            return 2
        selected = [c for c in CHECKS if c[0] in want]

    results = []
    for name, desc, fn in selected:
        try:
            status, detail = fn()
        except Exception as exc:                      # noqa: BLE001
            status, detail = FAIL, f'{type(exc).__name__}: {exc}'
        results.append((name, status, detail))
        print(f'[{status:<4}] {name:<9} {detail}')

    fails = sum(1 for _, s, _ in results if s == FAIL)
    warns = sum(1 for _, s, _ in results if s == WARN)
    if args.strict:
        fails += warns
    print(f'\n{len(results)} 项：FAIL {fails}，WARN {warns}，其余通过或跳过')
    return fails


if __name__ == '__main__':
    sys.exit(main())
