# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Machine learning & deep learning algorithm learning project. 16 algorithms across 6 phases, implemented from scratch (numpy-based, no sklearn for training). Each algorithm: model class → Jupyter experiment → Chinese 公众号 article.

GitHub: `https://github.com/HuangWuwutelling/ml-learning` (push proxy needed in China: `git config --global http.proxy http://127.0.0.1:7897`)

## Learning Roadmap (6 Phases)

| Phase | Algorithms | Status |
|-------|-----------|--------|
| 1. Linear Models | Linear Regression ✅, Ridge, Lasso, Logistic Regression | 1/4 done |
| 2. Tree/Ensemble | CART, Random Forest, GBDT/XGBoost | not started |
| 3. SVM | Linear + Kernel SVM | not started |
| 4. Clustering | K-Means, DBSCAN | not started |
| 5. Dimensionality | PCA | not started |
| 6. Deep Learning | MLP, CNN, RNN/LSTM, Word2Vec, AE, GAN | not started |

Full details in `plan.md` (excluded from git).

## Standard Workflow for Adding a New Algorithm

1. **Model class**: Create `models/<algorithm>.py` with `__init__`, `fit(self, X, y)`, `predict(self, X)`. Pure numpy — no sklearn for training. Record losses in `self.losses`.
2. **Notebook**: Create `notebooks/dayN_<algorithm>.ipynb` with the standard flow:
   - Load data → select features → log1p transform target
   - train_test_split (80/20, random_state=42)
   - Standardize (fit on train only, transform both)
   - Train → evaluate (R² / RMSE / accuracy)
   - Visualization cells (loss curve, scatter plots) for article screenshots
3. **Article**: Create `articles/NN_<algorithm>.md` with problem-driven narrative:
   - Start simple → discover issue → improve → compare results
   - Personal/conversational tone (use "我", specific experiences, real reactions)
   - Include before/after results table
   - Screenshot placeholders: `> **【截图 N】** description`
4. **Git**: `git add` → `git commit -m "Day N: algorithm name"` → `git push`

## Directory Structure

- `models/` — Algorithm implementations (pure numpy)
- `notebooks/` — Jupyter experiments with training, evaluation, visualization
- `data/` — Kaggle datasets (train.csv, test.csv) — download from Kaggle, not committed from articles/
- `articles/` — Chinese 公众号 articles (excluded from git)
- `utils/` — Utility functions
- `plan.md` — Learning roadmap (excluded from git)

## Common Commands

```bash
pip install -r requirements.txt   # numpy, pandas, matplotlib, scikit-learn
jupyter notebook                  # start from project root
git push                          # requires proxy: git config --global http.proxy http://127.0.0.1:7897
```

## Common Gotchas

- **Matplotlib Chinese font**: Setting `plt.style.use('seaborn')` resets font config. Always re-set after style:
  ```python
  plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
  plt.rcParams['axes.unicode_minus'] = False
  ```
- **Standardization**: Fit on train set only, transform both train and test (avoid data leakage)
- **log transform**: Use `np.log1p()` / `np.expm1()` for long-tail target distributions
- **Article screenshots**: Use seaborn style + steelblue (data) / crimson (regression line) color scheme
