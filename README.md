# ML Learning

机器学习 & 深度学习算法学习项目。每种算法用 Numpy 从零实现，在真实数据集上实验。

## 项目结构

```
├── models/           # 算法实现（纯 Numpy）
├── notebooks/        # 训练 & 可视化 Jupyter notebook
├── data/             # 数据集（Kaggle 下载）
├── utils/            # 工具函数
├── requirements.txt
└── .gitignore
```

## 快速复现

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载数据

本项目使用 Kaggle 数据集，需要自行下载后放入 `data/` 目录：

**House Prices: Advanced Regression Techniques**
- 链接：https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques
- 下载 `train.csv` 放入 `data/` 目录

### 3. 运行

```bash
# Day 1: 线性回归
jupyter notebook notebooks/day1_linear_regression.ipynb

# Day 2: Ridge & Lasso 回归
jupyter notebook notebooks/day2_ridge_lasso.ipynb
```

## 已实现算法

| Day | 算法 | Notebook | 模型文件 |
|-----|------|----------|----------|
| 1 | 线性回归（单变量 → 多变量） | `notebooks/day1_linear_regression.ipynb` | `models/linear_regression.py` |
| 2 | Ridge & Lasso（L1/L2 正则化） | `notebooks/day2_ridge_lasso.ipynb` | `models/ridge_regression.py` / `models/lasso_regression.py` |

## 算法实现说明

- 所有算法基于 Numpy 实现，不使用 sklearn 等 ML 库进行训练
- sklearn 仅用于 `train_test_split` 等辅助功能
- 梯度下降作为核心优化方法
