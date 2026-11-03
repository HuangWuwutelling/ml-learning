# ADR-0013 · 术语表与 ADR 的公开落点

- 状态: accepted
- 登记日期: 2026-11-01
- 决策日期: 2026-11-01

## 约束

`scripts/`、`.claude/`、`_local/`、`articles/` 都被 gitignore，放在这些目录下的文档在
GitHub 上看不到，等于没有证据。而本仓的术语是**跨目录**的：同一个数（例如「背景值」
「recall 分母」）同时出现在文章、`models/`、RAG 项目和评测脚本里，集中一处才有
「统一语言」的意义。

另外，`mattpocock-skills` 插件的 `ADR-FORMAT.md` 硬编码 `docs/adr/`：它扫该目录取最大
编号来推进下一条 ADR。

## 裁定

- **术语表**：`GLOSSARY-MAP.md` + 各 context 的 `GLOSSARY-*.md`，放**仓库根目录**。
  插件的多 context 约定正是「根放 MAP，指向各处」。
- **ADR**：放 **`docs/adr/`**（不是根 `adr/`），这样插件扫目录取编号时能找到已有 14 条，
  不会另建第二处 ADR 目录。
- **`.gitignore` 调整**：`docs/` 原本整体被排除，改成 `!docs/` 解除目录级排除，
  再用 `docs/superpowers/` 重新排除那一个私有子树（review 产物仍不上 GitHub）。
- 生成器与 check 脚本仍放 `scripts/`（功能性文件，本机自用）；但**统一检查入口放
  `tools/`**，因为它要作为公开证据出现在 GitHub 上。
- 同一概念只在一份术语表里定义；跨 context 借词要在 `GLOSSARY-MAP.md` 的接缝表里登记。

## 后果

根目录多出 5 个 md，`docs/` 下多出 `adr/`，这是有意的公开资产。
`docs/` 从「整体私有」变成「默认公开、superpowers 子树私有」，**以后往 `docs/` 放东西
前先想清楚是不是私有**，私有的进 `docs/superpowers/` 或 `_local/`。
这些文件是公开内容：**不得**写入公司名、客户名、未公开的求职策略细节。
术语表只收「本仓怎么用这个词」，不收「这个领域所有定义」。
