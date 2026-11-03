# GLOSSARY-MAP

本仓有四个 context。每个 context 一份术语表，**术语只在它所属的 context 内有效**。
跨 context 借词时，两份表里都要能查到，并在各自表的 `## Relationships` 里登记关系。

| Context | 术语表 | 覆盖范围 |
|---|---|---|
| 环境科学 | [GLOSSARY-environment-science.md](GLOSSARY-environment-science.md) | 土壤/沉积物/水质、污染指数与分级表、标准限值、判源流程 |
| AI 应用工程 | [GLOSSARY-ai-application.md](GLOSSARY-ai-application.md) | RAG 检索、Agent 编排、微调、评测口径 |
| 发文管线 | [GLOSSARY-publishing-pipeline.md](GLOSSARY-publishing-pipeline.md) | 文章口径、参数标注、字数统计、状态词 |
| 工程流程与工具链 | [GLOSSARY-engineering-process.md](GLOSSARY-engineering-process.md) | 文档分层、阶段边界、review 协议、测试与检查入口 |

## 跨 context 的接缝

| 接缝 | 说明 | 各自表里的入口 |
|---|---|---|
| 标准文本作为知识库语料 | 环境科学的法典/标准条文，是 AI 应用工程里 RAG 的检索对象 | 环境科学「判源三步」/ AI 应用工程「dense 检索」 |
| 评测集 | 同一批文件，两种读法：环境科学的评测题要回源核，AI 应用的评测题要按 want/avoid 判 | AI 应用工程「评测集」/ 发文管线「CJK 字数口径」 |
| 归档基线 | 发文管线的产物（PNG/CSV）在工程流程里有一条「重跑必须逐字节不变」的硬断言 | 发文管线「封面图」/ 工程流程「归档基线」 |

## 决策记录

一条决策一个文件，放在 [`docs/adr/`](docs/adr/)，格式固定为「约束 → 裁定 → 后果」。
索引见 [docs/adr/README.md](docs/adr/README.md)。

写新术语的规矩：先在对应 context 的表里加词条，**再**在用到它的正文里换用新词；
已经写错的地方不要顺手改，先在 `## Flagged ambiguities` 里记下历史裁定。
