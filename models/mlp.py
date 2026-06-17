"""
Multilayer Perceptron (MLP) — fully-connected feedforward network.

 Architecture
   Input → [Linear → ReLU]^(L-1) → Linear → Softmax → Output

 Forward: X @ W + b → activation → next layer
 Backward: chain rule gradients flowing from output to input

 References
   - Rumelhart, Hinton, Williams (1986). Learning representations by
     back-propagating errors.
   - Bishop (2006). Pattern Recognition and Machine Learning, Ch. 5.
"""
import numpy as np


class MLP:
    """Multilayer Perceptron for multi-class classification.

    Parameters
    ----------
    layer_dims : list of int
        Dimensions of each layer, e.g. [64, 32, 10] means
        64 inputs → 32 hidden → 10 outputs.
    lr : float
        Learning rate for gradient descent.
    epochs : int
        Number of full passes over the training data.
    random_state : int
        Seed for weight initialization.
    """

    def __init__(self, layer_dims, lr=0.01, epochs=1000, random_state=42):
        self.layer_dims = layer_dims
        self.lr = lr
        self.epochs = epochs
        self.random_state = random_state
        self.params = {}
        self.losses_ = []

    # ── Activation functions ─────────────────────────────

    @staticmethod
    def _relu(Z):
        return np.maximum(0, Z)

    @staticmethod
    def _relu_derivative(Z):
        return (Z > 0).astype(float)

    @staticmethod
    def _softmax(Z):
        """Stable softmax: subtract max per row to prevent overflow."""
        shifted = Z - Z.max(axis=1, keepdims=True)
        exp_z = np.exp(shifted)
        return exp_z / exp_z.sum(axis=1, keepdims=True)

    # ── Parameter initialization ─────────────────────────

    def _init_params(self):
        """Xavier (Glorot) initialization for all weight matrices."""
        rng = np.random.RandomState(self.random_state)
        for i in range(1, len(self.layer_dims)):
            fan_in = self.layer_dims[i - 1]
            fan_out = self.layer_dims[i]
            limit = np.sqrt(6 / (fan_in + fan_out))
            self.params[f"W{i}"] = rng.uniform(-limit, limit, (fan_in, fan_out))
            self.params[f"b{i}"] = np.zeros((1, fan_out))

    # ── Forward propagation ──────────────────────────────

    def _forward(self, X):
        """Run forward pass, cache intermediate values for backward.

        Returns
        -------
        cache : dict with keys:
            A0, Z1, A1, Z2, A2, ..., A{L}  (L = output layer)
        """
        cache = {"A0": X}
        L = len(self.layer_dims) - 1  # number of transformations

        for i in range(1, L + 1):
            A_prev = cache[f"A{i-1}"]
            Z = A_prev @ self.params[f"W{i}"] + self.params[f"b{i}"]
            cache[f"Z{i}"] = Z

            if i == L:  # output layer: softmax
                cache[f"A{i}"] = self._softmax(Z)
            else:  # hidden layer: ReLU
                cache[f"A{i}"] = self._relu(Z)

        return cache

    # ── Backward propagation ─────────────────────────────

    def _backward(self, cache, y_onehot):
        """Compute gradients via backpropagation (chain rule).

        For the output layer, the gradient of softmax + cross-entropy
        simplifies to (A - y) — a well-known result.

        Parameters
        ----------
        cache : dict
            Forward-pass cache from _forward().
        y_onehot : ndarray, shape (n, n_classes)
            Ground-truth one-hot labels.

        Returns
        -------
        grads : dict with keys W1, b1, ..., W{L}, b{L}
        """
        m = y_onehot.shape[0]
        L = len(self.layer_dims) - 1
        grads = {}

        # Output layer: dZ = A - y  (simplified gradient)
        A_out = cache[f"A{L}"]
        dZ = A_out - y_onehot
        grads[f"W{L}"] = cache[f"A{L-1}"].T @ dZ / m
        grads[f"b{L}"] = dZ.sum(axis=0, keepdims=True) / m

        # Hidden layers (L-1 down to 1)
        for i in range(L - 1, 0, -1):
            dA = dZ @ self.params[f"W{i+1}"].T
            dZ = dA * self._relu_derivative(cache[f"Z{i}"])
            grads[f"W{i}"] = cache[f"A{i-1}"].T @ dZ / m
            grads[f"b{i}"] = dZ.sum(axis=0, keepdims=True) / m

        return grads

    # ── Loss ─────────────────────────────────────────────

    @staticmethod
    def _cross_entropy(y_true, y_pred):
        """Cross-entropy loss with epsilon for numerical stability."""
        return -np.mean(np.sum(y_true * np.log(y_pred + 1e-8), axis=1))

    # ── Public API ───────────────────────────────────────

    def fit(self, X, y):
        """Train the network using gradient descent.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Training data.
        y : ndarray, shape (n_samples,) or (n_samples, n_classes)
            Labels (1D integer labels or one-hot encoded).
        """
        X = np.atleast_2d(np.asarray(X, dtype=float))

        # Convert 1D labels to one-hot
        if y.ndim == 1:
            self.classes_ = np.unique(y)
            n_classes = len(self.classes_)
            y_onehot = np.zeros((len(y), n_classes))
            for idx, label in enumerate(y):
                y_onehot[idx, label] = 1.0
        else:
            y_onehot = np.asarray(y, dtype=float)
            self.classes_ = np.arange(y_onehot.shape[1])

        self.n_classes_ = y_onehot.shape[1]

        # Ensure layer_dims[-1] matches n_classes
        if self.layer_dims[-1] != self.n_classes_:
            self.layer_dims = list(self.layer_dims[:-1]) + [self.n_classes_]

        self._init_params()
        self.losses_ = []

        for epoch in range(self.epochs):
            cache = self._forward(X)
            loss = self._cross_entropy(y_onehot, cache[f"A{len(self.layer_dims)-1}"])
            self.losses_.append(loss)

            grads = self._backward(cache, y_onehot)
            for key in self.params:
                self.params[key] -= self.lr * grads[key]

        return self

    def predict_proba(self, X):
        """Return class probabilities.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)

        Returns
        -------
        proba : ndarray, shape (n_samples, n_classes)
        """
        cache = self._forward(np.atleast_2d(np.asarray(X, dtype=float)))
        return cache[f"A{len(self.layer_dims)-1}"]

    def predict(self, X):
        """Return predicted class labels.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)

        Returns
        -------
        y_pred : ndarray, shape (n_samples,)
        """
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]
