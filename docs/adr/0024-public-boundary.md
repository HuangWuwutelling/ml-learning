# ADR-0024 · GitHub 只收 README、复现代码和已发文章的项目

- 状态: accepted
- 登记日期: 2026-11-07

## 约束

仓里有三类东西混在一起：

1. 文章正文（`articles/`，本机独立 git 仓，有自己的历史）
2. 复现用的代码：`models/`、`notebooks/`、`data/`、`projects/` 里的已发文章项目、`scripts/` 里的测量与评测脚本
3. 没发文章的副线项目：QMS 质量合规助手、GB 36600 MCP server、Power BI 召回面板、Rust 重写 DBSCAN / PyO3 绑定 / embedding 微服务

一次误推把这三类一起推上了 GitHub：2026-11-07 推 `main` 时整条推了 57 笔 commit，
119 个副线项目文件跟着公开（QMS 目录 1.8 GB、三个 Rust 项目合计 3.6 GB、
GB 36600 MCP 语料与 Power BI 数据生成脚本都在里面）。

两条已确立的约束跟这次冲突：

- ADR-0011：副线项目不进简历，公司名 / 客户名一律不得出现在任何上 GitHub 的文件里，术语表和 ADR 也在内
- ADR-0013：`docs/adr/` 与 `docs/agents/` 是公开落点

副线项目代码暂不公开，不等于它的决策不公开：ADR-0017/0018/0019-0022 讲的是这批
项目的判定口径和架构选择（严重度走关键词规则、评测判定是纯函数、标准限值走确定性
规则、MCP 而非 REST、embedding 模型进程内只建一次），术语表也收了它们的词条。
这些内容不含客户信息，可以继续公开。

## 裁定

**GitHub 公开集合 = 白名单**，判定标准一句话：

> 一个项目进 GitHub 的条件是有一篇已发布文章支撑它。

| 进 GitHub | 不进 GitHub |
|---|---|
| `README.md`、`GLOSSARY-*.md` | `articles/`（本机独立仓） |
| `docs/adr/`、`docs/agents/` | `_local/`、`docs/superpowers/`、`.claude/` |
| `tools/` | `scripts/` 里的封面 / 出图 / notebook 生成脚本 |
| `models/`、`notebooks/`、`data/` | 6 个副线项目目录（见下） |
| 有已发布文章支撑的 `projects/` | 本机部署文件、运行产物、`.venv/` |
| 文章引用到的复现脚本 + 结果 JSON | |

按「有已发布文章支撑」这条标准，当前在 GitHub 里的项目是：生态环境法典智能问答
（llm/02、llm/11）、环保申报智能助手（llm/06、llm/09、llm/11）、环境违法严重程度识别
（llm/07）、ML Playground（ml/00、engineering/01-04）、LLM Streaming（llm/17）、
Injection Guard（llm/18）、契约测试套件 `projects/evals/`（ADR-0015）。

暂不公开的 6 个：`quality_compliance_assistant`、`env_standards_mcp`、
`power_bi_recall_dashboard`、`rust_dbscan`、`rust_pyo3_dbscan`、`rust_embedding_service`。

机制上落三件事：

1. **`.gitignore` 表达边界**：默认忽略 + 显式放行。`scripts/*` 全忽略，只放行 10 个
   复现 / 检查文件；6 个副线项目目录整目录忽略。规则写在文件里的注释上，不靠记忆。
2. **副线项目移出跟踪**：`git rm --cached` 拿掉索引条目，代码留在本机磁盘上，
   历史存进本地 `local-only` 分支（不推）。
3. **机器守门**：`tools/check_all.py` 加 `publish` 检查项，本地专属目录出现在跟踪
   列表里就判 FAIL，`scripts/` 里出现白名单外的文件也判 FAIL。

做完这三件，`main` 分支的跟踪集就等于 GitHub 上的内容，推送不再需要挑 commit：
**ADR-0006 的临时分支 + cherry-pick 那套流程退役，本文取代它。**

## 后果

- 推 GitHub 就是 `git push origin main`；推之前跑 `python tools/check_all.py --only publish`。
- 副线项目转正的条件：写出一篇已发布文章 → 从 `.gitignore` 删掉对应目录 →
  `git add` 该目录 → 提交。没有文章就留在本机。
- 已经推上去的 119 个文件仍在 GitHub 的历史里。清掉要 force-push 重写公开历史，
  本 ADR 不做这件事；要清就单独决定。
- ADR 与术语表继续公开：讲清判定口径和架构选择本身不泄露客户信息，公司名、客户名
  仍然一律不写（ADR-0011 不变）。
- 新增检查脚本时注意：公开的 `tools/check_all.py` 会调用 `scripts/utility/` 下的三个
  脚本，它们在白名单里，改名要同步改白名单。
