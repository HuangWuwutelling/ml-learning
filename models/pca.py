import numpy as np


class PCA:
    """
    Principal Component Analysis via SVD.

    Parameters
    ----------
    n_components : int or None
        Number of components to keep. If None, keep all.
    """
    def __init__(self, n_components=None):
        self.n_components = n_components
        self.components_ = None
        self.mean_ = None
        self.explained_variance_ = None
        self.explained_variance_ratio_ = None
        self.singular_values_ = None

    def fit(self, X):
        n_samples, n_features = X.shape
        self.mean_ = X.mean(axis=0)
        X_centered = X - self.mean_

        # SVD on centered data
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

        n_components = self.n_components or n_features
        self.components_ = Vt[:n_components]
        self.singular_values_ = S[:n_components]

        # Explained variance
        var_total = (S ** 2) / (n_samples - 1)
        self.explained_variance_ = var_total[:n_components]
        self.explained_variance_ratio_ = self.explained_variance_ / var_total.sum()
        return self

    def transform(self, X):
        X_centered = X - self.mean_
        return np.dot(X_centered, self.components_.T)

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X_pca):
        return np.dot(X_pca, self.components_) + self.mean_
