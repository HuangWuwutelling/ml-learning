import json
import os
import socket
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Prevent eval_tools / eval_no_tool from hanging on a slow LLM API (previous
# run timed out at 120s because DeepSeek returned 401 slowly). Default to
# 30s — short enough to fail fast and let the run complete.
socket.setdefaulttimeout(30)
# Ensure project root is on sys.path so 'agent' and 'qms_app' resolve,
# AND remove this script's directory (eval/) so it does NOT shadow the
# `datasets` package (which would break the sentence_transformers import
# chain because `from datasets import Dataset` would hit eval/datasets/
# instead of the installed HuggingFace `datasets` library).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
# Use normcase for case-insensitive comparison (Windows fs is case-insensitive
# but sys.path strings may differ in case between __file__ resolution and the
# cwd-derived path Python inserts at startup).
for i, p in enumerate(sys.path):
    if os.path.normcase(p) == os.path.normcase(_SCRIPT_DIR):
        sys.path.pop(i)
        break
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qms_project.settings')
django.setup()
from agent.graph import run_with_trace
from agent.tools import assess_severity, get_embeddings
from eval.scoring import tool_set_scores, no_tool_score
from langchain_community.vectorstores import Chroma

RESULTS_DIR = Path('eval/results')
CHROMA_DIR = str(Path('knowledge/chroma_db'))

def eval_severity():
    """严重度判定：关键词规则表回归测试。

    这不是分类能力评测。severity_25.jsonl 的标签和 agent/tools.py 里的关键词
    表出自同一套东西，所以这个指标跑的是「规则表有没有被改坏」的回归检查：
    改了关键词表而没同步改数据集，这里就会掉分。
    """
    cases = [json.loads(l) for l in open('eval/datasets/severity_25.jsonl', encoding='utf-8')]
    correct = 0
    per_case = []
    for c in cases:
        r = assess_severity.invoke({'complaint_text': c['text']})
        ok = r['severity'] == c['expected']
        correct += int(ok)
        per_case.append({'id': c['id'], 'expected': c['expected'],
                         'got': r['severity'], 'ok': ok})
    return {
        'name': 'severity_25',
        'total': len(cases),
        'correct': correct,
        'accuracy': correct / len(cases),
        'target': 0.75,
        'scoring': '关键词规则表回归测试：标签与规则表同源，不代表分类能力',
        'per_case': per_case,
        'summary': f'{correct}/{len(cases)} label match',
    }

def eval_tools():
    """工具选择：agent 实际调了哪些工具 vs 预期该调哪些。

    改之前这项是假指标：另起一个 LLM 去「猜」该调哪些工具，只要模型回了非空
    字符串就算对，从来没跟 expected_tools 比过，所以它不可能失败。
    现在改成跑真 agent，从轨迹的 tool_calls 里读实际调用。
    """
    cases = [json.loads(l) for l in open('eval/datasets/tools_30.jsonl', encoding='utf-8')]
    per_case = []
    for c in cases:
        expected = c['expected_tools']
        try:
            trace = run_with_trace(c['query'], thread_id=c['id'])
        except Exception as e:
            per_case.append({'id': c['id'], 'expected': expected, 'called': [],
                             'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'exact': 0.0,
                             'error': f'{type(e).__name__}: {str(e)[:150]}'})
            continue
        called = trace['tools_called']
        s = tool_set_scores(called, expected)
        per_case.append({'id': c['id'], 'expected': expected, 'called': called,
                         'precision': s['precision'], 'recall': s['recall'],
                         'f1': s['f1'], 'exact': s['exact']})
    n = len(cases)
    exact = sum(1 for x in per_case if x['exact'] >= 1.0)
    mean_f1 = sum(x['f1'] for x in per_case) / n
    errors = sum(1 for x in per_case if 'error' in x)
    if errors == n:
        # 一条都没跑起来：这不是「准确率 0」，是「没测出来」。
        # 报成 FAIL 会把「没配 key」说成「agent 全错」。
        first = next(x['error'] for x in per_case if 'error' in x)
        raise RuntimeError(f'{n} cases all failed to run: {first}')
    return {
        'name': 'tools_30',
        'total': n,
        # accuracy 是集合 F1 的均值（少调、多调都扣分）；correct 是集合完全一致的条数
        'correct': exact,
        'accuracy': mean_f1,
        'target': 0.80,
        'exact_match': exact,
        'mean_precision': sum(x['precision'] for x in per_case) / n,
        'mean_recall': sum(x['recall'] for x in per_case) / n,
        'errors': errors,
        'scoring': 'accuracy = 实际调用工具集合与 expected_tools 的集合 F1；correct = 集合完全一致的条数',
        'per_case': per_case,
        'summary': f'mean F1 {mean_f1:.2%}, exact {exact}/{n}, errors {errors}',
    }

def eval_no_tool():
    """不该调工具：这 8 条一次工具都不该调，但仍然要回话。

    改之前用「回复长度 < 100」当「没调工具」的代理：调了工具回一段长文照样算过，
    没调工具但回得长的反而算错。现在直接读轨迹里的 tool_calls。
    """
    cases = [json.loads(l) for l in open('eval/datasets/no_tool_8.jsonl', encoding='utf-8')]
    per_case = []
    for c in cases:
        try:
            trace = run_with_trace(c['query'], thread_id=c['id'])
        except Exception as e:
            per_case.append({'id': c['id'], 'called': [], 'reply_len': 0, 'ok': False,
                             'error': f'{type(e).__name__}: {str(e)[:150]}'})
            continue
        called = trace['tools_called']
        s = no_tool_score(called, trace['text'])
        per_case.append({'id': c['id'], 'called': called, 'reply_len': len(trace['text']),
                         'no_tool': s['no_tool'], 'replied': s['replied'],
                         'ok': bool(s['ok'])})
    n = len(cases)
    correct = sum(1 for x in per_case if x['ok'])
    errors = sum(1 for x in per_case if 'error' in x)
    if errors == n:
        # 同上：一条都没跑起来 = 没测出来，不是「8 条全错」
        first = next(x['error'] for x in per_case if 'error' in x)
        raise RuntimeError(f'{n} cases all failed to run: {first}')
    return {
        'name': 'no_tool_8',
        'total': n,
        'correct': correct,
        'accuracy': correct / n,
        'target': 1.00,
        'errors': errors,
        'scoring': '正确 = 一次工具都没调，并且 agent 仍然回了一句话',
        'per_case': per_case,
        'summary': f'{correct}/{n} no-tool + replied' + (f', errors {errors}' if errors else ''),
    }

def eval_rag():
    """Real precision@5 (no filter).

    Previous version constrained results with `filter={'doc_id': {'$in': expected}}`,
    which made the metric degenerate: it only measured whether the expected doc
    had >= 5 chunks. This version retrieves top 5 from the full collection and
    counts how many have an `expected_doc_ids` doc_id — true precision.
    """
    cases = [json.loads(l) for l in open('eval/datasets/rag_20.jsonl', encoding='utf-8')]
    # 复用 agent 的 embedding 模型：同一个进程里只建一次（transformers 4.57
    # 的 meta device 加载并发会 race），也保证测的就是 agent 用的那个检索器。
    embeddings = get_embeddings()
    chroma = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings,
                    collection_name='qms_knowledge')
    per_case = []
    for c in cases:
        # NO filter — get top 5 from full collection
        results = chroma.similarity_search(c['query'], k=5)
        relevant = sum(1 for r in results
                       if r.metadata.get('doc_id') in c['expected_doc_ids'])
        p = relevant / 5 if results else 0.0
        per_case.append({'id': c['id'], 'precision': p, 'relevant': relevant,
                         'expected': c['expected_doc_ids']})
    correct = sum(1 for c in cases
                  for x in per_case
                  if x['id'] == c['id'] and x['precision'] >= c['min_precision_at_5'])
    avg_p = sum(x['precision'] for x in per_case) / len(per_case)
    return {
        'name': 'rag_20',
        'total': len(cases),
        'correct': correct,
        'accuracy': correct / len(cases),
        'avg_precision': avg_p,
        'per_case': per_case,
        # Honest target for 47-chunk demo KB with bge-small-zh-v1.5
        # (real precision, not the degenerate filter-based one)
        'target': 0.40,
        'scoring': 'precision@5 = 全集合 top-5 里 doc_id 落在 expected_doc_ids 的占比；correct = 单条 precision >= min_precision_at_5',
        'summary': f'{correct}/{len(cases)} pass, avg precision@5 {avg_p:.2f}',
    }

METRICS = [
    (eval_severity, 'severity_25'),
    (eval_tools, 'tools_30'),
    (eval_no_tool, 'no_tool_8'),
    (eval_rag, 'rag_20'),
]


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description='跑 QMS 评测')
    ap.add_argument('--only', help='只跑指定指标，逗号分隔（如 tools_30,no_tool_8）')
    return ap.parse_args(argv)


def main(argv=None):
    """跑全部指标，落盘结果，返回退出码。

    退出码三态：
      0 = 所有指标都跑到且达标
      1 = 有指标跑到但低于目标
      2 = 有指标没跑到（跳过），数字没测出来，不算失败也不能当通过

    argv 传 None 时读 sys.argv[1:]；测试直接传 []，免得 pytest 的参数被 argparse
    当成评测选项解析掉（argparse 的用法错误也用退出码 2，语义上同样是「没测出来」）。

    --only 只跑一部分指标：整轮评测要十几分钟，机器内存吃紧时按指标分开跑，
    每次进程短一点；结果文件按指标增量落盘，中途被打断也不至于全丢。
    """
    args = parse_args(argv)
    selected = METRICS
    if args.only:
        want = {s.strip() for s in args.only.split(',') if s.strip()}
        unknown = want - {n for _, n in METRICS}
        if unknown:
            print(f'unknown metric: {sorted(unknown)}', file=sys.stderr)
            return 2
        selected = [m for m in METRICS if m[1] in want]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results = {
        'timestamp': datetime.now().isoformat(),
        'metrics': {},
    }
    failed = []
    skipped = []
    passed = []
    out = RESULTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    def save():
        """增量落盘：每跑完一个指标写一次，中途被打断也留着已测出的数字。"""
        results['summary'] = {'passed': passed, 'failed': failed, 'skipped': skipped}
        # 显式写 UTF-8：write_text 默认用系统 locale（Windows 上是 GBK），
        # 落盘的中文就不是 UTF-8 了，别人拿 UTF-8 读会直接 UnicodeDecodeError。
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')

    # Wrap each fn() call in try/except so a failure in one metric
    # doesn't abort the whole run. Save partial results with
    # "status": "skipped" and the error message for the failed ones.
    for fn, name in selected:
        try:
            r = fn()
            ok = r['accuracy'] >= r['target']
            r['passed'] = ok
            r['status'] = 'ok'
            results['metrics'][name] = r
            if ok:
                passed.append(name)
            else:
                failed.append(name)
            print(f"[{name}] {r['summary']} (target {r['target']:.0%}) {'PASS' if ok else 'FAIL'}")
        except Exception as e:
            results['metrics'][name] = {'name': name, 'status': 'skipped',
                                        'error': f'{type(e).__name__}: {str(e)[:200]}'}
            skipped.append(name)
            print(f"[{name}] SKIPPED: {type(e).__name__}: {str(e)[:120]}")
        save()
    print(f'\n[done] saved to {out}')
    print(f"[summary] pass {len(passed)}, fail {len(failed)}, skipped {len(skipped)}")
    if skipped:
        print('[summary] skipped metrics were NOT measured - do not read them as passing')
    if failed:
        return 1
    if skipped:
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
