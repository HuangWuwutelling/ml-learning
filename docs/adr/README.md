# ADR 索引

一条决策一个文件，格式固定为「约束 → 裁定 → 后果」。文件名是 ASCII slug，标题是中文。

| 编号 | 决策 | 状态 |
|---|---|---|
| [0001](0001-article-no-unsourced-data.md) | 文章没有官方源就不放 | accepted |
| [0002](0002-deprecated-but-not-abandoned.md) | 三个主项目降级但不停用 | accepted |
| [0003](0003-default-retrieval-is-dense.md) | RAG 默认检索模式保持 dense | accepted |
| [0004](0004-deleted-article-figures-are-intentional.md) | 已发布文章的配图删除是有意的 | accepted |
| [0005](0005-frozen-projects-are-not-run-routinely.md) | 已定稿项目不主动运行 | accepted |
| [0006](0006-push-only-selected-commits.md) | 推 GitHub 只推选定的那一笔 | superseded by 0024 |
| [0007](0007-console-output-ascii-only.md) | 控制台输出只用 ASCII | accepted |
| [0008](0008-article-numbers-follow-source.md) | 文章数字以源文为准 | accepted |
| [0009](0009-three-file-division-of-labour.md) | README / CLAUDE.md / plan.md 三文件分工 | accepted |
| [0010](0010-main-projects-add-only.md) | 主项目零改动 | accepted |
| [0011](0011-side-projects-not-on-resume.md) | 副线项目不进简历 | accepted |
| [0012](0012-models-transform-not-generate.md) | 模型只做口径转换，不产生新数据 | accepted |
| [0013](0013-glossary-and-adr-public-locations.md) | 术语表与 ADR 的公开落点 | accepted |
| [0014](0014-dual-axis-review-no-rerank.md) | 双轴 review 不跨轴合并重排 | accepted |
| [0015](0015-contract-tests-live-outside-frozen-projects.md) | 契约测试放在冻结项目外面 | accepted |
| [0016](0016-issue-tracker-lives-in-plans.md) | 本地 issue tracker 落在 docs/superpowers/plans/ | accepted |
| [0017](0017-severity-by-keyword-rules.md) | 严重度判定走关键词规则，不调 LLM | accepted |
| [0018](0018-eval-scoring-is-pure-and-skip-is-not-pass.md) | 评测判定逻辑做成纯函数，跳过不等于通过 | accepted |
| [0019](0019-standard-limits-are-deterministic-rules.md) | 标准限值与风险分档走确定性规则，不交给模型 | accepted |
| [0020](0020-standard-pdf-not-in-repo.md) | 标准原文 PDF 不进仓库，提交解析后的 JSON 基线 | accepted |
| [0021](0021-mcp-not-rest.md) | 标准查询对外用 MCP server，不用 REST | accepted |
| [0022](0022-embedding-model-loaded-once-per-process.md) | embedding 模型进程内只建一次 | accepted |
| [0023](0023-plan-md-is-an-index.md) | plan.md 是索引层，细节分流到 notes / ADR / plans | accepted |
| [0024](0024-public-boundary.md) | GitHub 只收 README、复现代码和已发文章的项目 | accepted |
| [0025](0025-knowledge-point-cards-for-ai-history.md) | ai-history 从 13 起走知识点卡片体裁 | accepted |
| [0026](0026-job-projects-target-job-family-matrix.md) | 求职项目按岗位族能力矩阵设计，不为单份 JD 定制 | accepted |

新写一条：复制最近一条的文件，把编号往后排，文件名 slug 与标题保持一致，
然后在本表加一行。
