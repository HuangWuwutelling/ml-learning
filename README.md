# ML Learning

机器学习 & 深度学习算法学习项目 + LLM 工程作品集。

18 个 numpy 手写 ML 算法 + 14 个环境模型 + 60+ 篇科普文章（AI 史 / 算法 / LLM 工程 / 工程 / 环境 / 因果推断），每个模型都有对应文章与可复现代码。

> 项目主旗舰 + 求职叙事：见 [_local/plan.md](_local/plan.md)（gitignored）。
>
> **当前主旗舰**：fastapi-rag（代码仓库双源 RAG，文章 #15-#19 已内部定稿，待真实发布到公众号）。项目代码在 `projects/fastapi-rag/`，本 README 在文章未真实发布前不收录该项目。

## 项目结构

```
├── models/              # 18 个手写算法 + 环境模型
├── notebooks/           # 训练 & 可视化 Jupyter notebook
├── projects/
│   ├── ml_playground/   # FastAPI + Gradio 统一平台
│   ├── fastapi-rag/     # 主旗舰（文章未真实发布，README 暂不收录）
│   ├── wali_cmd/        # 微信小程序（本地仓库）
│   └── gb15618/         # 行业案例（源码已迁独立仓库）
├── 环境法律法规智能问答系统/   # 旧 RAG 项目（降级为知识点库）
├── articles/            # 学习记录（独立 git 仓库）
├── scripts/             # 封面图 / notebook 生成脚本（按系列子目录）
├── data/                # 数据集
├── 环保类知识库LLM Wiki/      # YoudaoNote LLM Wiki
├── _local/              # 发文计划 + 求职叙事（gitignored）
├── requirements.txt
└── .gitignore
```

## 文章系列

### AI 发展史线 (`articles/ai-history/`)

千字科普短文，不涉及代码。

| # | 文章 | 说明 |
|---|------|------|
| 00 | **WALL·E 的学习曲线**——从拾荒机器人到 AI 笔记 | 用 WALL·E 的进化弧线引出 AI 发展的主线 |
| 01 | **AI 70 年：从图灵到大模型时代** | 一张时间线串起 11 个关键节点 |
| 02 | **AI 三起两落：同一个剧本，三个变量** | 三次热潮的重复模式，以及三个改变剧本的变量 |
| 03 | 当 AI 走出科技公司：ChatGPT 与 DeepSeek 的启示 | 普及的两个层级：交互 + 成本 |
| 04 | 从词向量到大模型：NLP 进化路线图 | One-hot → Word2Vec → RNN → Transformer → BERT/GPT |
| 05 | 从 28% 到 2%：一场计算机视觉的革命 | LeNet → AlexNet → VGG/ResNet → ViT → 多模态；ImageNet 错误率从 28% 跌到 2% |
| 06 | **深度学习三巨头的三十年**：Hinton、LeCun、Bengio 的坚持与分野 | 2018 图灵奖 + 2024 诺奖；30 年寒冬坚持 |
| 07 | AlphaGo → AlphaFold：AI 改变科学的两次证明 | 1997 深蓝"算"出胜利、2024 诺奖"发现"科学 |
| 08 | **Hassabis 传：从国际象棋神童到诺贝尔化学奖** | 4 岁学棋 → 创办 DeepMind → AlphaGo → AlphaFold → 2024 诺奖 |
| 09 | **Token：LLM 的最小单元** | 从字符到 BPE：LLM 看到了什么、读懂了什么 |
| 10 | **RLHF 的 5 年：1.3B 模型怎么打败 175B** | SFT → Reward Model → PPO 三阶段 |
| 11 | **Scaling Law 走到头：越大≠越聪明** | 从 Kaplan 到 Chinchilla，三面墙堵住 scaling |

### 算法线 (`articles/ml/`) — 已实现算法

从 numpy 手写到深度学习，每个算法包含原理推导与代码实现。

| # | 算法 | 模型文件 |
|---|------|----------|
| 00 | ML 算法选型指南 + ML Playground 介绍 | — |
| 01 | 线性回归（单变量 → 多变量） | `models/linear_regression.py` |
| 02 | 岭回归与 Lasso（L1/L2 正则化） | `models/ridge_regression.py` / `models/lasso_regression.py` |
| 03 | 逻辑回归（二分类） | `models/logistic_regression.py` |
| 04 | 决策树（CART 分类树） | `models/decision_tree.py` |
| 05 | 随机森林（Bagging + 随机特征） | `models/random_forest.py` |
| 06 | GBDT（梯度提升，串行回归树） | `models/gradient_boosting.py` |
| 07 | K-Means（Lloyd 算法） | `models/kmeans.py` |
| 08 | DBSCAN（密度聚类） | `models/dbscan.py` |
| 09 | SVM（SMO + 核技巧） | `models/svm.py` |
| 10 | PCA（主成分分析，SVD 分解） | `models/pca.py` |
| 11 | MLP（多层感知机，反向传播） | `models/mlp.py` |
| 12 | CNN（卷积神经网络，im2col） | `models/cnn.py` |
| 13 | RNN / LSTM（循环神经网络，BPTT） | `models/rnn.py` |
| 14 | Word2Vec（Skip-gram + Negative Sampling） | `models/word2vec.py` |
| 15 | Transformer（Decoder-only，自注意力） | `models/transformer.py` |
| 16 | AutoEncoder（编码器-解码器，无监督降维） | `models/autoencoder.py` |
| 17 | kNN（k 近邻分类，懒惰学习） | `models/knn.py` |
| 18 | 倾向得分匹配（PSM, Propensity Score Matching） | `models/propensity_score_matching.py` |

### LLM 工具链线 (`articles/llm/`)

RAG、AI Agent、Prompt Engineering、Fine-tuning 等 LLM 工程实践。

| 文章 | 涉及概念 |
|------|---------|
| AI Agent 入门 | Agent, Tool Calling |
| RAG 实战：环境法典智能问答 | RAG, ChromaDB, DeepSeek |
| LLM Wiki：用 AI 构建知识库 | LLM Wiki, YoudaoNote |
| ML 入门 | ML 基础概念 |
| 你写的 Prompt 为什么不 work？5 个反模式自查 | Prompt Engineering |
| 从 Chain 到 Graph：一个环境申报 Agent 怎么把流程画成图 | LangChain, LangGraph, Tracing, env_agent |
| LoRA 微调：用 4GB 显卡微调大模型 | LoRA/QLoRA, PEFT, Qwen2.5-0.5B |
| 向量数据库：不只是 RAG 的存储 | Vector DB, Embedding, BGE, ChromaDB |
| 我给 AI 请了个环保顾问（LangGraph 构建排污许可申报 Agent） | Agent + RAG + Tools + Gradio |
| 让 AI 学会"一次只问一个问题"（System Prompt 中的决策状态机） | Prompt Engineering, System Prompt |
| 把法规喂给 AI（从 HTML 到向量检索的全链路实现） | RAG, ChromaDB, BGE |
| RAG 评估实战（RAGAS） | RAG Evaluation, RAGAS |
| 向量数据库进阶：Hybrid+Rerank 让法典问答 context_recall 从 0.35 推到 0.40 | Hybrid Search, BM25, RRF, Cross-Encoder, HNSW |
| MCP 协议：统一 LLM 工具调用的标准接口 | MCP, JSON-RPC 2.0, stdio / HTTP+SSE |

### 项目工程线 (`articles/engineering/`)

从项目实战中总结的工程经验。

| # | 文章 |
|---|------|
| 01 | FastAPI 入门（以 ML Playground 为例） |
| 02 | Linux 服务器部署：从 SSH 到 systemd |
| 03 | Docker 容器化：一次构建，到处运行 |
| 04 | Docker Compose：多服务编排实战 |
| 05 | 一个人用 vibe coding 做小程序：步骤与架构 |
| 06 | 139 条数据的小程序搜索，真的需要向量数据库吗 |

### 环境工程线 (`articles/env/`)

利用环境工程专业背景 + 编程能力，展示跨领域建模与分析。

| # | 文章 | 模型文件 |
|---|------|----------|
| 01 | 河流底泥镉污染分布 | `models/river_sediment_cd.py` |
| 02 | 大气镉沉降模拟 | `models/atmo_cd_deposition.py` |
| 03 | 洪水底泥镉农田输入 | `models/floodplain_cd_deposition.py` |
| 04 | 室内甲醛通风模型 | `models/indoor_formaldehyde.py` |
| 05 | 废石清理后底泥镉去哪了 | `models/floodplain_recovery.py` |
| 06 | 杜邦 C-8 污染案：科学如何论证工厂与健康的因果链 | — |
| 07 | 科学能排除因果吗？泡花碱厂调查的解读（C8 姊妹篇） | — |
| 08 | 电镀厂酸雾：从工艺产污到大气扩散与沉降 | `models/electroplating_acid_mist.py` |
| 09 | 电镀厂铬（Cr(VI)）：大气沉降与健康风险 | `models/electroplating_cr.py` |
| 10 | 甲酰胺是什么，它可能从哪里来 | — |
| 11 | 邻苯二甲酸酯：用了八十年的增塑剂，二十年监管路 | — |
| 12 | 微塑料：除了食物，外卖盒还给你加了什么料 | — |
| 13 | 从 PFOA 到 GenX：PFAS 家族为什么禁不完 | — |
| 14 | 一块农用地到底算不算污染？GB 15618-2018 的判定逻辑 | — |
| 15 | GB 15618 自动化评价工具：不用装 Python，exe 双击就能跑 | — |
| 16 | 麻疹为什么必须打疫苗，普通感冒不用：SEIR 与 R0（已发 2026-08-07） | `models/seir.py` |
| 17 | 屋顶光伏装多少，末端电压会越限？（已发 2026-08-08） | `models/pv_distribution.py` |
| 18 | 三氯乙烯/四氯乙烯：地下水看不见的羽流（已发） | `models/groundwater_tce_pce.py` |
| 19 | 为什么西电东送，必须升到 ±1100 kV 直流？（已发 2026-08-10） | `models/uhvdc.py` |
| 20 | 从没在极地用过，POPs 是怎么到的北极？（已发 2026-08-17） | `models/pops_lrt.py` |
| 21 | 半衰期：为什么布洛芬 4-6 小时吃一次，而不是 24 小时（已发 2026-08-15） | `models/ibuprofen_pk.py` |
| 22 | 同一罐奶粉，为什么冲出来不一样？一个方程讲清溶解的原理（已发 2026-08-16） | `models/milk_powder.py` |

> 另有图件脚本：`models/multi_metal_comparison.py`、`models/multi_metal_spatial.py`（多金属迁移对比与空间分布图）。

### 因果推断线 (`articles/causal/`)

经典论文配实际数据，每篇从零跑通一个因果推断方法。文章讲思路和结果，完整代码放 GitHub。

| # | 文章 | 涉及概念 |
|---|------|---------|
| 00 | 相关不等于因果：怎么从数据里找到因果关系？（已发 2026-08-23） | 因果推断概念、Pearl 因果阶梯、confounder |
| 01 | 推荐 v2 上线，业务组说 GMV 涨了 30%，这是 v2 带来的吗？（已发 2026-08-25） | PSM 倾向得分匹配、logistic 倾向得分、NN k=4 + 卡尺（0.2×PS std）、SMD 平衡性检验、朴素对比 vs PSM、Rosenbaum & Rubin 1983 / Austin 2011 / Stuart 2010 |
| 02 | 涨最低工资反而不裁员？DID 怎么算出 +2.75 FTE（已发 2026-08-27） | DID 双重差分、平行趋势假设、2x2 表、ATT、Card & Krueger 1994、Bertrand et al. 2004、Neumark & Wascher 2000 |
| 03 | 只差高考 1 分：一本线背后，断点回归如何识别精英大学入学的因果效应（已发 2026-09-02） | RDD 断点回归、running variable=分数差、cutoff c=0、连续性假设、局部线性回归、带宽 ±20 分、LATE at cutoff、placebo、density test、Ruixue Jia & Hongbin Li *JPubE* 2021（5.2%-9.7% 起薪溢价 / IV 28.3%-45.6% / 信号假说）、Lee & Lemieux 2010、Imbens & Kalyanaraman 2012、McCrary 2008 |
| 06 | 涨最低工资，出口复杂度反而升了？因果推断告诉你为什么（已发 2026-08-30） | DID 双重差分、企业出口复杂度（export sophistication）、低复杂度产品退出机制、异质性处理效应、Li, Peng, Huang & Zhou 2022；对照文献 Jia 2014、Card & Krueger 1994 |

> **关于 02**：causal 系列里 4 个 notebook 中唯一完全 self-contained 的——Card & Krueger 1994 Table 2 的 4 行均值数据直接内联进 `notebooks/causal_02_DID.ipynb` 的 cell-1，单 notebook 即可跑通。其他 3 篇（01 PSM / 04 SCM / 05 DAG）依赖真实数据集，需要 `articles/causal/data/` 配套；03 RDD 为纯概念文，无 notebook、无数据依赖。

## 项目

| 项目 | 描述 | 状态 |
|------|------|------|
| **ML Playground** | 18 个手写算法的 FastAPI + Gradio 统一演示平台 | 演示 |
| **GB 15618 评价工具** | 农用地土壤污染风险评价，库 + GUI + exe 三种分发 | 行业案例 |
| **瓦力命令行速查** | 微信小程序，Linux/Windows 命令速查（139 条），含语法/示例/说明/类目浏览 | 副线 |
| 环境法规智能问答（旧） | ChromaDB + DeepSeek RAG 知识库（env-rag 旧旗舰，已降级） | 降级 |
| LLM Wiki 知识库 | AI 自动构建的环保知识库（YoudaoNote） | 工具 |

> 主旗舰 **fastapi-rag**（W1-W7 已跑通，代码 + 部署 + RAGAS 评估齐备）暂未收录，待 #15-#19 文章真实发布后再补登。
>
> 降级项目代码保留在 `环境法律法规智能问答系统/` 和 `projects/env_agent/`，不再维护、不进面试稿，方法论沉淀到 fastapi-rag 复用。

## 快速复现

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行 Notebook

```bash
# Day 1-17: 从线性回归到 Transformer
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/dayN_*.ipynb

# 或逐个运行
jupyter notebook notebooks/day1_linear_regression.ipynb
```

### 3. 运行项目

```bash
# ML Playground（演示平台）
uvicorn projects/ml_playground.app:app

# RAG 旧旗舰（降级项目，代码保留）
cd 环境法律法规智能问答系统 && python app.py

# GB 15618 评价工具（库 + GUI）
git clone https://github.com/HuangWuwutelling/gb15618.git
cd gb15618 && pip install -e . && python -m gb15618

# GB 15618 评价工具（Windows exe，免装 Python）
# 从 https://github.com/HuangWuwutelling/gb15618/releases/latest 下载 gb15618.exe，双击运行
```