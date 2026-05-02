# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Machine learning & deep learning algorithm learning project. Each algorithm is implemented (numpy-based, no sklearn for training), experimented in Jupyter notebooks, and documented with Chinese 公众号 articles for portfolio.

## Directory Structure

- `models/` — Algorithm class implementations (e.g., `linear_regression.py`)
- `notebooks/` — Jupyter notebooks for training, evaluation, and visualization
- `data/` — Kaggle datasets (train.csv, test.csv)
- `articles/` — Chinese 公众号 articles (excluded from GitHub via .gitignore)
- `plan.md` — Learning roadmap (excluded from GitHub via .gitignore)
- `requirements.txt` — For reproducibility
- `.gitignore` — Excludes articles/, plan.md, __pycache__, .ipynb_checkpoints

## Model Pattern

Each model class follows:
- `__init__(self, lr=0.01, epochs=1000)` — hyperparams
- `fit(self, X, y)` — gradient descent training, records `self.losses`
- `predict(self, X)` — returns predictions

Example: `LinearRegression` in `models/linear_regression.py`.

## Notebook Pattern

Each notebook follows this flow:
1. Load data → select features → log1p transform target
2. train_test_split (80/20, random_state=42)
3. Standardize (fit on train, transform both train and test)
4. Train model → evaluate (RMSE, R²)
5. Visualization cells (loss curve, scatter plots) for article screenshots

## Common Commands

```bash
# Activate conda environment
conda activate base  # or your env name

# Start Jupyter from project root
jupyter notebook

# Install dependencies
pip install numpy pandas matplotlib scikit-learn
```

## Common Gotchas

- **Matplotlib Chinese font**: `plt.style.use('seaborn')` resets font config. Always re-set after style: `plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']` + `plt.rcParams['axes.unicode_minus'] = False`
- **Standardization**: Must fit on train set only, then transform both train and test (to avoid data leakage)
- **log transform**: Use `np.log1p()` / `np.expm1()` for target variable to handle long-tail distributions
- **Screenshot generation**: Use seaborn style + consistent color scheme (steelblue for data, crimson for regression line) for article-ready visuals

## Dependencies

numpy, pandas, matplotlib, scikit-learn (train_test_split only). PyTorch (deep learning phase).
