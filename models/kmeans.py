import numpy as np


class KMeans:
    """
    K-Means clustering, pure numpy.

    Parameters
    ----------
    k : int
        Number of clusters (default 3).
    max_iters : int
        Maximum iterations (default 100).
    random_state : int or None
        Random seed for centroid initialization (default 42).
    """
    def __init__(self, k=3, max_iters=100, random_state=42):
        self.k = k
        self.max_iters = max_iters
        self.random_state = random_state
        self.centroids_ = None
        self.inertia_ = None
        self.labels_ = None
        self.n_iter_ = None

    def _init_centroids(self, X):
        """Randomly select k distinct samples as initial centroids."""
        rng = np.random.RandomState(self.random_state)
        indices = rng.choice(len(X), size=self.k, replace=False)
        return X[indices].copy()

    def _assign_clusters(self, X):
        """Assign each sample to the nearest centroid. Return (labels, inertia)."""
        dists = np.zeros((len(X), self.k))
        for j, c in enumerate(self.centroids_):
            diff = X - c
            dists[:, j] = np.sum(diff ** 2, axis=1)
        labels = np.argmin(dists, axis=1)
        inertia = np.min(dists, axis=1).sum()
        return labels, inertia

    def fit(self, X):
        """
        Run Lloyd's algorithm.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
        """
        self.centroids_ = self._init_centroids(X)
        prev_labels = None

        for it in range(self.max_iters):
            labels, inertia = self._assign_clusters(X)

            # Check convergence: no label change
            if prev_labels is not None and np.all(labels == prev_labels):
                self.n_iter_ = it
                break
            prev_labels = labels.copy()

            # Update centroids
            for j in range(self.k):
                mask = labels == j
                if mask.sum() > 0:
                    self.centroids_[j] = X[mask].mean(axis=0)
                # If empty cluster, keep previous centroid (no re-init)

        else:
            self.n_iter_ = self.max_iters

        self.labels_, self.inertia_ = self._assign_clusters(X)

    def predict(self, X):
        """Assign new samples to the nearest centroid."""
        dists = np.zeros((len(X), self.k))
        for j, c in enumerate(self.centroids_):
            diff = X - c
            dists[:, j] = np.sum(diff ** 2, axis=1)
        return np.argmin(dists, axis=1)
