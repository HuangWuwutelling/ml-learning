# 公众号发文计划

## 目标

转行 AI 工程师（**AI/LLM 应用工程方向**），目标薪资 ~2 万，广州。边工作边准备，6 个月周期。

主轴：**3 个能上线、能评估、能讲清技术决策的项目**，公众号文章是项目证据的放大器，不再是独立生产目标。**2026-08-04 重排**：env-rag / env-agent 退出旗舰（技术方法论迁移到新项目），新旗舰为 **fastapi-rag**。

- **fastapi-rag**（新主旗舰，2026-08-04 起）：FastAPI 仓库双源 RAG（代码 AST-aware chunk + 官方文档 Markdown chunk → Qdrant），Hybrid/Rerank 检索、RAGAS 4 指标 + **AST-ground-truth 自动核验**（API 引用题）、Langfuse trace、Prompt 注入防护、Docker Compose 一键部署、Gradio UI。技术栈复用 env-rag 已沉淀能力，差异化在「代码 RAG」场景。
- **gb15618**（行业案例旗舰，保留）：GB 15618-2018 农用地评价工具，**当前形态为「Python + PyInstaller 本地 exe」**（批量化、便捷化的环境从业者场景，三种分发形态：Python 包 + GUI + exe），微信小程序版本代码保留、主题待定。**Python 实现已迁至独立仓库** `github.com/HuangWuwutelling/gb15618`（`projects/gb15618/` 仅留跳转 README）：4 模块（limits / evaluator / excel_io / cli）+ 101 测试全绿，`v0.1.0` GitHub Release 已发布 `gb15618.exe`。
- **env-rag / env-agent**（降级为知识点库，2026-08-04）：旧项目代码保留在 `环境法律法规智能问答系统/` 与 `projects/env_agent/`，**不再维护、不进面试稿、不作为旗舰叙事**；Hybrid+Rerank、RAGAS、Langfuse trace、工具校验等方法论迁移到 fastapi-rag 复用。

差异化定位：会做 LLM/AI 应用，同时理解真实行业数据、法规和工作流程（环境工程背景），且能在「非环境行业」场景快速复制落地。

## 核心原则（项目优先）

1. **项目优先**：先做能运行、能评估、能部署的项目，再从项目产出文章。
2. **三个项目 = 求职叙事**（2026-08-04 起）：**fastapi-rag**（技术深度，新主旗舰）+ **gb15618**（行业案例，行业深度）+ **env-rag/env-agent 旧项目**（仅作知识点库，不进面试稿，不进 30 秒主叙事）。
3. **文章必须先过 4 个问题**（少于 3 个 → 不写）：
   - 来自真实运行项目？
   - 增加 AI/LLM 应用工程师核心能力？
   - 能产生可展示的指标 / 截图 / 测试 / 故障记录？
   - 值得在面试中讲 5 分钟？
4. **暂停未连接到旗舰项目的扩写**：新选题先问"它属于哪个项目"，无所属则不进 plan.md。env-rag / env-agent 已降级，新文章不再挂这两个项目。

## 6 周路线（2026-08-04 → 2026-09-15）

> **2026-08-04 重排**：env-rag / env-agent 退出旗舰，**fastapi-rag** 接位。下文路线从 W1 起完全重排。
>
> **env-rag 阶段已沉淀的可复用能力**（不再独立演进，作为 fastapi-rag 的起点）：
> - 30 题 + ChromaDB（baseline_v2）：faithfulness 0.802 / answer_relevancy 0.780 / context_precision 0.641 / context_recall 0.800 — **方法论可迁移，数据不可迁移**（评估集要重建）
> - Hybrid+Rerank 工程经验（#13 文章）
> - Langfuse docker compose 部署卡 NextAuth 阻塞（待解，W1 必清）

| 周 | 主任务 | 公众号 |
|---|--------|----------|
| W1 | **Langfuse NextAuth 阻塞解决**（`restart langfuse-web` 续接）→ FastAPI 仓库 clone（`fastapi/fastapi` 官方仓库，含 `docs/en/docs/` 文档）→ AST-aware chunk 脚本（按 class/function/method 三级切分，保留 docstring + signature + decorators + body）→ Qdrant 双源索引（代码 + 文档同 collection，metadata `source_type`）→ baseline RAGAS 30 题评估 | — |
| W2 | Hybrid 检索（BM25 + dense 双路融合）→ Cross-Encoder rerank → **AST-ground-truth 评估集 v1**（API 引用题机器核验 ≥50 题，分 3 类：API 引用 / 用法示例 / 概念对比）→ RAGAS 复测 | **#15**《Hybrid+Rerank 在 FastAPI 文档问答上的复测》（context_recall 数字对比） |
| W3 | Langfuse trace 接入 fastapi-rag（解决阻塞后可观测）→ Gradio 演示 UI（参考 env-rag UI）→ Docker Compose 一键部署（FastAPI + Qdrant + Langfuse + Nginx） | **#16**《FastAPI-RAG 的可观测与一键部署》（Langfuse trace UI + Docker Compose 复用工程 #04） |
| W4 | 评估集扩充到 ≥80 题（增加代码引用题、跨文件概念对比题）→ Prompt 注入防护（7 攻击 + 7 防线，方法论从 env-rag 沉淀复用）→ 错误案例分析（bad case 归类） | **#17**《RAG 评估集设计：AST 自动核验 80 题》（讲评估集设计 + 机器核验落地） |
| W5 | README 重写（30 秒内讲清「我能做什么」，首页只突出 fastapi-rag + gb15618）→ 3 套面试讲解稿（fastapi-rag / gb15618 / 旧项目技术沉淀，每套 ≤ 5 分钟）→ 项目打磨 | **#18**《代码 RAG 的工程取舍：AST chunk vs 文档 chunk》 |
| W6 | 验收 + 缓冲（预留修复、补充文章、复测） | — |

> **2026-08-04 重排说明**：env-rag W2「Qdrant 迁移」原计划已合并到 fastapi-rag W1（Qdrant 直接成为新项目栈）。env-agent W4「工具校验」方法论沉淀到 fastapi-rag W4「Prompt 注入防护」（校验对象从 tool call 改成 user query）。#15-#18 文章标题与项目归属全部改为 fastapi-rag。

**评估基线状态**（2026-08-02 复跑，env-rag 旧基线，方法论可迁移）：
- 23 题 + ChromaDB：faithfulness 0.730 / context_recall 0.300（**与 #12 文章数据可比**）
- 30 题 + ChromaDB（baseline_v2）：faithfulness 0.802 / context_recall 0.800（**新基线方法论参考**）
- fastapi-rag W1 末需重建 30 题 FastAPI 评估集作新基线

设计稿：`plan.md` 即设计稿与路线图（CLAUDE.md 规定 plan.md 为单一事实源）

## 当前文章清单（按目录分类，2026-07-31）

### 算法线 (`articles/ml/`)
| # | 文章 | 项目归属 | 状态 |
|---|------|----------|------|
| 00 | ML 算法选型指南 + ML Playground 介绍 | 通用 | ✅ 已发 |
| 01 | 线性回归 | 通用 | ✅ 已发 |
| 02 | 岭回归与 Lasso | 通用 | ✅ 已发 |
| 03 | 逻辑回归 | 通用 | ✅ 已发 |
| 04 | 决策树 CART | 通用 | ✅ 已发 |
| 05 | 随机森林 | 通用 | ✅ 已发 |
| 06 | GBDT / XGBoost | 通用 | ✅ 已发 |
| 07 | K-Means 聚类 | 通用 | ✅ 已发 |
| 08 | DBSCAN 密度聚类 | 通用 | ✅ 已发 |
| 09 | SVM | 通用 | ✅ 已发 |
| 10 | PCA 降维 | 通用 | ✅ 已发 |
| 11 | MLP 神经网络 | 通用 | ✅ 已发 |
| 12 | CNN 卷积神经网络 | 通用 | ✅ 已发 |
| 13 | RNN 与 LSTM | 通用 | ✅ 已发 |
| 14 | Word2Vec 词向量 | 通用 | ✅ 已发 |
| 15 | Transformer (Attention) | 通用 | ✅ 已发 |
| 16 | AutoEncoder 自编码器 | 通用 | ✅ 已发 |
| 17 | kNN 近邻分类 | 通用 | ✅ 已发 |
| 18 | 朴素贝叶斯：基于概率的简单分类器（Naive Bayes） | — | 暂停 |
| 19 | KNN 回归：k 近邻的回归版本（KNN Regression） | — | 暂停 |
| 20 | 集成学习进阶：Stacking 与 Blending（Stacking, Blending） | — | 暂停 |
| 21 | 异常检测：Isolation Forest 与 LOF（Anomaly Detection） | — | 暂停 |
| 22 | t-SNE：高维数据可视化（t-SNE） | — | 暂停 |

### 深度学习框架线 (`articles/framework/`)

定位：算法线讲 numpy 从零实现。这条线原计划讲 PyTorch——生产环境的默认框架。算法线讲"为什么这么做"，框架线讲"框架替你做了什么"。

**整张表按方案 A 合并为 1 篇 PyTorch 实战**（挂在 fastapi-rag 下作为辅助，2026-08-04 起），不再单设系列。逐条选题已暂停。

| # | 文章 | 对应算法线 | 项目归属 | 状态 |
|---|------|-----------|----------|------|
| 01 | PyTorch tensor 与 autograd：从 numpy 到自动求值 | — | fastapi-rag | 暂停（合并为 1 篇 PyTorch 实战） |
| 02 | nn.Module 与训练循环：用 PyTorch 重写 MLP | MLP (#11) | fastapi-rag | 暂停（同上） |
| 03 | 卷积神经网络实战：PyTorch 训练 CNN | CNN (#12) | fastapi-rag | 暂停（同上） |
| 04 | RNN/LSTM 文本生成：PyTorch 版 | RNN (#13) | fastapi-rag | 暂停（同上） |
| 05 | Transformer 训练：PyTorch 实现小型 Decoder | Transformer (#15) | fastapi-rag | 暂停（同上） |
| 06 | 微调预训练模型：distilbert + 小数据集 | LoRA (#07 LLM) | fastapi-rag | 暂停（同上） |

### LLM 工具链线 (`articles/llm/`)
| # | 文章 | 涉及概念 | 项目归属 | 状态 |
|---|------|---------|----------|------|
| 01 | AI Agent 入门 | Agent, Tool Calling | 通用 | ✅ 已发 |
| 02 | RAG 实战：环境法典智能问答 | RAG, ChromaDB, DeepSeek | env-rag | ✅ 已发 |
| 03 | LLM Wiki：用 AI 构建知识库 | LLM Wiki, YoudaoNote | 通用 | ✅ 已发 |
| 04 | ML 入门 | ML 基础概念 | 通用 | ✅ 已发 |
| 05 | 你写的 Prompt 为什么不 work？5 个反模式自查 | Prompt Engineering | 通用 | ✅ 已发 |
| 06 | 从 Chain 到 Graph：一个环境申报 Agent 怎么把流程画成图 | LangChain, LangGraph, Tracing, env_agent | env-agent | ✅ 已发 |
| 07 | LoRA 微调：低成本微调开源模型 | LoRA/QLoRA, PEFT, Qwen2.5-0.5B | 通用 | ✅ 已发 |
| 08 | 向量数据库：不只是 RAG | Vector DB, Embedding, BGE, ChromaDB | env-rag | ✅ 已发 |
| 09 | 我给 AI 请了个环保顾问（LangGraph 构建排污许可申报 Agent） | Agent + RAG + Tools + Gradio | env-agent | ✅ 已发 |
| 10 | 让 AI 学会"一次只问一个问题"（System Prompt 中的决策状态机） | Prompt Engineering, System Prompt | env-agent | ✅ 已发 |
| 11 | 把法规喂给 AI（从 HTML 到向量检索的全链路实现） | RAG, ChromaDB, BGE | env-rag | ✅ 已发 |
| — | ~~开源许可证入门与实战（从 pip install 说起）~~ | ~~Open Source License, Compliance, SBOM~~ | — | ❌ 已砍（2026-07-18：主题偏离主线，与 LLM 工程师核心痛点弱相关） |
| 12 | RAG 评估实战（RAGAS） | RAG Evaluation | env-rag | ✅ 已发 |
| 13 | 向量数据库进阶：Hybrid+Rerank 让法典问答 context_recall 从 0.35 推到 0.40 | RRF, Cross-Encoder, HNSW 调优 | env-rag | ✅ 已发 |
| 14 | MCP 协议：统一 LLM 工具调用的标准接口 | MCP, JSON-RPC 2.0, stdio / HTTP+SSE | 通用 | ✅ 已发 |
| 15 | Hybrid+Rerank 在 FastAPI 文档问答上的复测 | Hybrid, Rerank, RAGAS | fastapi-rag | 📝 待发（W2，FastAPI 场景的 RAGAS 数字对比） |
| 16 | FastAPI-RAG 的可观测与一键部署 | Langfuse, Trace, Docker Compose | fastapi-rag | 📝 待发（W3，trace UI + 部署复用工程 #04） |
| 17 | RAG 评估集设计：AST 自动核验 80 题 | AST, 评估集设计, RAGAS | fastapi-rag | 📝 待发（W4，讲评估集设计 + 机器核验落地） |
| 18 | 代码 RAG 的工程取舍：AST chunk vs 文档 chunk | AST chunk, 双源融合 | fastapi-rag | 📝 待发（W5，代码 RAG 特有的工程决策） |
| — | ~~vLLM 入门：模型推理加速与部署~~ | ~~vLLM~~ | — | ❌ 已砍（2026-07-26：纯二手资料编译，无本地一手实践支撑，与 LLM 线其他文章的"项目驱动"风格不符） |
| 19 | Dify vs Coze：低代码搭建 AI 应用 | Dify, Coze | — | 暂停（原 #16 顺延为 #19） |

### 环境工程线 (`articles/env/`)
| # | 文章 | 项目归属 | 状态 |
|---|------|----------|------|
| 01 | 河流底泥镉污染分布 | 通用 | ✅ 已发 |
| 02 | 大气镉沉降模拟 | 通用 | ✅ 已发 |
| 03 | 洪水底泥镉农田输入 | 通用 | ✅ 已发 |
| 04 | 室内甲醛通风模型 | 通用 | ✅ 已发 |
| 05 | 废石清理后底泥镉去哪了 | 通用 | ✅ 已发 |
| 06 | 杜邦 C-8 污染案：科学如何论证工厂与健康的因果链 | 通用 | ✅ 已发 |
| 07 | 科学能排除因果吗？泡花碱厂调查的解读（C8 姊妹篇）| 通用 | ✅ 已发 |
| 08 | 电镀厂酸雾：从工艺产污到大气扩散与沉降 | 通用 | ✅ 已发 |
| 09 | 电镀厂铬（Cr(VI)）：大气沉降与健康风险 | 通用 | ✅ 已发 |
| 10 | 甲酰胺是什么，它可能从哪里来 | 通用 | ✅ 已发 |
| 11 | 邻苯二甲酸酯：用了八十年的增塑剂，二十年监管路 | 通用 | ✅ 已发 |
| 12 | 微塑料：除了食物，外卖盒还给你加了什么料 | 通用 | ✅ 已发 |
| 13 | 从 PFOA 到 GenX：PFAS 家族为什么禁不完 | 通用 | ✅ 已发 |
| 14 | 一块农用地到底算不算污染？GB 15618-2018 的判定逻辑 | gb15618 | ✅ 已发（2026-08-03） |
| 15 | GB 15618 自动化评价工具：不用装 Python，exe 双击就能跑 | gb15618 | ✅ 已发（2026-08-03；标题从「三种分发形态：库 + GUI + exe」改为现版，对非技术读者更友好） |
| 16 | 感冒等病毒传染病传播模型：SEIR 与 R0 | 通用 | 📝 草稿 |
| 17 | 分布式光伏对配电网的影响：4 种渗透率 | 通用 | 📝 草稿 |
| — | ~~数据不出本机：用 Python + PyInstaller 把 GB 15618 评价做成 exe~~ | — | ❌ 已合并到 env/15（2026-08-02：env/17 复活后与 env/15 主题重复，合并保留 env/15） |
| 18 | 三氯乙烯/四氯乙烯：地下水看不见的羽流 | 通用 | ✅ 已发 |
| 19 | 西电东输：UHVDC 物理 | 通用 | 📝 草稿 |
| 20 | POPs 远距离传输：5 纬度带 box model | 通用 | 📝 草稿 |
| 21 | 一杯白酒 24 小时：酒精在你血液里怎么消失的 | 通用 | 📝 草稿 |

### 项目工程线 (`articles/engineering/`)
| # | 文章 | 内容 | 项目归属 | 状态 |
|---|------|------|----------|------|
| 01 | FastAPI：为什么选它 | FastAPI 对比 Flask/Django，Pydantic 校验，错误处理，异步场景 | 通用 | ✅ 已发 |
| 02 | Linux 服务器部署：从 SSH 到 systemd | SSH 免密 + 传代码 → apt + venv + pip → nohup → systemd → journalctl 排查 | 通用 | ✅ 已发 |
| 03 | Docker 容器化：一次构建，到处运行 | Dockerfile → build/run → 镜像传输（save/load 或仓库），含与手动部署对比 | env-rag | ✅ 已发（env-rag 部署复用） |
| 04 | Docker Compose：多服务编排实战 | ML Playground + PostgreSQL + Nginx 三服务编排；网络/卷/env/healthcheck 5 关键概念；生产 7 条注意事项；附完整 `docker-compose.yml` + `nginx.conf` | env-rag | ✅ 已发（env-rag 部署复用） |
| — | ~~LLM_Text_to_SQL~~ | ~~从自然语言到数据库查询~~ | — | ❌ 已砍（2026-07-23：naive 版 prompt 策略全网饱和，安全/生产化角度并入 fastapi-rag 项目线，作为项目产出的文章） |
| — | ~~Langfuse 本地复现 + 5 trace 实测~~ | ~~复现 `langfuse/langfuse`（docker compose 部署）→ 接入 fastapi-rag 捕获 trace，作为 fastapi-rag 主旗舰的可观测能力~~ | fastapi-rag | ✅ 已并入 fastapi-rag W1-W3（解决 NextAuth 阻塞后接入） |
| — | ~~Qdrant 本地复现 + ChromaDB RAGAS 对比~~ | ~~复现 `qdrant/qdrant`（单二进制部署）→ 同数据集换库对比 RAGAS 指标~~ | fastapi-rag | ✅ 已并入 fastapi-rag W1（Qdrant 直接作为新项目栈） |

### AI 发展史线 (`articles/ai-history/`)
| # | 文章 | 项目归属 | 状态 |
|---|------|----------|------|
| 00 | WALL·E 的学习曲线——从拾荒机器人到 AI 笔记 | 通用 | ✅ 已发 |
| 01 | AI 70 年：从图灵到大模型时代 | 通用 | ✅ 已发 |
| 02 | AI 三起两落：同一个剧本，三个变量 | 通用 | ✅ 已发 |
| 03 | 当 AI 走出科技公司：ChatGPT 与 DeepSeek 的启示 | 通用 | ✅ 已发 |
| 04 | 从词向量到大模型：NLP 进化路线图 | 通用 | ✅ 已发 |
| 05 | 一场计算机视觉的革命：从 28% 到 2% | 通用 | ✅ 已发 |
| 06 | 深度学习三巨头：Hinton、LeCun、Bengio | 通用 | ✅ 已发 |
| 07 | AlphaGo → AlphaFold：AI 改变科学的两次证明 | 通用 | ✅ 已发 |
| 08 | Hassabis 传：从国际象棋神童到诺贝尔化学奖 | 通用 | ✅ 已发 |
| 09 | Token：LLM 的最小单元 | 通用 | ✅ 已发 |
| 10 | RLHF：从人类反馈中学习 | 通用 | ✅ 已发 |
| 11 | Scaling Law：越大越好？ | 通用 | ✅ 已发 |

## 暂停清单（不连接到旗舰项目则不进 plan.md）

| 来源系列 | 暂停选题 | 状态原因 |
|----------|----------|----------|
| articles/llm/ | 16 Dify vs Coze | 二手资料；项目驱动风格不匹配 |
| articles/framework/ | 6 篇 PyTorch 教程（原 01-06） | 合并为 1 篇 PyTorch 实战 |
| articles/ml/ | 18 朴素贝叶斯 / 19 KNN 回归 / 20 Stacking / 21 异常检测 / 22 t-SNE | 不在旗舰项目路径上 |
| articles/env/ | 17 PyInstaller exe 版 | ❌ 已合并到 env/15（2026-08-02：env/17 与 env/15 主题重复，合并保留 env/15） |
| articles/env/ | 19 MTBE/BTEX | 科普类，不在项目路径上 |
| projects/gb15618-miniapp（路径） | 微信云开发小程序版本 | 暂停发布新文章，主题待定；代码保留在 `projects/gb15618-miniapp/miniprogram/`，作为「行业案例」备用素材（路径 `-miniapp` 后缀为历史原因保留） |
| articles/ai-history/ | 本周期停止扩写 | 已发 12 篇作公众号日常内容缓冲，不占主线 |
| **环境法律法规智能问答系统/**（env-rag，路径） | **降级为知识点库**（2026-08-04） | **代码保留**（RAG 工程资产 + 文章 #02/#08/#11/#12/#13 的实践记录）；**不再维护**、**不进面试稿**、**不作为旗舰叙事**。Hybrid/Rerank、RAGAS、Langfuse 方法论迁移到 fastapi-rag |
| **projects/env_agent/**（env-agent，路径） | **降级为知识点库**（2026-08-04） | **代码保留**（LangGraph Agent 工程资产 + 文章 #06/#09/#10 的实践记录）；**不再维护**、**不进面试稿**、**不作为旗舰叙事**。工具校验方法论沉淀到 fastapi-rag W4 Prompt 注入防护 |

## 求职入口

第 5 周同步完成（见上方 6 周路线 W5）：

- `README.md` 重写：30 秒内讲清「我能做什么」，首页只突出 **fastapi-rag** + **gb15618** 两个项目（旧项目降级不进入主叙事）
- 3 套面试讲解稿，每套 ≤ 5 分钟，存到 `docs/interview-prep/`：
  1. fastapi-rag（主，5 分钟技术深度）
  2. gb15618（行业案例，5 分钟行业理解）
  3. env-rag / env-agent 技术沉淀（可选，3-5 分钟方法论迁移）
- 移除 `simple_agent.py`、`app_text_to_sql.py` 等过期项目描述

## 验收清单（6 周末检查）

- [ ] plan.md 头部有「目标 + 核心原则 + 6 周路线」
- [ ] 所有系列表都带「项目归属」列
- [ ] 末尾有「暂停清单」与「求职入口」段
- [ ] **fastapi-rag 主旗舰**：双源索引（代码 AST chunk + 文档 Markdown chunk） + Hybrid+Rerank + 评估集 ≥80 题（其中 AST-ground-truth 自动核验 ≥50 题） + RAGAS 4 指标 + Langfuse trace（NextAuth 阻塞已解） + Docker Compose 一键部署 + Prompt 注入防护（7 攻击 + 7 防线）
- [x] gb15618（PyInstaller 打包）已发布（v0.1.0 Release，`projects/gb15618/` 源码迁至独立仓库 `HuangWuwutelling/gb15618`） + env/14 + env/15 已发（env/16 不写）
- [ ] env-rag / env-agent 旧项目代码保留 + 标注「降级为知识点库」+ 不进面试稿
- [ ] 3 套面试讲解稿齐备（fastapi-rag + gb15618 + 旧项目技术沉淀可选）

