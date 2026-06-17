"""
Recurrent Neural Networks — numpy only, no deep learning framework.

Classes
  RNN  — vanilla RNN with BPTT for character-level language modeling
  LSTM — LSTM with gating mechanism, same API

Both support: fit(text_indices, target_indices) → training,
sample(seed, n_chars, temp) → text generation.

References
  - Rumelhart et al. (1986). Learning representations by back-propagating errors.
  - Hochreiter & Schmidhuber (1997). Long Short-Term Memory.
  - Karpathy (2015). The Unreasonable Effectiveness of Recurrent Neural Networks.
"""
import numpy as np


class RNN:
    """Vanilla RNN with Backpropagation Through Time.

    Parameters
    ----------
    hidden_size : int
    lr : float
    seq_length : int  — truncated BPTT window
    """

    def __init__(self, hidden_size=100, lr=0.01, seq_length=25, random_state=42):
        self.hidden_size = hidden_size
        self.lr = lr
        self.seq_length = seq_length
        self.random_state = random_state
        self.losses_ = []
        self.vocab_size = None

    def _init_params(self, vocab_size):
        rng = np.random.RandomState(self.random_state)
        h = self.hidden_size
        v = vocab_size
        self.W_xh = rng.randn(h, v) * 0.01
        self.W_hh = rng.randn(h, h) * 0.01
        self.W_hy = rng.randn(v, h) * 0.01
        self.b_h = np.zeros((h, 1))
        self.b_y = np.zeros((v, 1))

    def forward(self, inputs, h_prev):
        """Unfold the RNN over seq_length steps.

        Parameters
        ----------
        inputs : list of int, length seq_length
        h_prev : ndarray (hidden_size, 1)

        Returns
        -------
        hs : dict of hidden states
        ps : dict of output probabilities
        cache : (xs, hs, ys, ps) for backward
        """
        xs, hs, ys, ps = {}, {}, {}, {}
        hs[-1] = np.copy(h_prev)
        for t in range(len(inputs)):
            xs[t] = np.zeros((self.vocab_size, 1))
            xs[t][inputs[t]] = 1.0
            hs[t] = np.tanh(self.W_xh @ xs[t] + self.W_hh @ hs[t - 1] + self.b_h)
            ys[t] = self.W_hy @ hs[t] + self.b_y
            y_shift = ys[t] - ys[t].max()
            ps[t] = np.exp(y_shift) / np.sum(np.exp(y_shift))
        return hs, ps, (xs, hs, ys, ps)

    def backward(self, targets, cache):
        """Backpropagation Through Time.

        Parameters
        ----------
        targets : list of int, length seq_length — target char indices
        cache : (xs, hs, ys, ps) from forward

        Returns
        -------
        h_next : ndarray (hidden_size, 1) — last hidden state
        """
        xs, hs, ys, ps = cache
        T = len(targets)
        dW_xh = np.zeros_like(self.W_xh)
        dW_hh = np.zeros_like(self.W_hh)
        dW_hy = np.zeros_like(self.W_hy)
        db_h = np.zeros_like(self.b_h)
        db_y = np.zeros_like(self.b_y)
        dh_next = np.zeros((self.hidden_size, 1))
        for t in reversed(range(T)):
            dy = np.copy(ps[t])
            dy[targets[t]] -= 1
            dW_hy += dy @ hs[t].T
            db_y += dy
            dh = self.W_hy.T @ dy + dh_next
            dh_raw = (1 - hs[t] * hs[t]) * dh
            db_h += dh_raw
            dW_xh += dh_raw @ xs[t].T
            dW_hh += dh_raw @ hs[t - 1].T
            dh_next = self.W_hh.T @ dh_raw
        for dparam in [dW_xh, dW_hh, dW_hy, db_h, db_y]:
            np.clip(dparam, -5, 5, out=dparam)
        self.W_xh -= self.lr * dW_xh
        self.W_hh -= self.lr * dW_hh
        self.W_hy -= self.lr * dW_hy
        self.b_h -= self.lr * db_h
        self.b_y -= self.lr * db_y
        return hs[T - 1]

    def fit(self, X, y, epochs=100, verbose=True):
        """Train the RNN.

        Parameters
        ----------
        X : ndarray (n_chars,) — character indices
        y : ndarray (n_chars,) — target indices (shifted by 1)
        epochs : int
        """
        n = len(X)
        self.vocab_size = int(X.max()) + 1
        self._init_params(self.vocab_size)
        self.losses_ = []
        n_batches = (n - 1) // self.seq_length
        for epoch in range(epochs):
            h = np.zeros((self.hidden_size, 1))
            epoch_loss = 0.0
            p = 0
            while p + self.seq_length + 1 < n:
                inputs = X[p:p + self.seq_length].tolist()
                targets = y[p:p + self.seq_length].tolist()
                p += self.seq_length
                hs, ps, cache = self.forward(inputs, h)
                loss = -np.mean([np.log(ps[t][targets[t], 0])
                                 for t in range(self.seq_length)])
                epoch_loss += loss
                h = self.backward(targets, cache)
            self.losses_.append(epoch_loss / n_batches)
            if verbose and epoch % max(1, epochs // 10) == 0:
                print(f'Epoch {epoch}/{epochs}, loss: {self.losses_[-1]:.4f}')
        return self

    # ── RNN-specific helpers ──

    def _step(self, x, h):
        """Single RNN step: x_t, h_{t-1} → h_t, y."""
        h = np.tanh(self.W_xh @ x + self.W_hh @ h + self.b_h)
        y = self.W_hy @ h + self.b_y
        return h, y

    def summary(self):
        """Print model architecture summary."""
        h = self.hidden_size
        v = self.vocab_size
        if v is None:
            print("Model not initialized yet. Call fit() first to set vocab_size.")
            return
        print(f"{'Weight':<25} {'Shape':<20} {'Params':<10}")
        print("-" * 55)
        for name, shape, params in [
            ("W_xh (input→hidden)", f"({h}, {v})", h * v),
            ("W_hh (hidden→hidden)", f"({h}, {h})", h * h),
            ("b_h", f"({h}, 1)", h),
            ("W_hy (hidden→output)", f"({v}, {h})", v * h),
            ("b_y", f"({v}, 1)", v)]:
            print(f"{name:<25} {shape:<20} {params:<10}")
        total = h * v + h * h + h + v * h + v
        print("-" * 55)
        print(f"{'Total params':<46} {total}")

    def predict(self, X):
        """Predict next character indices.

        Parameters
        ----------
        X : ndarray, shape (n_samples,) — character indices

        Returns
        -------
        preds : ndarray, shape (n_samples,) — predicted next char index
        """
        proba = self.predict_proba(X)
        return proba.argmax(axis=1)

    def predict_proba(self, X):
        """Return probability distribution for next char at each position.

        Parameters
        ----------
        X : ndarray, shape (n_samples,) — character indices

        Returns
        -------
        proba : ndarray, shape (n_samples, vocab_size)
        """
        X = np.atleast_1d(np.asarray(X, dtype=int))
        h = np.zeros((self.hidden_size, 1))
        proba_list = []
        for t in range(len(X)):
            x = np.zeros((self.vocab_size, 1))
            x[X[t]] = 1.0
            h, y = self._step(x, h)
            y_shift = y - y.max()
            p = np.exp(y_shift) / np.sum(np.exp(y_shift))
            proba_list.append(p.ravel())
        return np.array(proba_list)

    def sample(self, seed_idx, n_chars=200, temp=1.0):
        """Generate character indices from a seed.

        Parameters
        ----------
        seed_idx : int — starting character index
        n_chars : int
        temp : float — sampling temperature

        Returns
        -------
        indices : list of int, length n_chars + 1
        """
        h = np.zeros((self.hidden_size, 1))
        x = np.zeros((self.vocab_size, 1))
        x[seed_idx] = 1.0
        indices = [seed_idx]
        for _ in range(n_chars):
            h, y = self._step(x, h)
            y_shift = y - y.max()
            p = np.exp(y_shift / temp) / np.sum(np.exp(y_shift / temp))
            idx = np.random.choice(self.vocab_size, p=p.ravel())
            x = np.zeros((self.vocab_size, 1))
            x[idx] = 1.0
            indices.append(idx)
        return indices


class LSTM:
    """Long Short-Term Memory network.

    Parameters
    ----------
    hidden_size : int
    lr : float
    seq_length : int
    """

    def __init__(self, hidden_size=100, lr=0.01, seq_length=25, random_state=42):
        self.hidden_size = hidden_size
        self.lr = lr
        self.seq_length = seq_length
        self.random_state = random_state
        self.losses_ = []
        self.vocab_size = None

    def _init_params(self, vocab_size):
        rng = np.random.RandomState(self.random_state)
        h = self.hidden_size
        v = vocab_size

        def r(shape):
            return rng.randn(*shape) * 0.01

        self.W_f = r((h, h + v))
        self.W_i = r((h, h + v))
        self.W_c = r((h, h + v))
        self.W_o = r((h, h + v))
        self.b_f = np.ones((h, 1))  # forget gate bias = 1: keep info at init
        self.b_i = np.zeros((h, 1))
        self.b_c = np.zeros((h, 1))
        self.b_o = np.zeros((h, 1))
        self.W_hy = r((v, h))
        self.b_y = np.zeros((v, 1))

    @staticmethod
    def _sigmoid(x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -100, 100)))

    def forward(self, inputs, h_prev, c_prev):
        """Unfold the LSTM over seq_length steps.

        Returns
        -------
        hs : dict of hidden states
        cs : dict of cell states
        ps : dict of output probabilities
        cache : tuple for backward
        """
        xs, hs, cs, ys, ps = {}, {}, {}, {}, {}
        hs[-1] = np.copy(h_prev)
        cs[-1] = np.copy(c_prev)
        gates = {}
        for t in range(len(inputs)):
            xs[t] = np.zeros((self.vocab_size, 1))
            xs[t][inputs[t]] = 1.0
            z = np.vstack([hs[t - 1], xs[t]])
            f = self._sigmoid(self.W_f @ z + self.b_f)
            i = self._sigmoid(self.W_i @ z + self.b_i)
            c_hat = np.tanh(self.W_c @ z + self.b_c)
            o = self._sigmoid(self.W_o @ z + self.b_o)
            cs[t] = f * cs[t - 1] + i * c_hat
            hs[t] = o * np.tanh(cs[t])
            ys[t] = self.W_hy @ hs[t] + self.b_y
            y_shift = ys[t] - ys[t].max()
            ps[t] = np.exp(y_shift) / np.sum(np.exp(y_shift))
            gates[t] = (f, i, c_hat, o, z)
        return hs, cs, ps, (xs, hs, cs, ys, ps, gates)

    def backward(self, targets, cache):
        """BPTT for LSTM."""
        xs, hs, cs, ys, ps, gates = cache
        T = len(targets)
        h = self.hidden_size
        dW_f = np.zeros_like(self.W_f)
        dW_i = np.zeros_like(self.W_i)
        dW_c = np.zeros_like(self.W_c)
        dW_o = np.zeros_like(self.W_o)
        db_f = np.zeros_like(self.b_f)
        db_i = np.zeros_like(self.b_i)
        db_c = np.zeros_like(self.b_c)
        db_o = np.zeros_like(self.b_o)
        dW_hy = np.zeros_like(self.W_hy)
        db_y = np.zeros_like(self.b_y)
        dh_next = np.zeros((h, 1))
        dc_next = np.zeros((h, 1))
        for t in reversed(range(T)):
            dy = np.copy(ps[t])
            dy[targets[t]] -= 1
            dW_hy += dy @ hs[t].T
            db_y += dy
            dh = self.W_hy.T @ dy + dh_next
            f, i, c_hat, o, z = gates[t]
            do = dh * np.tanh(cs[t])
            dc = dh * o * (1 - np.tanh(cs[t]) ** 2) + dc_next
            df = dc * cs[t - 1]
            di = dc * c_hat
            dc_hat = dc * i
            df_raw = f * (1 - f) * df
            di_raw = i * (1 - i) * di
            dc_hat_raw = (1 - c_hat ** 2) * dc_hat
            do_raw = o * (1 - o) * do
            dW_f += df_raw @ z.T
            dW_i += di_raw @ z.T
            dW_c += dc_hat_raw @ z.T
            dW_o += do_raw @ z.T
            db_f += df_raw
            db_i += di_raw
            db_c += dc_hat_raw
            db_o += do_raw
            dz = (self.W_f.T @ df_raw + self.W_i.T @ di_raw
                  + self.W_c.T @ dc_hat_raw + self.W_o.T @ do_raw)
            dh_next = dz[:h]
            dc_next = f * dc
        for dparam in [dW_f, dW_i, dW_c, dW_o, dW_hy, db_f, db_i, db_c, db_o, db_y]:
            np.clip(dparam, -5, 5, out=dparam)
        self.W_f -= self.lr * dW_f
        self.W_i -= self.lr * dW_i
        self.W_c -= self.lr * dW_c
        self.W_o -= self.lr * dW_o
        self.W_hy -= self.lr * dW_hy
        self.b_f -= self.lr * db_f
        self.b_i -= self.lr * db_i
        self.b_c -= self.lr * db_c
        self.b_o -= self.lr * db_o
        self.b_y -= self.lr * db_y
        return hs[T - 1], cs[T - 1]

    def fit(self, X, y, epochs=100, verbose=True):
        """Train the LSTM."""
        n = len(X)
        self.vocab_size = int(X.max()) + 1
        self._init_params(self.vocab_size)
        self.losses_ = []
        n_batches = (n - 1) // self.seq_length
        for epoch in range(epochs):
            h = np.zeros((self.hidden_size, 1))
            c = np.zeros((self.hidden_size, 1))
            epoch_loss = 0.0
            p = 0
            while p + self.seq_length + 1 < n:
                inputs = X[p:p + self.seq_length].tolist()
                targets = y[p:p + self.seq_length].tolist()
                p += self.seq_length
                hs, cs, ps, cache = self.forward(inputs, h, c)
                loss = -np.mean([np.log(ps[t][targets[t], 0])
                                 for t in range(self.seq_length)])
                epoch_loss += loss
                h, c = self.backward(targets, cache)
            self.losses_.append(epoch_loss / n_batches)
            if verbose and epoch % max(1, epochs // 10) == 0:
                print(f'Epoch {epoch}/{epochs}, loss: {self.losses_[-1]:.4f}')
        return self

    # ── LSTM-specific helpers ──

    def _step(self, x, h, c):
        """Single LSTM step: x_t, h_{t-1}, c_{t-1} → h_t, c_t, y."""
        z = np.vstack([h, x])
        f = self._sigmoid(self.W_f @ z + self.b_f)
        i = self._sigmoid(self.W_i @ z + self.b_i)
        c_hat = np.tanh(self.W_c @ z + self.b_c)
        o = self._sigmoid(self.W_o @ z + self.b_o)
        c = f * c + i * c_hat
        h = o * np.tanh(c)
        y = self.W_hy @ h + self.b_y
        return h, c, y

    def summary(self):
        """Print model architecture summary."""
        v = self.vocab_size or "?"
        h = self.hidden_size
        print(f"{'Weight':<25} {'Shape':<20} {'Params':<10}")
        print("-" * 55)
        for name, shape, params in [
            ("W_f (forget gate)", f"({h}, {h+v})", h * (h + v)),
            ("W_i (input gate)", f"({h}, {h+v})", h * (h + v)),
            ("W_c (candidate)", f"({h}, {h+v})", h * (h + v)),
            ("W_o (output gate)", f"({h}, {h+v})", h * (h + v)),
            ("b_f/b_i/b_c/b_o", f"({h}, 1) x4", h * 4),
            ("W_hy (hidden→output)", f"({v}, {h})", v * h),
            ("b_y", f"({v}, 1)", v)]:
            print(f"{name:<25} {shape:<20} {params:<10}")
        total = 4 * h * (h + v) + 4 * h + v * h + v
        print("-" * 55)
        print(f"{'Total params':<46} {total}")

    def predict(self, X):
        """Predict next character indices."""
        proba = self.predict_proba(X)
        return proba.argmax(axis=1)

    def predict_proba(self, X):
        """Return probability distribution for next char at each position."""
        X = np.atleast_1d(np.asarray(X, dtype=int))
        h = np.zeros((self.hidden_size, 1))
        c = np.zeros((self.hidden_size, 1))
        proba_list = []
        for t in range(len(X)):
            x = np.zeros((self.vocab_size, 1))
            x[X[t]] = 1.0
            h, c, y = self._step(x, h, c)
            y_shift = y - y.max()
            p = np.exp(y_shift) / np.sum(np.exp(y_shift))
            proba_list.append(p.ravel())
        return np.array(proba_list)

    def sample(self, seed_idx, n_chars=200, temp=1.0):
        """Generate character indices from a seed."""
        h = np.zeros((self.hidden_size, 1))
        c = np.zeros((self.hidden_size, 1))
        x = np.zeros((self.vocab_size, 1))
        x[seed_idx] = 1.0
        indices = [seed_idx]
        for _ in range(n_chars):
            h, c, y = self._step(x, h, c)
            y_shift = y - y.max()
            p = np.exp(y_shift / temp) / np.sum(np.exp(y_shift / temp))
            idx = np.random.choice(self.vocab_size, p=p.ravel())
            x = np.zeros((self.vocab_size, 1))
            x[idx] = 1.0
            indices.append(idx)
        return indices
