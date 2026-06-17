"""
AutoEncoder — unsupervised neural network for dimensionality reduction.

Architecture (Encoder → Decoder):
  Input → [Linear + ReLU] → Bottleneck (linear) → [Linear + ReLU] → Output (Sigmoid)

The network is trained to reconstruct its input by passing it through a narrow
bottleneck layer, forcing it to learn a compressed representation.

References
  - Rumelhart, Hinton, Williams (1986). Learning internal representations
    by error propagation. (Parallel Distributed Processing, Vol. 1.)
  - Hinton & Salakhutdinov (2006). Reducing the dimensionality of data with
    neural networks. Science, 313(5786), 504-507.
"""
import numpy as np


class AutoEncoder:
    """Fully-connected autoencoder for unsupervised representation learning.

    Parameters
    ----------
    input_dim : int
        Dimensionality of the input data.
    encoding_dim : int
        Dimensionality of the bottleneck (latent) layer.
    hidden_dim : int
        Number of units in the encoder and decoder hidden layers.
    lr : float
        Learning rate for gradient descent.
    epochs : int
        Number of passes over the training data.
    random_state : int
        Seed for weight initialization.
    """

    def __init__(self, input_dim, encoding_dim=3, hidden_dim=32,
                 lr=0.01, epochs=200, random_state=42):
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.hidden_dim = hidden_dim
        self.lr = lr
        self.epochs = epochs
        self.random_state = random_state
        self.rng = np.random.RandomState(random_state)
        self.params = {}
        self.losses_ = []

        # Architecture:
        #   input -> hidden(ReLU) -> bottleneck(linear) -> hidden(ReLU) -> output(Sigmoid)
        self.layer_dims = [input_dim, hidden_dim, encoding_dim, hidden_dim, input_dim]
        self._init_params()

    # ── Activations ────────────────────────────────────────

    @staticmethod
    def _relu(Z):
        return np.maximum(0, Z)

    @staticmethod
    def _relu_derivative(Z):
        return (Z > 0).astype(float)

    @staticmethod
    def _sigmoid(Z):
        Z = np.clip(Z, -500, 500)
        return 1.0 / (1.0 + np.exp(-Z))

    @staticmethod
    def _sigmoid_derivative(A):
        return A * (1.0 - A)

    # ── Initialization ─────────────────────────────────────

    def _init_params(self):
        """Xavier (Glorot) uniform initialization for all layers."""
        L = len(self.layer_dims) - 1
        for i in range(1, L + 1):
            fan_in = self.layer_dims[i - 1]
            fan_out = self.layer_dims[i]
            scale = np.sqrt(6.0 / (fan_in + fan_out))
            self.params[f'W{i}'] = self.rng.uniform(-scale, scale, (fan_in, fan_out))
            self.params[f'b{i}'] = np.zeros((1, fan_out))

    # ── Forward ────────────────────────────────────────────

    def _forward(self, X):
        """Full forward pass: encoder + decoder.

        Architecture indices (L = 4 transformations over 5 layers):
            Layer 1 (i=1): input_dim  -> hidden_dim   [ReLU]
            Layer 2 (i=2): hidden_dim -> encoding_dim  [linear / bottleneck]
            Layer 3 (i=3): encoding_dim -> hidden_dim  [ReLU]
            Layer 4 (i=4): hidden_dim -> input_dim     [Sigmoid / output]

        Returns
        -------
        cache : dict with A0, Z1, A1, ..., Z4, A4
        """
        cache = {'A0': X}
        L = len(self.layer_dims) - 1  # = 4

        for i in range(1, L + 1):
            A_prev = cache[f'A{i - 1}']
            Z = A_prev @ self.params[f'W{i}'] + self.params[f'b{i}']
            cache[f'Z{i}'] = Z

            if i == L:                      # output layer: Sigmoid
                cache[f'A{i}'] = self._sigmoid(Z)
            elif i == 2:                    # bottleneck: linear (no activation)
                cache[f'A{i}'] = Z
            else:                           # hidden layers: ReLU
                cache[f'A{i}'] = self._relu(Z)

        return cache

    # ── Backward ───────────────────────────────────────────

    def _backward(self, cache, X):
        """Backpropagation for MSE reconstruction loss.

        Loss:  L = (1 / 2m) * Σ (X - A_out)²

        Returns
        -------
        grads : dict with W1, b1, ..., W4, b4
        """
        m = X.shape[0]
        L = len(self.layer_dims) - 1
        grads = {}

        # Output layer: dL/dA_out = (A_out - X) / m
        A_out = cache[f'A{L}']
        dA = (A_out - X) / m

        for i in range(L, 0, -1):
            if i == L:                      # Sigmoid output
                dZ = dA * self._sigmoid_derivative(cache[f'A{i}'])
            elif i == 2:                    # Bottleneck (linear)
                dZ = dA
            else:                           # ReLU hidden
                dZ = dA * self._relu_derivative(cache[f'Z{i}'])

            grads[f'W{i}'] = cache[f'A{i - 1}'].T @ dZ
            grads[f'b{i}'] = dZ.sum(axis=0, keepdims=True)

            # Propagate gradient to the previous layer
            if i > 1:
                dA = dZ @ self.params[f'W{i}'].T

        return grads

    @staticmethod
    def _mse_loss(X, X_recon):
        """Per-sample MSE averaged over the batch, scaled by 0.5.

        L = 0.5 * (1/m) * sum_i ||X_i - X_recon_i||^2
        dL/dA = (A - X) / m   (consistent with _backward)
        """
        return 0.5 * np.sum((X - X_recon) ** 2) / X.shape[0]

    # ── Public API ─────────────────────────────────────────

    def fit(self, X):
        """Train the autoencoder to reconstruct input X.

        The same data is used as both input and reconstruction target
        (unsupervised learning).

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)
            Training data. Should be normalized to [0, 1] when using
            the default sigmoid output.
        """
        X = np.atleast_2d(np.asarray(X, dtype=float))
        self.losses_ = []

        for _ in range(self.epochs):
            cache = self._forward(X)
            loss = self._mse_loss(X, cache[f'A{len(self.layer_dims) - 1}'])
            self.losses_.append(loss)

            grads = self._backward(cache, X)
            for key in self.params:
                self.params[key] -= self.lr * grads[key]

        return self

    def encode(self, X):
        """Compress data to latent (bottleneck) representation.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)

        Returns
        -------
        Z : ndarray, shape (n_samples, encoding_dim)
        """
        X = np.atleast_2d(np.asarray(X, dtype=float))
        # Run only the encoder part: layers 1 (ReLU) and 2 (linear)
        A1 = self._relu(X @ self.params['W1'] + self.params['b1'])
        Z = A1 @ self.params['W2'] + self.params['b2']
        return Z

    def decode(self, Z):
        """Reconstruct data from latent representation.

        Parameters
        ----------
        Z : ndarray, shape (n_samples, encoding_dim)

        Returns
        -------
        X_recon : ndarray, shape (n_samples, input_dim)
        """
        Z = np.atleast_2d(np.asarray(Z, dtype=float))
        # Run the decoder part: layers 3 (ReLU) and 4 (Sigmoid)
        A3 = self._relu(Z @ self.params['W3'] + self.params['b3'])
        X_recon = self._sigmoid(A3 @ self.params['W4'] + self.params['b4'])
        return X_recon

    def reconstruct(self, X):
        """Full pipeline: encode then decode.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_features)

        Returns
        -------
        X_recon : ndarray, shape (n_samples, n_features)
        """
        return self.decode(self.encode(X))
