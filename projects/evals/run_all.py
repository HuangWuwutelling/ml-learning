"""一条命令复现三个主项目的契约测试。

Usage:
    python projects/evals/run_all.py             # 跑契约测试（秒级，不需要 key / GPU）
    python projects/evals/run_all.py -v          # 逐条打印
    python projects/evals/run_all.py --agent-eval # 额外跑 env_agent 的真实评测（要 key）

为什么把契约测试放在 `projects/evals/` 而不是三个主项目里面：
三个主项目已定稿，目录内一个字节都不改（ADR-0015）。契约测试要的东西
（评测集、预测产物、配置默认值）全都能只读拿到，放外置目录就不用动它们，
也不会让 GitHub 上那份 `env-law-qa` 镜像多出一批要手工同步的文件。

契约测试验的是「口径没漂」：默认检索档位、评测集条数与 id、工具清单、
README 上的数字和产物对不对得上。模型答得好不好由各自的评测脚本负责：
    python projects/env_agent/eval_agent.py --repeat 3   # 要 DEEPSEEK_API_KEY
    python projects/lora_finetune/eval.py                # 要 GPU 和已训练的 adapter
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACT_DIR = Path(__file__).resolve().parent / "tests"
AGENT_TEST = REPO_ROOT / "projects" / "env_agent" / "test_match_industry.py"


def run(label, cmd, cwd):
    """跑一条命令，返回退出码。"""
    print(f'\n--- {label} ---', flush=True)
    code = subprocess.call(cmd, cwd=str(cwd))
    print(f'--- {label}: exit {code} ---', flush=True)
    return code


def main():
    ap = argparse.ArgumentParser(description='复现三个主项目的契约测试')
    ap.add_argument('-v', '--verbose', action='store_true', help='逐条打印用例')
    ap.add_argument('--agent-eval', action='store_true',
                    help='额外跑 env_agent 的真实评测（需要 DEEPSEEK_API_KEY 和网络）')
    args = ap.parse_args()

    pytest_args = ['-m', 'pytest']
    if args.verbose:
        pytest_args.append('-v')
    else:
        pytest_args.append('-q')

    results = []

    results.append((
        '契约测试（env-rag / env_agent / lora_finetune）',
        run('契约测试', [sys.executable] + pytest_args + [str(CONTRACT_DIR)], REPO_ROOT),
    ))

    if AGENT_TEST.is_file():
        results.append((
            '行业名匹配单测（env_agent）',
            run('行业名匹配单测',
                [sys.executable] + pytest_args + [str(AGENT_TEST)],
                REPO_ROOT / "projects" / "env_agent"),
        ))

    if args.agent_eval:
        if not os.getenv('DEEPSEEK_API_KEY'):
            print('\n跳过 env_agent 真实评测：环境里没有 DEEPSEEK_API_KEY。')
        else:
            results.append((
                'env_agent 真实评测（12 用例 x3 轮）',
                run('env_agent 真实评测',
                    [sys.executable, 'eval_agent.py', '--repeat', '3'],
                    REPO_ROOT / "projects" / "env_agent"),
            ))

    print('\n========== 汇总 ==========')
    for label, code in results:
        print(f'[{"PASS" if code == 0 else "FAIL"}] {label}')
    failed = sum(1 for _, code in results if code != 0)
    print(f'\n{len(results)} 组，失败 {failed} 组')
    return failed


if __name__ == '__main__':
    sys.exit(main())
