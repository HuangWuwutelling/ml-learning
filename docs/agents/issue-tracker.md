# Issue tracker：本地 Markdown（落 docs/superpowers/plans/）

本仓的 issue tracker 是**本地 markdown**。不用 GitHub Issues（本机没有 `gh`，
且议题会公开），也不用 `.scratch/`（不在 `.gitignore` 的私有区里）。
裁定见 [ADR-0016](../adr/0016-issue-tracker-lives-in-plans.md)。

## 约定

- 一个特性一个目录：`docs/superpowers/plans/<topic>/`
- spec 在 `docs/superpowers/specs/<topic>/YYYY-MM-DD-<topic>-design.md`，
  不在 plan 目录里再复制一份（每个事实只有一处）
- 实施 ticket 一文件一条：`docs/superpowers/plans/<topic>/issues/NN-<slug>.md`，
  从 `01` 编号，不要合并成一个 tickets 文件
- 每个 ticket 文件头写三行：

  ```markdown
  Status: ready-for-agent
  Blocked by: none
  Type: task
  ```

  - `Status:` —— `needs-triage` / `needs-info` / `ready-for-agent` /
    `ready-for-human` / `wontfix`（triage 的五档）；
    `/wayfinder` 另用 `claimed` / `resolved`
  - `Blocked by:` —— 挡住它的 ticket 编号；全部 `resolved` 才算解锁
  - `Type:` —— 只有 `/wayfinder` 的 ticket 需要：`task` / `research` / `prototype` / `grilling`
- 讨论追加在文件底部 `## Comments` 下，不另建文件

## 与 Matt 默认约定的三处偏差

`grill-with-docs` / `to-spec` / `to-tickets` / `domain-modeling` 跑起来时按这张表，
不按 skill 的默认值：

| 项 | Matt 默认 | 本仓 |
|---|---|---|
| tracker 落点 | `.scratch/<feature>/` | `docs/superpowers/plans/<topic>/` |
| ADR 格式 | `docs/adr/NNNN-slug.md`，一段话即可，章节可选 | 同路径，但必须有 `# ADR-NNNN · 标题` 与 `## 约束` / `## 裁定` / `## 后果` 三节，编号四位连续 |
| 术语表布局 | 每个 context 一个目录，目录下 `GLOSSARY.md` | 根目录 `GLOSSARY-MAP.md` + 若干 `GLOSSARY-*.md`，词条格式 `**Term**:` + `_Avoid_:`，跨表不重名 |

写完跑一遍 `python tools/check_all.py`，FAIL 0 才算收口。
`--only adr,glossary` 可以只验这两条格式。
