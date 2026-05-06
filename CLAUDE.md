# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Machine learning & deep learning algorithm learning project. 16 algorithms across 6 phases, implemented from scratch (numpy-based, no sklearn for training). Each algorithm: model class → Jupyter experiment → Chinese 公众号 article.

GitHub: `https://github.com/HuangWuwutelling/ml-learning` (push proxy needed in China: `git config --global http.proxy http://127.0.0.1:7897`)

## Learning Roadmap (6 Phases)

| Phase | Algorithms | Status |
|-------|-----------|--------|
| 1. Linear Models | Linear Regression ✅, Ridge ✅, Lasso ✅, Logistic Regression ✅ | 4/4 done |
| 2. Tree/Ensemble | CART, Random Forest, GBDT/XGBoost | not started |
| 3. SVM | Linear + Kernel SVM | not started |
| 4. Clustering | K-Means, DBSCAN | not started |
| 5. Dimensionality | PCA | not started |
| 6. Deep Learning | MLP, CNN, RNN/LSTM, Word2Vec, AE, GAN | not started |

Full roadmap with recommended tutorials in `plan.md` (gitignored).

## Data Sources

- **House Prices (Days 1-2)**: Kaggle — download `train.csv` and `test.csv` from https://www.kaggle.com/competitions/house-prices-advanced-regression-techniques
- **Titanic (Day 3)**: pandas GitHub repo — `https://raw.githubusercontent.com/pandas-dev/pandas/main/doc/data/titanic.csv` (single combined file, split 80/20 in notebook)

## Standard Workflow for Adding a New Algorithm

1. **Model class**: Create `models/<algorithm>.py`. Pure numpy — no sklearn for training.
   - `__init__(self, lr=0.01, epochs=1000, ...)` — hyperparameters
   - `fit(self, X, y)` — gradient descent training, stores losses in `self.losses`
   - `predict(self, X)` — returns numpy array of predictions
   - For classifiers: also `predict_proba(self, X)` for probability output

2. **Notebook**: Create `notebooks/dayN_<algorithm>.ipynb` following the standard flow:
   - `import sys; sys.path.append("..")` or `os.path.abspath("..")` to reach `models/`
   - Load data → optional log1p for long-tail targets → train_test_split (80/20, random_state=42)
   - Standardize (fit on train only, transform both)
   - Train model(s) → evaluate
   - Scan hyperparameters
   - Visualization: loss curves, weight comparison, true vs predicted scatter / confusion matrix
   - Final comparison table as matplotlib `ax.table()` rendered as PNG for 公众号
   - Create via raw JSON (`.ipynb` format) — no need for `nbformat` library

3. **Article**: Create `articles/NN_<algorithm>.md` (gitignored, not pushed to GitHub):
   - Problem-driven narrative with personal tone (use "我")
   - Before/after results tables
   - Screenshot markers: `> **【截图 N】** description`
   - Optional: generate a cover image as PNG (900×383px, 100dpi) for 公众号

4. **Git**: commit with message `"Day N: algorithm name — brief description"`, push via proxy:
   ```bash
   git add -A
   git commit -m "Day N: algorithm name — what it does"
   git config --global http.proxy http://127.0.0.1:7897
   git push
   git config --global --unset http.proxy
   ```

5. **Verify**: re-execute notebook to confirm all cells run and outputs are saved:
   ```bash
   python -m jupyter nbconvert --to notebook --execute --inplace notebooks/dayN_*.ipynb
   ```

## Common Evaluation Patterns

**Regression** (House Prices):
```python
def evaluate(model, X, y):
    y_pred = model.predict(X)
    rmse = np.sqrt(np.mean((y - y_pred)**2))
    ss_res, ss_tot = np.sum((y-y_pred)**2), np.sum((y-y.mean())**2)
    return rmse, 1 - ss_res/ss_tot
```

**Classification** (Titanic):
```python
def accuracy(y_true, y_pred):
    return np.mean(y_true == y_pred)

def evaluate(model, X, y):
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)
    acc = accuracy(y, y_pred)
    eps = 1e-8
    loss = -np.mean(y * np.log(y_prob + eps) + (1 - y) * np.log(1 - y_prob + eps))
    return acc, loss

def confusion_matrix(y_true, y_pred):
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    return np.array([[tn, fp], [fn, tp]])
```

## Re-executing Notebooks

```bash
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/dayN_*.ipynb
```

## Directory Structure

- `models/` — Algorithm implementations (pure numpy, one file per algorithm)
- `notebooks/` — Jupyter experiments with training, evaluation, visualization
- `data/` — Datasets (not committed to git)
- `articles/` — Chinese 公众号 articles (gitignored)
- `utils/` — Empty (utility functions if needed later)
- `plan.md` — Learning roadmap with tutorial references (gitignored)

## Existing Models

| Algorithm | File | Status |
|-----------|------|--------|
| Linear Regression | `models/linear_regression.py` | ✅ committed |
| Ridge Regression | `models/ridge_regression.py` | ✅ committed |
| Lasso Regression | `models/lasso_regression.py` | ✅ committed |
| Logistic Regression | `models/logistic_regression.py` | ✅ done |

## Article Writing Style

Articles are Chinese 公众号 posts with a personal, practitioner tone:
- **Tone**: natural but not overly colloquial — use "我" for personal observations, avoid textbook phrases ("从信息论的角度", "答案就是")
- **Terminology**: prefer academic terms ("映射" not "压", "经过" not "套", "偏差" not "离谱")
- **Screenshot descriptions**: each screenshot gets 2-3 sentences — first sentence describes what's shown, followed by 1-2 sentences explaining key observations or insights
- **Structure**: problem-driven narrative, before/after comparisons, concrete results

## Key Conventions

- **Regression target**: `np.log1p()` for long-tail distributions (e.g., SalePrice)
- **Standardization**: `(X - mean) / std`, fit on train only
- **Random state**: always `random_state=42` for reproducibility
- **Feature engineering (House Prices)**: numerical → median fill → ordinal mapping → OHE
- **Feature engineering (Titanic)**: Age→median fill, Sex→binary (male=1), Embarked→OHE, drop Name/Ticket/Cabin
- **Visualization**: seaborn-v0_8-whitegrid style, SimHei/Microsoft YaHei for Chinese fonts, `axes.unicode_minus=False` (fixes U+2212 minus sign glyph issue with Chinese fonts)
- **Log scale gotcha**: matplotlib log-scale axes with Chinese fonts render U+2212 minus in scientific notation — avoid log scale on axes with negative labels, or use `FuncFormatter(lambda x, _: f"{x:.4g}")` for log-scale x-axis
- **Article screenshots**: matplotlib `ax.table()` for comparison tables, saved as PNG at 200dpi
- **Cover image**: generated with matplotlib at exactly 900×383px (figsize=(9, 3.83), dpi=100), no `bbox_inches='tight'`
- **Classifier visualization**: add a sigmoid/softmax function curve plot early in the notebook to explain the activation function
- **Notebook creation**: write raw JSON (`.ipynb` format 4.4) — cells have `cell_type`, `source` (list of strings), `metadata`, and `execution_count`/`outputs` for code cells

## Gradients Reference

- **Linear Regression**: `dw = (1/n) X.T · (ŷ - y)`, `db = (1/n) Σ(ŷ - y)`
- **Ridge (L2)**: `dw += α·w` (weight decay), bias not regularized
- **Lasso (L1)**: `dw += α·sign(w)` (constant-force shrinkage)
- **Logistic Regression**: Same gradient form as linear regression, but `ŷ = σ(Xw+b)` (sigmoid) and loss is BCE not MSE

## Dependencies

numpy, pandas, matplotlib, scikit-learn (train_test_split only).

## Environment

- Windows 11, Python 3.11 via Anaconda or standalone
- `jupyter` may need to be launched as `python -m jupyter notebook` if not in PATH
- Git push to GitHub requires proxy in China: `http://127.0.0.1:7897`
