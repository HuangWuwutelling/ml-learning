import numpy as np


class _RegressionTree:
    """Regression tree using MSE — internal base learner for GBDT."""
    def __init__(self, max_depth=3, min_samples_leaf=1):
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.tree_ = None

    def _mse(self, y):
        if len(y) < 2:
            return 0.0
        return np.var(y) * len(y)

    def _find_split(self, X, y, _n_candidates=50):
        """Find best split using at most _n_candidates thresholds per feature."""
        best_mse, best_feat, best_thresh = float('inf'), None, None
        n_features = X.shape[1]

        for f in range(n_features):
            col = X[:, f]
            values = np.unique(col)
            if len(values) < 2:
                continue
            midpoints = (values[:-1] + values[1:]) / 2
            if len(midpoints) > _n_candidates:
                idx = np.linspace(0, len(midpoints) - 1, _n_candidates, dtype=int)
                candidates = midpoints[idx]
            else:
                candidates = midpoints
            for thresh in candidates:
                mask = col <= thresh
                if mask.sum() < self.min_samples_leaf or (~mask).sum() < self.min_samples_leaf:
                    continue
                mse = self._mse(y[mask]) + self._mse(y[~mask])
                if mse < best_mse:
                    best_mse = mse
                    best_feat = f
                    best_thresh = thresh
        return best_feat, best_thresh

    def _build_tree(self, X, y, depth):
        node = {'value': np.mean(y), 'n_samples': len(y)}
        if depth >= self.max_depth or len(y) < self.min_samples_leaf * 2:
            return node

        feat, thresh = self._find_split(X, y)
        if feat is None:
            return node

        mask = X[:, feat] <= thresh
        node['feature_idx'] = feat
        node['threshold'] = thresh
        node['left'] = self._build_tree(X[mask], y[mask], depth + 1)
        node['right'] = self._build_tree(X[~mask], y[~mask], depth + 1)
        return node

    def fit(self, X, y):
        self.tree_ = self._build_tree(X, y, 0)
        return self

    def predict(self, X):
        return np.array([self._predict_one(x) for x in X])

    def _predict_one(self, x, node=None):
        if node is None:
            node = self.tree_
        if 'left' not in node:
            return node['value']
        if x[node['feature_idx']] <= node['threshold']:
            return self._predict_one(x, node['left'])
        return self._predict_one(x, node['right'])


class GBDTRegressor:
    """
    Gradient Boosting Decision Tree for regression.

    Builds shallow regression trees sequentially, each fitting the residuals
    (negative gradients) of the current ensemble.

    Parameters
    ----------
    n_estimators : int, default=100
        Number of boosting stages (trees).
    learning_rate : float, default=0.1
        Shrinkage factor — scales each tree's contribution.
    max_depth : int, default=3
        Maximum depth of each regression tree.
    min_samples_leaf : int, default=1
        Minimum samples per leaf in each tree.
    """
    def __init__(self, n_estimators=100, learning_rate=0.1,
                 max_depth=3, min_samples_leaf=1):
        self.n_estimators = n_estimators
        self.lr = learning_rate
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.trees_ = []
        self.initial_pred_ = None
        self.train_loss_ = []

    def fit(self, X, y):
        self.initial_pred_ = np.mean(y)
        F = np.full(len(y), self.initial_pred_)

        for i in range(self.n_estimators):
            residuals = y - F
            tree = _RegressionTree(
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
            )
            tree.fit(X, residuals)
            self.trees_.append(tree)
            F += self.lr * tree.predict(X)
            self.train_loss_.append(np.mean((y - F) ** 2))
        return self

    def predict(self, X):
        pred = np.full(X.shape[0], self.initial_pred_)
        for tree in self.trees_:
            pred += self.lr * tree.predict(X)
        return pred


class GBDTClassifier:
    """
    Gradient Boosting Decision Tree for binary classification.

    Uses log loss (binary cross-entropy). Each tree fits the gradient
    of the log loss w.r.t. the log-odds prediction.

    Parameters
    ----------
    n_estimators : int, default=100
    learning_rate : float, default=0.1
    max_depth : int, default=3
    min_samples_leaf : int, default=1
    """
    def __init__(self, n_estimators=100, learning_rate=0.1,
                 max_depth=3, min_samples_leaf=1):
        self.n_estimators = n_estimators
        self.lr = learning_rate
        self.max_depth = max_depth
        self.min_samples_leaf = min_samples_leaf
        self.trees_ = []
        self.initial_pred_ = None
        self.train_loss_ = []

    def fit(self, X, y):
        y = np.asarray(y, dtype=float)
        pos_ratio = np.mean(y)
        # Guard against log(0) and log(div by 0)
        pos_ratio = np.clip(pos_ratio, 1e-15, 1 - 1e-15)
        log_odds = np.log(pos_ratio / (1 - pos_ratio))

        self.initial_pred_ = log_odds
        F = np.full(len(y), log_odds)

        for i in range(self.n_estimators):
            p = 1 / (1 + np.exp(-F))
            residuals = y - p  # gradient of log loss
            tree = _RegressionTree(
                max_depth=self.max_depth,
                min_samples_leaf=self.min_samples_leaf,
            )
            tree.fit(X, residuals)
            self.trees_.append(tree)
            F += self.lr * tree.predict(X)
            # Log loss
            p = 1 / (1 + np.exp(-F))
            p = np.clip(p, 1e-15, 1 - 1e-15)
            self.train_loss_.append(
                -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
            )
        return self

    def predict_proba(self, X):
        F = np.full(X.shape[0], self.initial_pred_)
        for tree in self.trees_:
            F += self.lr * tree.predict(X)
        p = 1 / (1 + np.exp(-F))
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)
