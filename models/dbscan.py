import numpy as np


class DBSCAN:
    """
    DBSCAN clustering, pure numpy.

    Parameters
    ----------
    eps : float
        Maximum distance between two samples for neighborhood.
    min_pts : int
        Minimum number of samples in a neighborhood to form a dense region.
    """
    def __init__(self, eps=0.5, min_pts=5):
        self.eps = eps
        self.min_pts = min_pts
        self.labels_ = None
        self.n_clusters_ = None
        self.n_noise_ = None

    def _region_query(self, X, i):
        """Return indices of all points within eps of X[i]."""
        diff = X - X[i]
        dists = np.sqrt(np.sum(diff ** 2, axis=1))
        return np.where(dists <= self.eps)[0]

    def fit(self, X):
        n = len(X)
        # -1 = unclassified, -2 = noise (provisional), 0+ = cluster id
        labels = -np.ones(n, dtype=int)
        cluster_id = 0

        for i in range(n):
            if labels[i] != -1:
                continue

            neighbors = self._region_query(X, i)

            if len(neighbors) < self.min_pts:
                labels[i] = -2
                continue

            # Core point: start a new cluster
            labels[i] = cluster_id
            seeds = [j for j in neighbors if j != i]

            while seeds:
                j = seeds.pop()

                if labels[j] >= 0:
                    continue

                if labels[j] == -2:
                    labels[j] = cluster_id
                    continue

                # labels[j] == -1: unclassified
                labels[j] = cluster_id
                new_neighbors = self._region_query(X, j)

                if len(new_neighbors) >= self.min_pts:
                    seeds.extend(nn for nn in new_neighbors if labels[nn] < 0)

            cluster_id += 1

        labels[labels == -2] = -1
        self.labels_ = labels
        self.n_clusters_ = cluster_id
        self.n_noise_ = (labels == -1).sum()
        return self

    def fit_predict(self, X):
        self.fit(X)
        return self.labels_
