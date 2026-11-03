# projects/evals · 三个主项目的契约测试

一条命令复现「三个简历主项目的口径没有漂」：

```bash
python projects/evals/run_all.py          # 契约测试 + 行业名匹配单测（秒级）
python projects/evals/run_all.py -v       # 逐条打印
python projects/evals/run_all.py --agent-eval   # 额外跑 env_agent 真实评测（要 key）
```

## 为什么测试不放在三个主项目里面

`环境法律法规智能问答系统/`、`projects/env_agent/`、`projects/lora_finetune/`
都已定稿，是简历上会被追问的三个项目。契约测试放在它们目录里会带来两个问题：

1. **两处 git 仓库要手工同步**。GitHub 上那份 `env-law-qa` 是主仓目录的镜像，
   主仓加一批测试文件，镜像就得跟一次，跟不上就会出现「本地有、GitHub 没有」。
2. **改动边界会被一点点磨掉**。先加一个测试文件是「只加不改」，
   第二次改测试里的断言就已经在改项目的事实了。边界写在 ADR 里，
   目录也分开，边界才守得住。

所以契约测试全部外置到这里（见 ADR-0015）。三个主项目目录**一个字节都没动**。

## 契约测试怎么做到不 import 业务代码

`import tools` 会拉起 langchain_core，`import eval` 会拉起 torch 和 transformers。
契约测试要在一台只装了 pytest 的机器上也跑得动，所以：

- 配置默认值用正则从源码里取 `os.getenv(NAME, "default")` 的默认字面量，
  不 import、不读本机 `.env`，所以开发机的配置不会影响断言。
- 用例表（`CASES`）用 `ast` 解析，不 `ast.literal_eval` —— `eval_agent.py` 里
  有一条 `"avoid": ALL_TOOLS`，是同模块常量，直接 literal_eval 会抛
  `malformed node or string`。`conftest.py` 里的 `module_literal()` 先把模块顶层的
  字面量常量收进 env，再逐个节点解析。
- 产物（评测集、预测 jsonl、`eval_results.json`）直接读 JSON。

唯一一处真的执行了业务代码是 `rrf_fuse`，因为它是纯函数且只依赖 loguru，
值得用真行为而不是抄一份实现来测。

## 目录

| 文件 | 验什么 |
|---|---|
| `tests/conftest.py` | 路径定位 + 不 import 的源码取值工具 |
| `tests/test_rag_contract.py` | 默认检索档位是 dense、检索参数默认值、30 条评测集结构、RRF 融合行为 |
| `tests/test_agent_contract.py` | 12 条用例结构、工具清单与 `tools.py` 一致、模糊问题禁调工具 |
| `tests/test_lora_contract.py` | 34 条留出集分布、29.4% / 91.2% 可从产物复算、三组对照口径、LoRA 适配器配置 |

## 边界

- **只读**。本目录不写三个主项目里的任何文件。
- **验口径，不验智能**。模型答得好不好由各自的评测脚本负责：
  `projects/env_agent/eval_agent.py --repeat 3`（要 `DEEPSEEK_API_KEY` 和网络）、
  `projects/lora_finetune/eval.py`（要 GPU 和已训练的 adapter）。
  这两套跑不动时不要拿契约测试冒充评测结果。
