# ML Learning

机器学习 & 深度学习算法学习项目 + LLM 工程作品集。每种算法用 Numpy 从零实现，在真实数据集上实验。

## 项目结构

```
├── models/           # 算法实现（纯 Numpy + 环境模型）
├── notebooks/        # 训练 & 可视化 Jupyter notebook
├── projects/
│   ├── ml_playground/    # FastAPI + Gradio 统一平台
│   ├── env_agent/        # LangGraph 环保申报 Agent
│   ├── app_text_to_sql.py
│   └── simple_agent.py
├── articles/         # 公众号文章（ml/ | llm/ | engineering/ | env/ | ai-history/）
├── scripts/          # Notebook 生成 & 封面图脚本
├── data/             # 数据集
├── 环境法律法规智能问答系统/   # RAG + ChromaDB + DeepSeek
├── 环保类知识库LLM Wiki/      # YoudaoNote LLM Wiki
├── requirements.txt
└── .gitignore
```

## 已实现算法

| Day | 算法 | 模型文件 |
|-----|------|----------|
| 1 | 线性回归（单变量 → 多变量） | `models/linear_regression.py` |
| 2 | Ridge & Lasso（L1/L2 正则化） | `models/ridge_regression.py` / `models/lasso_regression.py` |
| 3 | 逻辑回归（二分类） | `models/logistic_regression.py` |
| 4 | 决策树（CART 分类树） | `models/decision_tree.py` |
| 5 | 随机森林（Bagging + 随机特征） | `models/random_forest.py` |
| 6 | GBDT（梯度提升，串行回归树） | `models/gradient_boosting.py` |
| 7 | K-Means（Lloyd 算法） | `models/kmeans.py` |
| 8 | DBSCAN（密度聚类） | `models/dbscan.py` |
| 9 | SVM（SMO + 核技巧） | `models/svm.py` |
| 10 | PCA（主成分分析，SVD 分解） | `models/pca.py` |
| 11 | MLP（多层感知机，反向传播） | `models/mlp.py` |
| 12 | CNN（卷积神经网络，im2col） | `models/cnn.py` |
| 13 | RNN / LSTM（循环神经网络，BPTT） | `models/rnn.py` |
| 14 | Word2Vec（Skip-gram + Negative Sampling） | `models/word2vec.py` |
| 15 | Transformer（Decoder-only，自注意力） | `models/transformer.py` |
| 16 | AutoEncoder（编码器-解码器，无监督降维） | `models/autoencoder.py` |

## 环境模型

| 模型 | 描述 | 代码 |
|------|------|------|
| 河流底泥 Cd 污染分布 | 悬浮沉积物-污染物耦合模型，模拟 100km 河段 Cd 沿程分布 | `models/river_sediment_cd.py` |
| 大气 Cd 沉降模拟 | 高斯烟羽模型，模拟焚烧厂 Cd 排放对周边农田的长期累积效应 | `models/atmo_cd_deposition.py` |
| 洪水底泥 Cd 农田输入 | 漫滩沉积模型，模拟洪水将河床 Cd 输移至两岸农田 | `models/floodplain_cd_deposition.py` |
| 室内甲醛通风模型 | 箱式模型，模拟通风/活性炭/活性锰对室内甲醛浓度的影响 | `models/indoor_formaldehyde.py` |
| 多金属对比 | Cd, Pb, As 多金属迁移差异对比 | `models/multi_metal_comparison.py` |
| 空间分布 | 变河床条件下的 Cd 空间分布 | `models/multi_metal_spatial.py` |
| 废石清理后底泥 Cd 去向 | 活性层替换模型，追踪废石清理后底泥镉的三个去向（稀释/搬运/封存） | `models/floodplain_recovery.py` |
| 电镀厂酸雾全过程 | 产污→集气→洗涤→高斯烟羽→干湿沉降→土壤酸化，全链条质量平衡与达标分析 | `models/electroplating_acid_mist.py` |
| 电镀厂 Cr(VI) 健康风险 | 同一工厂 Cr(VI) 扩散、土壤累积、吸入/摄入致癌风险评估（US EPA IRIS） | `models/electroplating_cr.py` |

## AI 发展史系列

千字科普短文，不涉及代码，把算法线零散的知识点串成时间线，给读者一个"上帝视角"。

| # | 文章 | 说明 |
|---|------|------|
| 00 | **WALL·E 的学习曲线**——从拾荒机器人到 AI 笔记 | 用 WALL·E 的进化弧线引出 AI 发展的主线 |
| 01 | **AI 70 年：从图灵到大模型时代** | 一张时间线串起 11 个关键节点，搭起整个系列的框架 |
| 02 | **AI 三起两落：同一个剧本，三个变量** | 三次热潮的重复模式，以及三个改变剧本的变量（✅ 已发） |
| 03 | 当 AI 走出科技公司：ChatGPT 与 DeepSeek 的启示 | 普及的两个层级：交互（ChatGPT）+ 成本（DeepSeek）（✅ 已发） |
| 04 | 从词向量到大模型：NLP 进化路线图 | 技术线：从 one-hot → Word2Vec → RNN → Transformer → BERT/GPT（✅ 已发） |

## 环境法医学系列

科普短文，用具体案例讲解环境暴露与健康效应的科学论证框架。

| # | 文章 | 说明 |
|---|------|------|
| 06 | **杜邦 C-8 污染案：科学如何论证工厂与健康的因果链** | 以杜邦 PFOA 案拆解"源→途径→暴露→效应→因果"六环节论证框架（✅ 已发） |
| 07 | **科学能排除因果吗？泡花碱厂调查的解读** | 武汉新洲泡花碱厂调查，同一框架反向拆解"科学如何否定因果"（✅ 已发） |

## 环境工程系列

电镀行业污染物全过程模拟与分析文章，从工艺产污到大气扩散再到健康风险评估。

| # | 文章 | 说明 |
|---|------|------|
| 08 | **电镀厂酸雾：从工艺产污到大气扩散与沉降** | 产污→集气→洗涤→高斯烟羽→干湿沉降→土壤酸化，全链条质量平衡与达标分析（✅ 已发） |
| 09 | **电镀厂铬（Cr(VI)）：大气沉降与健康风险** | 同一工厂 Cr(VI) 扩散、土壤累积、吸入/摄入致癌风险评估（US EPA IRIS）（✅ 已发） |

## 项目

| 项目 | 描述 | 技术栈 |
|------|------|--------|
| **ML Playground** | 所有算法的 FastAPI + Gradio 统一平台 | FastAPI, Gradio, Matplotlib |
| **Text-to-SQL 助手** | 自然语言转 SQL 查询 | Gradio, DeepSeek API |
| **环保申报 AI Agent** | 多轮对话 Agent，查法规 + 算排放 + 填表单 | LangGraph, DeepSeek, BGE |
| **环境法规智能问答** | RAG 知识库问答系统 | ChromaDB, BGE, DeepSeek, FastAPI |
| **LLM Wiki 知识库** | AI 自动构建的环保知识库 | YoudaoNote, LLM Wiki 范式 |

## 快速复现

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行 Notebook

```bash
# Day 1-15: 从线性回归到 Transformer
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/dayN_*.ipynb

# 或逐个运行
jupyter notebook notebooks/day1_linear_regression.ipynb
```

### 3. 运行项目

```bash
# ML Playground
uvicorn projects.ml_playground.app:app

# 环保申报 Agent
python projects/env_agent/app.py

# Text-to-SQL
python projects/app_text_to_sql.py

# RAG 法律问答
cd 环境法律法规智能问答系统 && python app.py
```

## 算法实现说明

- sklearn 仅用于 `train_test_split` 等辅助功能
- 环境模型为独立脚本，无类接口，直接运行输出结果

## 未跟踪的文件

以下路径存在于本地但不会推送 GitHub：

| 路径 | 说明 |
|------|------|
| `articles/` | 公众号文章内容 |
| `scripts/` | Notebook 生成 & 封面图脚本 |
| `plan.md` | 文章/项目状态清单 |
| `.mcp.json` | MCP 配置文件（本地机器相关） |
| `docs/` | 设计文档、笔记 |
| `CLAUDE.md` | Claude Code 项目说明 |
| `.venv/` | Python 虚拟环境 |
| `.env` | API 密钥等环境变量 |
| `projects/app_text_to_sql.py` | 个人项目 |
| `projects/simple_agent.py` | 个人项目 |
