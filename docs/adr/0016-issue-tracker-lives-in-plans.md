# ADR-0016 · 本地 issue tracker 落在 docs/superpowers/plans/

- 状态: accepted
- 登记日期: 2026-11-02
- 决策日期: 2026-11-02

## 约束

Matt Pocock 的 `to-spec` / `to-tickets` / `triage` 都要读写一个「issue tracker」，
前置是 `setup-matt-pocock-skills`。它默认落 `.scratch/<feature>/`，
同时官方支持本地 markdown（不需要 `gh`）。

本仓有三条约束跟这个默认打架：

1. **本机没有 `gh` CLI。** GitHub Issues 要在网页上手工建，且议题是公开的。
2. **本仓的分工是「草稿与设计私有、定稿才公开」**（[ADR-0009](0009-three-file-division-of-labour.md)、
   [ADR-0013](0013-glossary-and-adr-public-locations.md)）。`.gitignore` 里的私有区是
   `_local/` 与 `docs/superpowers/`，**没有 `.scratch/`**。默认落点会把还没定稿的设计
   随代码一起推进公开仓。
3. **`docs/superpowers/plans/<topic>/` 已经在用**，放 brief / report / diff / fix-report / re-review。

## 裁定

**issue tracker 用本地 markdown，落 `docs/superpowers/plans/<topic>/`；
spec 仍落 `docs/superpowers/specs/<topic>/YYYY-MM-DD-<topic>-design.md`。**

- 约定写进 `docs/agents/issue-tracker.md`（公开，只写规则不写内容），
  供 `to-spec` / `to-tickets` / `triage` 读取。
- 不新建 `.scratch/`，不为它改 `.gitignore`，不装 `gh`。
- 重跑 `setup-matt-pocock-skills` 时以 `docs/agents/issue-tracker.md` 为准，
  不要把它覆盖回默认值。

## 后果

- ticket 路径是 `docs/superpowers/plans/<topic>/issues/NN-<slug>.md`，
  一文件一条，`Status:` / `Blocked by:` 写在文件头。
- ticket 与 spec 都在私有区，不随代码公开；公开仓里只留最终代码与 README。
- **`_local/plan.md` 仍是进度的唯一事实源。** ticket 是工作单元，不是进度账本：
  做完的 ticket 留档不删，摘要只进 `plan.md`（ADR-0009）。
- 这套约定不跟仓库走：换仓库、换机器都要重新裁定一次。
- 两个格式冲突按本仓约定处理，不由 skill 默认值覆盖：ADR 必须三段式，
  术语表用根目录 `GLOSSARY-MAP.md` + `GLOSSARY-*.md`。两条都有
  `python tools/check_all.py` 守着。
