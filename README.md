# ML Learning

机器学习 & 深度学习算法学习项目 + LLM 工程作品集。

## 项目结构

```
├── models/           # 算法实现（ML 算法 + 环境模型）
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
| 06 | 他们坚持了三十年：Hinton、LeCun、Bengio | 2018 图灵奖 + 2024 诺奖；30 年寒冬坚持，学生的学生承包了今天大模型半壁江山 |
| 07 | AlphaGo → AlphaFold：AI 改变科学的两次证明 | 1997 深蓝"算"出胜利、2024 诺奖"发现"科学；27 年 AI 能力从"算"走到"发现" |

### 算法线 (`articles/ml/`)

从 numpy 手写到深度学习，每个算法包含原理推导与代码实现。

| # | 文章 |
|---|------|
| 00 | ML 算法选型指南 + ML Playground 介绍 |
| 01 | 线性回归 |
| 02 | 岭回归与 Lasso |
| 03 | 逻辑回归 |
| 04 | 决策树 CART |
| 05 | 随机森林 |
| 06 | GBDT / XGBoost |
| 07 | K-Means 聚类 |
| 08 | DBSCAN 密度聚类 |
| 09 | SVM |
| 10 | PCA 降维 |
| 11 | MLP 神经网络 |
| 12 | CNN 卷积神经网络 |
| 13 | RNN 与 LSTM |
| 14 | Word2Vec 词向量 |

### LLM 工具链线 (`articles/llm/`)

RAG、AI Agent、Prompt Engineering、Fine-tuning 等 LLM 工程实践。

| 文章 | 涉及概念 |
|------|---------|
| AI Agent 入门 | Agent, Tool Calling |
| RAG 实战：环境法典智能问答 | RAG, ChromaDB, DeepSeek |
| LLM Wiki：用 AI 构建知识库 | LLM Wiki, YoudaoNote |
| ML 入门 | ML 基础概念 |
| 你写的 Prompt 为什么不 work？5 个反模式自查 | Prompt Engineering |

### 项目工程线 (`articles/engineering/`)

从项目实战中总结的工程经验。

| # | 文章 |
|---|------|
| 01 | FastAPI 入门（以 ML Playground 为例） |

### 环境工程线 (`articles/env/`)

利用环境工程专业背景 + 编程能力，展示跨领域建模与分析。

| # | 文章 |
|---|------|
| 01 | 河流底泥镉污染分布 |
| 02 | 大气镉沉降模拟 |
| 03 | 洪水底泥镉农田输入 |
| 04 | 室内甲醛通风模型 |
| 05 | 废石清理后底泥镉去哪了 |
| 06 | 杜邦 C-8 污染案：科学如何论证工厂与健康的因果链 |
| 07 | 科学能排除因果吗？泡花碱厂调查的解读（C8 姊妹篇） |
| 08 | 电镀厂酸雾：从工艺产污到大气扩散与沉降 |
| 09 | 电镀厂铬（Cr(VI)）：大气沉降与健康风险 |
| 10 | 甲酰胺是什么，它可能从哪里来 |
| 11 | 邻苯二甲酸酯：用了八十年的增塑剂，二十年监管路 |

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

