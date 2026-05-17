# ML Learning

机器学习 & 深度学习算法学习项目。每种算法用 Numpy 从零实现，在真实数据集上实验。

## 项目结构

```
├── models/           # 算法实现（纯 Numpy）
├── notebooks/        # 训练 & 可视化 Jupyter notebook
├── data/             # 数据集
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

**Titanic: Machine Learning from Disaster**
- Day 3 使用 pandas 内置数据集，自动下载
- 或手动下载：https://raw.githubusercontent.com/pandas-dev/pandas/main/doc/data/titanic.csv
- 保存为 `titanic_train.csv` 放入 `data/` 目录

**Iris (鸢尾花数据集)**
- Day 4 使用 `sklearn.datasets.load_iris()` 自动加载，无需手动下载

**Digits (手写数字数据集)**
- Day 5 使用 `sklearn.datasets.load_digits()` 自动加载，无需手动下载

**California Housing (加州房价数据集)**
- Day 6 使用 `sklearn.datasets.fetch_california_housing()` 自动加载，无需手动下载

**Mall Customers (商场客户数据)**
- Day 7 使用 `kagglehub.dataset_download()` 自动下载，无需手动操作

**make_moons (月牙形合成数据)**
- Day 8 使用 `sklearn.datasets.make_moons()` 自动生成，无需手动下载

### 3. 运行

```bash
# Day 1: 线性回归
jupyter notebook notebooks/day1_linear_regression.ipynb

# Day 2: Ridge & Lasso 回归
jupyter notebook notebooks/day2_ridge_lasso.ipynb

# Day 3: 逻辑回归（Titanic 幸存者预测）
jupyter notebook notebooks/day3_logistic_regression.ipynb

# Day 4: 决策树（Iris 分类）
jupyter notebook notebooks/day4_decision_tree.ipynb

# Day 5: 随机森林（Digits 手写数字分类）
jupyter notebook notebooks/day5_random_forest.ipynb

# Day 6: GBDT（加州房价回归）
jupyter notebook notebooks/day6_gbdt.ipynb

# Day 7: K-Means（商场客户分群）
jupyter notebook notebooks/day7_kmeans.ipynb

# Day 8: DBSCAN（月牙形数据密度聚类）
jupyter notebook notebooks/day8_dbscan.ipynb
```

## 已实现算法

| Day | 算法 | Notebook | 模型文件 |
|-----|------|----------|----------|
| 1 | 线性回归（单变量 → 多变量） | `notebooks/day1_linear_regression.ipynb` | `models/linear_regression.py` |
| 2 | Ridge & Lasso（L1/L2 正则化） | `notebooks/day2_ridge_lasso.ipynb` | `models/ridge_regression.py` / `models/lasso_regression.py` |
| 3 | 逻辑回归（二分类） | `notebooks/day3_logistic_regression.ipynb` | `models/logistic_regression.py` |
| 4 | 决策树（CART 分类树） | `notebooks/day4_decision_tree.ipynb` | `models/decision_tree.py` |
| 5 | 随机森林（Bagging + 随机特征） | `notebooks/day5_random_forest.ipynb` | `models/random_forest.py` |
| 6 | GBDT（梯度提升，串行回归树） | `notebooks/day6_gbdt.ipynb` | `models/gradient_boosting.py` |
| 7 | K-Means（Lloyd 算法） | `notebooks/day7_kmeans.ipynb` | `models/kmeans.py` |
| 8 | DBSCAN（密度聚类） | `notebooks/day8_dbscan.ipynb` | `models/dbscan.py` |

## 算法实现说明

- 所有算法基于 Numpy 实现，不使用 sklearn 等 ML 库进行训练
- sklearn 仅用于 `train_test_split` 等辅助功能
- 梯度下降作为核心优化方法
