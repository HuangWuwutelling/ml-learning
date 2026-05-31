"""
Convolutional Neural Network — numpy only, no deep learning framework.

Architecture
  Conv → ReLU → Pool → Conv → ReLU → Pool → Flatten → Dense → ReLU → Dense → Softmax

Key technique: im2col for efficient convolution (unfolds image patches into
matrix columns, then uses GEMM for the actual computation).

References
  - LeCun et al. (1998). Gradient-based learning applied to document recognition.
  - CS231n: Convolutional Neural Networks for Visual Recognition.
"""
import numpy as np


# ── im2col / col2im helpers ───────────────────────────────

def im2col(X, k_size, pad, stride=1):
    """Unfold image patches into column vectors.

    Parameters
    ----------
    X : ndarray, shape (N, C, H, W)
    k_size : int
    pad : int
    stride : int

    Returns
    -------
    col : ndarray, shape (C * k_size^2, N * out_H * out_W)
    """
    N, C, H, W = X.shape
    out_H = (H + 2 * pad - k_size) // stride + 1
    out_W = (W + 2 * pad - k_size) // stride + 1

    X_pad = np.pad(X, ((0, 0), (0, 0), (pad, pad), (pad, pad)), mode='constant')

    col = np.zeros((N, C, k_size, k_size, out_H, out_W))
    for i in range(k_size):
        i_end = i + out_H * stride
        for j in range(k_size):
            j_end = j + out_W * stride
            col[:, :, i, j, :, :] = X_pad[:, :, i:i_end:stride, j:j_end:stride]

    return col.reshape(N, -1, out_H * out_W).transpose(1, 0, 2).reshape(-1, N * out_H * out_W)


def col2im(dcol, X_shape, k_size, pad, stride=1):
    """Reverse of im2col — distribute column gradients back to image.

    Parameters
    ----------
    dcol : ndarray, shape (C * k_size^2, N * out_H * out_W)
    X_shape : tuple (N, C, H, W)
    k_size, pad, stride : same as im2col

    Returns
    -------
    dX : ndarray, shape (N, C, H, W)
    """
    N, C, H, W = X_shape
    out_H = (H + 2 * pad - k_size) // stride + 1
    out_W = (W + 2 * pad - k_size) // stride + 1

    dcol = dcol.reshape(C * k_size * k_size, N, out_H * out_W)
    dcol = dcol.transpose(1, 0, 2).reshape(N, C, k_size, k_size, out_H, out_W)

    dX_pad = np.zeros((N, C, H + 2 * pad, W + 2 * pad))
    for i in range(k_size):
        i_end = i + out_H * stride
        for j in range(k_size):
            j_end = j + out_W * stride
            dX_pad[:, :, i:i_end:stride, j:j_end:stride] += dcol[:, :, i, j, :, :]

    return dX_pad[:, :, pad:-pad, pad:-pad] if pad > 0 else dX_pad


# ── Layer classes ─────────────────────────────────────────

class Conv2D:
    """2D convolution layer (im2col-based)."""
    def __init__(self, in_channels, out_channels, k_size=3, pad=0, stride=1, seed=42):
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.k_size = k_size
        self.pad = pad
        self.stride = stride

        # He init (recommended for ReLU)
        self.W = None
        self.b = None
        self._init_params(seed)

    def _init_params(self, seed):
        rng = np.random.RandomState(seed)
        fan_in = self.in_channels * self.k_size * self.k_size
        limit = np.sqrt(2 / fan_in)
        self.W = rng.uniform(-limit, limit,
                             (self.out_channels, self.in_channels, self.k_size, self.k_size))
        self.b = np.zeros((1, self.out_channels, 1, 1))

    def forward(self, X):
        """X: (N, C_in, H, W) → out: (N, C_out, H_out, W_out)"""
        self.X = X
        N, C, H, W = X.shape
        out_H = (H + 2 * self.pad - self.k_size) // self.stride + 1
        out_W = (W + 2 * self.pad - self.k_size) // self.stride + 1

        col = im2col(X, self.k_size, self.pad, self.stride)                     # (C*k^2, N*OH*OW)
        W_flat = self.W.reshape(self.out_channels, -1)                           # (C_out, C_in*k^2)

        out = W_flat @ col                                                       # (C_out, N*OH*OW)
        out = out.reshape(self.out_channels, N, out_H, out_W).transpose(1, 0, 2, 3)
        out += self.b
        return out

    def backward(self, dout, lr):
        """dout: (N, C_out, H_out, W_out)"""
        N = self.X.shape[0]
        out_H, out_W = dout.shape[2], dout.shape[3]

        # dout → (C_out, N*OH*OW)
        dout_reshaped = dout.transpose(1, 0, 2, 3).reshape(self.out_channels, -1)

        col = im2col(self.X, self.k_size, self.pad, self.stride)                 # (C_in*k^2, N*OH*OW)

        # dW = dout @ col.T → (C_out, C_in*k^2)
        dW = (dout_reshaped @ col.T).reshape(self.W.shape)
        dW /= N

        # db = sum dout over N, H, W
        db = dout.sum(axis=(0, 2, 3), keepdims=True) / N

        # dX: col2im(W.T @ dout)
        W_flat = self.W.reshape(self.out_channels, -1)                           # (C_out, C_in*k^2)
        dcol = W_flat.T @ dout_reshaped                                          # (C_in*k^2, N*OH*OW)
        dX = col2im(dcol, self.X.shape, self.k_size, self.pad, self.stride)

        # Update
        self.W -= lr * dW
        self.b -= lr * db

        return dX


class MaxPool2D:
    """Max pooling layer."""
    def __init__(self, pool_size=2, stride=2):
        self.pool_size = pool_size
        self.stride = stride

    def forward(self, X):
        """X: (N, C, H, W) → out: (N, C, H_out, W_out)"""
        self.X = X
        N, C, H, W = X.shape
        out_H = (H - self.pool_size) // self.stride + 1
        out_W = (W - self.pool_size) // self.stride + 1

        # Unfold windows
        col = im2col(X, self.pool_size, pad=0, stride=self.stride)  # (C*P^2, N*OH*OW)
        col = col.reshape(C, self.pool_size * self.pool_size, N * out_H * out_W)

        # Max across each window
        max_idx = col.argmax(axis=1)                                 # (C, N*OH*OW)
        out = col.max(axis=1)                                        # (C, N*OH*OW)

        self.max_idx = max_idx
        self.out_shape = (N, C, out_H, out_W)
        return out.reshape(C, N, out_H, out_W).transpose(1, 0, 2, 3)

    def backward(self, dout, lr=None):
        """dout: (N, C, H_out, W_out) → dX: (N, C, H_in, W_in)"""
        N, C, out_H, out_W = dout.shape
        dout_flat = dout.transpose(1, 0, 2, 3).reshape(C, -1)       # (C, N*OH*OW)

        # One-hot mask for max positions
        dcol = np.zeros((C, self.pool_size * self.pool_size, N * out_H * out_W))
        dcol[np.arange(C)[:, None], self.max_idx, np.arange(N * out_H * out_W)[None, :]] = dout_flat

        dcol = dcol.reshape(C * self.pool_size * self.pool_size, N * out_H * out_W)
        dX = col2im(dcol, self.X.shape, self.pool_size, pad=0, stride=self.stride)
        return dX


class Flatten:
    """Flatten (N, C, H, W) → (N, C*H*W)."""
    def forward(self, X):
        self.input_shape = X.shape
        return X.reshape(X.shape[0], -1)

    def backward(self, dout, lr=None):
        return dout.reshape(self.input_shape)


class Dense:
    """Fully-connected layer (no activation — applied separately)."""
    def __init__(self, in_features, out_features, seed=42):
        self.in_features = in_features
        self.out_features = out_features

        # Xavier init
        self.W = None
        self.b = None
        self._init_params(seed)

    def _init_params(self, seed):
        rng = np.random.RandomState(seed)
        limit = np.sqrt(6 / (self.in_features + self.out_features))
        self.W = rng.uniform(-limit, limit, (self.in_features, self.out_features))
        self.b = np.zeros((1, self.out_features))

    def forward(self, X):
        """X: (N, in_features) → out: (N, out_features)"""
        self.X = X
        return X @ self.W + self.b

    def backward(self, dout, lr):
        """dout: (N, out_features) → dX: (N, in_features)"""
        m = dout.shape[0]
        dW = self.X.T @ dout / m
        db = dout.sum(axis=0, keepdims=True) / m
        dX = dout @ self.W.T

        self.W -= lr * dW
        self.b -= lr * db
        return dX


class ReLU:
    """ReLU activation."""
    def forward(self, X):
        self.mask = X > 0
        return np.maximum(0, X)

    def backward(self, dout, lr=None):
        return dout * self.mask


# ── CNN model ─────────────────────────────────────────────

class CNN:
    """Convolutional Neural Network for image classification.

    Parameters
    ----------
    epochs : int
    lr : float
    random_state : int
    """

    def __init__(self, epochs=10, lr=0.01, random_state=42):
        self.epochs = epochs
        self.lr = lr
        self.random_state = random_state
        self.layers = []
        self.losses_ = []

    def _build(self, H, W, n_classes):
        """Construct the layer graph.

        Assumes two Conv+Pool blocks with stride 2 pooling:
        after two 2x2 pools, spatial dims are H/4 × W/4.
        """
        s = self.random_state
        self.layers = [
            Conv2D(1, 8, k_size=3, pad=1, seed=s),
            ReLU(),
            MaxPool2D(2, 2),
            Conv2D(8, 16, k_size=3, pad=1, seed=s + 1),
            ReLU(),
            MaxPool2D(2, 2),
            Flatten(),
            Dense((H // 4) * (W // 4) * 16, 128, seed=s + 2),
            ReLU(),
            Dense(128, n_classes, seed=s + 3),
        ]

    def _softmax(self, Z):
        """Stable softmax."""
        shifted = Z - Z.max(axis=1, keepdims=True)
        exp_z = np.exp(shifted)
        return exp_z / exp_z.sum(axis=1, keepdims=True)

    def _cross_entropy(self, y_true, y_pred):
        return -np.mean(np.sum(y_true * np.log(y_pred + 1e-8), axis=1))

    def fit(self, X, y):
        """Train the CNN.

        Parameters
        ----------
        X : ndarray, shape (n_samples, 784) or (n_samples, 28, 28)
            MNIST-style flattened or 2D images.
        y : ndarray, shape (n_samples,)
            Integer labels.
        """
        X = np.atleast_2d(np.asarray(X, dtype=float))

        # Reshape to (N, 1, H, W)
        if X.ndim == 2:
            side = int(np.sqrt(X.shape[1]))
            X = X.reshape(-1, 1, side, side)

        _, _, H, W = X.shape

        # One-hot labels (assume classes 0..n-1)
        n_classes = int(y.max()) + 1
        self.classes_ = np.arange(n_classes)
        y_onehot = np.zeros((len(y), n_classes))
        for idx, label in enumerate(y):
            y_onehot[idx, int(label)] = 1.0

        self._build(H, W, n_classes)
        self.losses_ = []

        for epoch in range(self.epochs):
            # Forward
            out = X
            for layer in self.layers:
                out = layer.forward(out)

            # Softmax + loss
            proba = self._softmax(out)
            loss = self._cross_entropy(y_onehot, proba)
            self.losses_.append(loss)

            # Backward: dL/dZ = proba - y (softmax + cross-entropy gradient)
            dout = proba - y_onehot
            for layer in reversed(self.layers):
                dout = layer.backward(dout, self.lr)

        return self

    def predict_proba(self, X):
        """Return class probabilities."""
        X = np.atleast_2d(np.asarray(X, dtype=float))
        if X.ndim == 2:
            side = int(np.sqrt(X.shape[1]))
            X = X.reshape(-1, 1, side, side)

        out = X
        for layer in self.layers:
            out = layer.forward(out)
        return self._softmax(out)

    def predict(self, X):
        """Return predicted class labels."""
        proba = self.predict_proba(X)
        return self.classes_[np.argmax(proba, axis=1)]
