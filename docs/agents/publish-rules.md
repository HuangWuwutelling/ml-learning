# 发布规则：本地仓与 GitHub 的边界

决策依据见 `docs/adr/0024-public-boundary.md`。本文件是操作版：改 `.gitignore`、
推 GitHub、加新项目之前看这里。

## 一句话判定

> 一个项目进 GitHub 的条件是有一篇已发布文章支撑它。

文章正文本身永远不进 GitHub（`articles/` 是本机独立仓，有自己的历史和发布流程）。

## 目录速查

| 路径 | GitHub | 说明 |
|---|---|---|
| `README.md` / `GLOSSARY-*.md` | 进 | 公开索引与术语表 |
| `docs/adr/` / `docs/agents/` | 进 | 决策记录与开工清单 |
| `docs/superpowers/` | 不进 | review 工作区 |
| `tools/` | 进 | 全仓检查入口 |
| `models/` / `notebooks/` / `data/` | 进 | 文章的算法实现与数据 |
| `projects/evals/` | 进 | 三个主项目的契约测试（ADR-0015） |
| `projects/` 里 6 个副线项目 | 不进 | 见下表 |
| `scripts/` | 部分进 | 只放行复现脚本白名单 |
| `articles/` / `_local/` / `.claude/` | 不进 | 本机独立仓 / 本机私有 |

不进 GitHub 的 6 个副线项目：

```
projects/quality_compliance_assistant/    QMS 质量合规助手
projects/env_standards_mcp/               GB 36600 标准查询 MCP server
projects/power_bi_recall_dashboard/        Power BI 召回面板
projects/rust_dbscan/                     Rust 重写 DBSCAN
projects/rust_pyo3_dbscan/                PyO3 绑定层
projects/rust_embedding_service/          Qwen2.5 embedding 微服务
```

它们的代码在本机磁盘上（`git rm --cached` 只动索引，不删文件），历史在本地
`local-only` 分支，不推 GitHub。

## scripts 白名单

`scripts/` 整目录默认忽略（封面图、出图、notebook 生成脚本与算法本身无关）。
只放行下面这些「文章引用到的复现脚本 + 结果」：

| 文件 | 对应文章 |
|---|---|
| `scripts/ai-history/measure_kv_cache.py` | ai-history/12 |
| `scripts/ai-history/kv_cache_measure.json` | ai-history/12 的实测结果 |
| `scripts/llm/ragas/run_ragas_eval.py` | llm/12、llm/13、llm/19 |
| `scripts/llm/ragas/probe_context_recall.py` | llm/13 的召回探针 |
| `scripts/llm/ragas/testset.jsonl` | llm/12 的 23 题集 |
| `scripts/llm/ragas/testset_v2_30q.jsonl` | llm/13 的 30 题集 |
| `scripts/llm/ragas/requirements-ragas.txt` | RAGAS 依赖版本 |
| `scripts/utility/check_naming.py` | `tools/check_all.py` 调用 |
| `scripts/utility/check_article.py` | `tools/check_all.py` 调用 |
| `scripts/utility/count_cjk.py` | 字数口径工具 |
| `scripts/build_commands.py` | engineering/05、engineering/06 的 139 条命令数据生成器（1069 行） |

`scripts/build_commands.py` 与本机独立仓 `projects/wali_cmd/scripts/build_commands.py`
字节一致，是发布快照：小程序源码本身留本机，发布这份是为了让读者能在仓库里核对
文章引用的行数与那 139 条命令数据。脚本的输出路径指向小程序目录，要重新生成数据
请用独立仓里的那份。

新增复现脚本：改 `.gitignore` 的白名单 + 改 `tools/check_all.py` 里的
`PUBLISHED_SCRIPT_FILES`，两处必须同步，否则 `publish` 检查项会判 FAIL。

## 日常动作

```bash
# 推之前查一遍边界
python tools/check_all.py --only publish

# 推送（main 的跟踪集 == GitHub 内容，不需要挑 commit）
git push origin main
```

国内网络推不动（HTTPS 握手失败）时走 SSH + 本地代理，见
`docs/superpowers/plans/_meta/platform-gotchas.md` 的「Git Push」节。

## 副线项目什么时候能进

1. 写出一篇已发布文章（文章在 `articles/`，本机仓）
2. 从 `.gitignore` 删掉该项目的忽略规则
3. `git add` 该项目目录，检查 `git status` 里没有大文件、`.venv/`、运行产物
4. 提交并推送

没有文章就留在本机。同理，`tools/check_all.py` 里针对副线项目的检查项在
clone 上会判 SKIP（目录不存在），这是预期行为，不是坏了。

## 三个容易踩的坑

- **`git rm --cached` 不删磁盘文件**，只移出索引。想彻底删再自己动手。
- **`.gitignore` 对已跟踪文件无效**。文件一旦进了索引，加忽略规则也不会让它消失，
  必须先 `git rm --cached`。
- **移出索引不等于从历史里消失**。2026-11-07 误推的 119 个文件仍在 GitHub 的
  历史里，清掉要 force-push 重写公开历史。
