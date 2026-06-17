import numpy as np


def _linear_kernel(x, y):
    return np.dot(x, y)


def _rbf_kernel(x, y, gamma):
    diff = x - y
    return np.exp(-gamma * np.dot(diff, diff))


def _poly_kernel(x, y, degree, coef0):
    return (np.dot(x, y) + coef0) ** degree


class SVM:
    """Support Vector Machine via SMO.

    Binary classifier using the kernel trick. Solves the dual problem
    with Sequential Minimal Optimization.

    Parameters
    ----------
    C : float
        Regularization parameter. Smaller C → wider margin (more tolerance
        for misclassification).
    kernel : {'linear', 'rbf', 'poly'}
        Kernel function.
    degree : int
        Degree for poly kernel (ignored otherwise).
    gamma : float
        RBF width parameter — controls influence radius of each support vector.
        Default: 1/n_features.
    coef0 : float
        Independent term for poly kernel.
    tol : float
        Tolerance for KKT violation — lower = more precise but slower.
    max_iter : int
        Maximum SMO iterations (outer loop passes).
    """
    def __init__(self, C=1.0, kernel='rbf', degree=3, gamma=None,
                 coef0=0.0, tol=1e-3, max_iter=200):
        self.C = C
        self.kernel = kernel
        self.degree = degree
        self.gamma = gamma
        self.coef0 = coef0
        self.tol = tol
        self.max_iter = max_iter

    def _kernel_fn(self, x, y):
        if self.kernel == 'linear':
            return _linear_kernel(x, y)
        if self.kernel == 'rbf':
            return _rbf_kernel(x, y, self.gamma)
        if self.kernel == 'poly':
            return _poly_kernel(x, y, self.degree, self.coef0)
        raise ValueError(f"Unknown kernel: {self.kernel}")

    def _compute_kernel_matrix(self, X):
        """Precompute full kernel matrix K[i,j] = K(X[i], X[j])."""
        n = X.shape[0]
        K = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                k = self._kernel_fn(X[i], X[j])
                K[i, j] = k
                K[j, i] = k
        return K

    def fit(self, X, y):
        n, d = X.shape
        # Encode labels as ±1
        y_ = np.where(y <= 0, -1.0, 1.0)

        if self.gamma is None:
            self.gamma = 1.0 / d

        self.X_ = X
        self.y_ = y_
        self.K_ = self._compute_kernel_matrix(X)

        # SMO state
        alpha = np.zeros(n)
        b = 0.0
        passes = 0

        while passes < self.max_iter:
            num_changed = 0
            for i in range(n):
                Ei = self._decision_fn(alpha, b, i) - y_[i]
                # Check KKT violation
                if (y_[i] * Ei < -self.tol and alpha[i] < self.C) \
                        or (y_[i] * Ei > self.tol and alpha[i] > 0):
                    # Select j != i
                    j = self._select_second(i, n)
                    Ej = self._decision_fn(alpha, b, j) - y_[j]

                    ai_old, aj_old = alpha[i], alpha[j]

                    # Compute bounds L, H
                    if y_[i] != y_[j]:
                        L = max(0, alpha[j] - alpha[i])
                        H = min(self.C, self.C + alpha[j] - alpha[i])
                    else:
                        L = max(0, alpha[i] + alpha[j] - self.C)
                        H = min(self.C, alpha[i] + alpha[j])

                    if abs(L - H) < 1e-10:
                        continue

                    eta = 2 * self.K_[i, j] - self.K_[i, i] - self.K_[j, j]
                    if eta >= 0:
                        continue

                    # Update α_j
                    alpha[j] -= y_[j] * (Ei - Ej) / eta
                    alpha[j] = np.clip(alpha[j], L, H)

                    if abs(alpha[j] - aj_old) < 1e-10:
                        continue

                    # Update α_i
                    alpha[i] += y_[i] * y_[j] * (aj_old - alpha[j])

                    # Update bias b
                    bi = b - Ei - y_[i] * (alpha[i] - ai_old) * self.K_[i, i] \
                         - y_[j] * (alpha[j] - aj_old) * self.K_[i, j]
                    bj = b - Ej - y_[i] * (alpha[i] - ai_old) * self.K_[i, j] \
                         - y_[j] * (alpha[j] - aj_old) * self.K_[j, j]

                    if 0 < alpha[i] < self.C:
                        b = bi
                    elif 0 < alpha[j] < self.C:
                        b = bj
                    else:
                        b = (bi + bj) / 2

                    num_changed += 1

            if num_changed == 0:
                passes += 1
            else:
                passes = 0

        # Store support vectors
        sv_mask = alpha > 1e-8
        self.alpha_ = alpha[sv_mask]
        self.sv_X_ = X[sv_mask]
        self.sv_y_ = y_[sv_mask]
        self.b_ = b
        self.n_support_ = self.alpha_.shape[0]
        return self

    def _decision_fn(self, alpha, b, i):
        """Compute decision function value for sample i: f(x_i) = Σ α_j y_j K(x_j, x_i) + b."""
        return np.dot(alpha * self.y_, self.K_[:, i]) + b

    def _decision(self, X):
        """Decision values f(x) for new samples."""
        n = X.shape[0]
        f = np.zeros(n)
        for i in range(n):
            s = self.b_
            for aj, xj, yj in zip(self.alpha_, self.sv_X_, self.sv_y_):
                s += aj * yj * self._kernel_fn(xj, X[i])
            f[i] = s
        return f

    def predict(self, X):
        return np.sign(self._decision(X)).astype(int)

    def predict_proba(self, X):
        """Return probability-like confidence via sigmoid of decision value."""
        f = self._decision(X)
        return 1.0 / (1.0 + np.exp(-np.clip(f, -100, 100)))

    def _select_second(self, i, n):
        j = np.random.randint(n - 1)
        return j if j < i else j + 1
