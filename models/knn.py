"""
k-Nearest Neighbors classifier, pure numpy.

Parameters
----------
k : int
    Number of neighbors.
weights : str
    'uniform' (每个邻居等权重) or 'distance' (距离倒数加权)。
metric : str
    'euclidean' or 'manhattan'。

Notes
-----
predict 平票时偏向 classes_ 中排序靠前的类别（np.argmax 行为）。
"""
import numpy as np


class KNN:
    def __init__(self, k=5, weights='uniform', metric='euclidean'):
        self.k = k
        self.weights = weights
        self.metric = metric
        self.X_train_ = None
        self.y_train_ = None
        self.classes_ = None
        self._label_to_idx = None  # 映射 y 的原始 label → votes 数组索引

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)
        self.X_train_ = X
        self.y_train_ = y
        self.classes_ = np.unique(y)
        if self.k > len(X):
            raise ValueError(f"k={self.k} > n_train={len(X)}")
        self._label_to_idx = {c: i for i, c in enumerate(self.classes_)}
        return self

    def _pairwise_dist(self, X):
        if self.metric == 'euclidean':
            # ||a - b||^2 = ||a||^2 + ||b||^2 - 2 a.b
            x2 = np.sum(X ** 2, axis=1, keepdims=True)
            t2 = np.sum(self.X_train_ ** 2, axis=1)
            d2 = x2 + t2 - 2 * X @ self.X_train_.T
            return np.sqrt(np.maximum(d2, 0))
        elif self.metric == 'manhattan':
            return np.abs(X[:, None, :] - self.X_train_[None, :, :]).sum(axis=2)
        else:
            raise ValueError(f'Unknown metric: {self.metric}')

    def _predict_row(self, d_row):
        idx = np.argpartition(d_row, self.k)[:self.k]
        labels = np.array([self._label_to_idx[self.y_train_[i]] for i in idx])
        if self.weights == 'uniform':
            w = np.ones(self.k)
        elif self.weights == 'distance':
            w = 1.0 / (d_row[idx] + 1e-8)
        else:
            raise ValueError(f'Unknown weights: {self.weights}')
        return np.bincount(labels, weights=w, minlength=len(self.classes_))

    def predict_proba(self, X):
        X = np.asarray(X, dtype=float)
        D = self._pairwise_dist(X)
        proba = np.zeros((len(X), len(self.classes_)))
        for i, d_row in enumerate(D):
            votes = self._predict_row(d_row)
            proba[i] = votes / votes.sum()
        return proba

    def predict(self, X):
        proba = self.predict_proba(X)
        idx = np.argmax(proba, axis=1)
        return self.classes_[idx]