# GLOSSARY · AI 应用工程

RAG、Agent、微调与评测的术语。数值口径以各项目源码与评测脚本为准。

## Language

**dense 检索（向量检索）**: 只用 BGE 嵌入向量做相似度检索，TOP-K 召回。本仓 RAG 项目的
默认模式。
_Avoid_: `向量库`、`语义检索`（不写 TOP-K 与嵌入模型）

**hybrid 检索（RRF 融合）**: 向量召回 50 条 + BM25 召回 50 条，用 RRF（k=60）融合排序。
_Avoid_: `混合检索`（不写融合方式）

**hybrid_rerank（精排）**: 在 hybrid 结果上再用 bge-reranker-v2-m3 精排。CPU 上每对约 0.47 s
（batch=32），50 条候选十几到二十秒，本机整条查询实测 285 s。**285 s 是精排段耗时，不是嵌入
耗时**，切到这个模式前必须先确认能接受这个延迟。
_Avoid_: `285 秒嵌入`、`慢检索`（不区分是哪一段）

**评测集（eval set）**: 一批带标准答案的题目与参考答案，用来量化检索或生成质量。本仓三套：
env-rag `data/eval/eval_set_v1.jsonl`（30 条，q001-q030，字段 id/query/ground_truth/reference/category）、
env_agent `eval_agent.py` 的 `CASES`（12 条，每条含 want/avoid 判据与 turns）、
lora_finetune `test_set.jsonl`（34 条，字段 text/label）。
_Avoid_: `测试集`、`测试用例`（与工程测试区分）

**want / avoid 判据**: Agent 评测的判据形式。每条 case 写清「必须出现哪些工具或信息」（want）
与「不能出现什么」（avoid），不写精确匹配文本。空数组表示该项无约束。
_Avoid_: `期望输出`、`断言字符串`

**recall 分母**: 参与 recall 计算的题数，不是评测集总数。env-rag 的历史评估跑 23 题，
recall 分母是 20，其中 3 题的标准答案不在语料里，不计入分母。
_Avoid_: `23 题的 recall`（不写分母的召回率不可复现）

**降级**: 停止继续开发、不再新增文章。**不等于**弃用，**不等于**不进简历。三个简历主项目
（RAG / Agent / 微调）自 2026-08-04 起处于降级状态，但仍是简历上的三个主项目。
_Avoid_: `下线`、`废弃`、`弃用`

**QLoRA（4-bit 微调）**: 基座权重以 4-bit 加载（BitsAndBytes），只训练 LoRA 低秩适配器，
按 4 GB 显存设计。`projects/lora_finetune/` 用它做环境违法严重程度识别。
_Avoid_: `LoRA 微调`（不写 4-bit）、`量化微调`

**结构化输出的三种实现**: lora 评测把「让模型吐出可解析结构」拆成三条路：
`predict_prompt_only`（纯 prompt + 解析）、`predict_response_format`（JSON 形式）、
`predict_tool_choice`（工具调用形式）。在 transformers 直推场景下三者都是「prompt + 解析 +
Pydantic 校验」的不同实现；未微调的基座跑同一套构成对照组，微调后的模型才体现训练收益。
_Avoid_: `三个模型`、`zero-shot`

**直推（transformers 本机推理）**: 用 transformers 直接跑 Qwen2.5-0.5B-Instruct，不走 API。
CPU 可跑，但与 OpenAI / Anthropic 的 `response_format` / `tool_choice` 不是同一套机制，
写文章时要说明这层差别。
_Avoid_: `本地部署`、`离线推理`（不写框架与模型）

**预审（pre-review）**: 报告报送前，用规则和模型对照法规与标准逐项核对，输出问题清单。
不等于领域专家的最终审核：P0 问题必须由人签字，工具不自动放行。
_Avoid_: `审核`（指最终审核时）、`自动审查`（暗示无需人工）

**问题清单（issue list）**: 某一份报告的预审产物，每条含章节、页码、原文引用、规则 id、
依据条款、风险等级、修改建议。与「评测集」不同：问题清单是单份报告的产物，评测集是带真值的题集。
_Avoid_: `测试集`、`错误列表`（不带证据指针时）

**规则 id**: 前缀 `S` 结构 / `M` 监测方案 / `D` 数据 / `C` 一致性 / `L` 叙述，加层内编号，
例如 `D02-SOIL-AS-2`。用于把问题归因到具体检查项，面试或复核时可逐条指认。
_Avoid_: `规则编号`（不写层前缀）

**待人工判断（needs human）**: 规则未命中但存在疑点，或 LLM 提出但无法用页码原文证实的项。
不计入通过，也不能被默认忽略。
_Avoid_: `未分类`、`其他`

**证据指针（evidence pointer）**: 页码 + 原文引用 + 表格行。LLM 结论必须能精确回溯到原文，
匹配不上即丢弃；规则结论也要给出命中的字段与位置。
_Avoid_: `出处`（不写页码与原文时）

**P0 / P1 / P2**: 问题风险等级。P0 阻断：评价标准选错、超标漏判、漏点位/漏因子、结论与数据
矛盾；P1 重要：限值数值错、频次不足、检出限高于限值、单位错、附件缺；P2 建议：表述不清、
图表缺页码、建议不具体。P0 一律转人工复核。
_Avoid_: `严重 / 一般 / 轻微`（不写判定口径）

## Relationships

- **dense / hybrid / hybrid_rerank** 是同一条检索链路上的三个档位，不是三个独立系统。
  默认档位是 dense。
- **评测集 → recall / want-avoid 判据**：数据集是载体，口径（分母、判据形式）决定数字怎么读。
- **降级 ≠ 弃用**：状态词只描述开发强度，不描述简历价值。

## Flagged ambiguities

1. **「23 题集」与「30 条文件」的关系**：`eval_set_v1.jsonl` 实际有 30 条（q001-q030）。
   历史评估跑的是其中 23 题，recall 分母只算 20 题（3 题标准答案不在语料里）。三个数字是同一条
   链上不同环节的数，读数字前先确认说的是哪个。
2. **「285 秒」曾被写成检索整体耗时**，实际只是 hybrid_rerank 的精排段。
3. **「召回率」不标分母即不可复现**，引用时必须带分母。
4. **lora 的「三个方法」是三种结构化输出实现**，不是三个模型，也不是三个训练阶段。
5. **Agent 的 want / avoid 判据与 RAG 的 ground truth / reference** 是两套判据形式，
   不要合并成「参考答案」。
