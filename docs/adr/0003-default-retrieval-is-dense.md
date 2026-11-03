# ADR-0003 · RAG 默认检索模式保持 dense

- 状态: accepted
- 登记日期: 2026-11-01

## 约束

`环境法律法规智能问答系统/` 有三档检索：`dense`（BGE 向量 TOP-K）、`hybrid`
（向量 + BM25 各 50 条，RRF k=60）、`hybrid_rerank`（融合结果再经 bge-reranker-v2-m3 精排）。
精排在本机 8 核 CPU 上每对约 0.47 s（batch=32），整条查询实测 285 s。

## 裁定

**默认检索模式保持 `dense`，不改。** `hybrid_rerank` 只作为可选模式存在，
切过去之前必须先读子项目 `CLAUDE.md` 的「数据流」节，确认能接受这个延迟。

## 后果

默认路径的响应延迟可控，演示和自测都跑得起来。代价是精排带来的召回收益在本机
演示不出来，写文章或做简历说明时要注明「本机 CPU 条件」，不能把 285 s 说成嵌入耗时。
术语对应 [GLOSSARY-ai-application.md](../../GLOSSARY-ai-application.md) 的
「hybrid_rerank（精排）」。
