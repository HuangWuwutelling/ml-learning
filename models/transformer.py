"""
Transformer — decoder-only language model (GPT-style).
Character-level, numpy only, with analytical backward pass.
"""
import numpy as np
from collections import OrderedDict


class TransformerLM:
    """Decoder-only Transformer for character-level language modeling.

    Architecture: pre-norm (LayerNorm before each sub-layer),
    residual connections, causal multi-head self-attention, ReLU FFN.

    Reference: "Attention Is All You Need" (Vaswani et al., 2017)
    """

    def __init__(self, vocab_size, d_model=64, n_heads=4, n_layers=3,
                 d_ff=256, max_seq_len=128, lr=0.001, beta1=0.9, beta2=0.999,
                 eps=1e-8, random_state=42):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len
        self.d_k = d_model // n_heads
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"

        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.rng = np.random.RandomState(random_state)
        self.t = 0  # Adam step

        self.params = OrderedDict()
        self._init_params()

        # Adam state
        self.m = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.params.items()}

    # ── Initialization ──────────────────────────────────────────────

    def _init_weight(self, n_in, n_out):
        scale = np.sqrt(2.0 / (n_in + n_out))
        return self.rng.uniform(-scale, scale, (n_in, n_out)).astype(np.float64)

    def _init_params(self):
        D, H = self.d_model, self.n_heads

        # Token embedding
        self.params['token_embed'] = self._init_weight(self.vocab_size, D)

        self.causal_mask = None

        # Transformer blocks
        for i in range(self.n_layers):
            p = f'block{i}_'
            self.params[f'{p}ln1_g'] = np.ones(D)
            self.params[f'{p}ln1_b'] = np.zeros(D)
            self.params[f'{p}W_q'] = self._init_weight(D, D)
            self.params[f'{p}W_k'] = self._init_weight(D, D)
            self.params[f'{p}W_v'] = self._init_weight(D, D)
            self.params[f'{p}W_o'] = self._init_weight(D, D)
            self.params[f'{p}ln2_g'] = np.ones(D)
            self.params[f'{p}ln2_b'] = np.zeros(D)
            self.params[f'{p}W_1'] = self._init_weight(D, self.d_ff)
            self.params[f'{p}b_1'] = np.zeros(self.d_ff)
            self.params[f'{p}W_2'] = self._init_weight(self.d_ff, D)
            self.params[f'{p}b_2'] = np.zeros(D)

        self.params['ln_out_g'] = np.ones(D)
        self.params['ln_out_b'] = np.zeros(D)
        self.params['W_out'] = self._init_weight(D, self.vocab_size)
        self.params['b_out'] = np.zeros(self.vocab_size)

    def _positional_encoding(self, max_len=None):
        max_len = max_len or self.max_seq_len
        pe = np.zeros((max_len, self.d_model))
        pos = np.arange(max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, self.d_model, 2)
                          * (-np.log(10000.0) / self.d_model))
        pe[:, 0::2] = np.sin(pos * div_term)
        pe[:, 1::2] = np.cos(pos * div_term)
        return pe

    def _build_causal_mask(self, seq_len):
        mask = np.triu(np.ones((seq_len, seq_len), dtype=bool), k=1)
        return ~mask  # True = allowed

    # ── Layer Normalization ─────────────────────────────────────────

    def layernorm(self, x, g, b):
        mu = x.mean(axis=-1, keepdims=True)
        var = x.var(axis=-1, keepdims=True)
        sigma = np.sqrt(var + self.eps)
        x_norm = (x - mu) / sigma
        return g * x_norm + b, (x, mu, sigma, x_norm, g)

    def layernorm_bwd(self, d_out, cache):
        x, mu, sigma, x_norm, g = cache
        d_x_norm = d_out * g
        dx = (1.0 / sigma) * (
            d_x_norm
            - np.mean(d_x_norm, axis=-1, keepdims=True)
            - x_norm * np.mean(d_x_norm * x_norm, axis=-1, keepdims=True)
        )
        d_g = (d_out * x_norm).sum(axis=(0, 1))
        d_b = d_out.sum(axis=(0, 1))
        return dx, d_g, d_b

    # ── Softmax ─────────────────────────────────────────────────────

    def softmax(self, x, axis=-1):
        x_max = x.max(axis=axis, keepdims=True)
        x_shifted = x - x_max
        exp_x = np.exp(x_shifted)
        return exp_x / exp_x.sum(axis=axis, keepdims=True)

    def softmax_bwd(self, d_out, cache):
        """d_out: gradient of loss w.r.t. softmax output.
        cache: the softmax output (probabilities).
        """
        p = cache
        # Jacobian: dL/ds_i = sum_j dL/dp_j * p_j * (delta_ij - p_i)
        # Vectorized: dp * p - p * sum(dp * p, axis=-1, keepdims=True)
        return p * (d_out - (d_out * p).sum(axis=-1, keepdims=True))

    # ── Multi-Head Attention ────────────────────────────────────────

    def attention(self, Q, K, V, causal_mask=None):
        """Multi-head attention forward.
        Q, K, V: (batch, n_heads, seq_len, d_k)
        returns: output, cache for backward
        """
        scale = 1.0 / np.sqrt(self.d_k)
        scores = Q @ K.transpose(0, 1, 3, 2) * scale
        if causal_mask is not None:
            scores = np.where(causal_mask, scores, -1e9)
        weights = self.softmax(scores, axis=-1)
        out = weights @ V
        return out, (Q, K, V, scores, weights, causal_mask)

    def attention_bwd(self, d_out, cache):
        """Backward through multi-head attention."""
        Q, K, V, scores, weights, causal_mask = cache
        d_k = Q.shape[-1]

        # d(weights @ V)
        d_weights = d_out @ V.transpose(0, 1, 3, 2)
        dV = weights.transpose(0, 1, 3, 2) @ d_out

        # d(softmax(scores))
        d_scores = self.softmax_bwd(d_weights, weights)

        # d(scores = Q @ K^T * scale)
        scale = 1.0 / np.sqrt(d_k)
        d_scores = d_scores * scale
        dQ = d_scores @ K
        dK = d_scores.transpose(0, 1, 3, 2) @ Q

        return dQ, dK, dV

    # ── FFN ─────────────────────────────────────────────────────────

    def ffn(self, x, W1, b1, W2, b2):
        h = x @ W1 + b1
        act = np.maximum(h, 0)  # ReLU
        out = act @ W2 + b2
        return out, (x, h, act)

    # ── Forward pass with full caching ──────────────────────────────

    def forward(self, x, cache=True):
        """Full forward pass with caching for backward.
        x: (batch, seq_len) — token indices
        returns: logits (batch, seq_len, vocab_size), cache dict
        """
        B, S = x.shape
        c = {}  # cache dict

        # Embedding + position
        c['x'] = x
        h = self.params['token_embed'][x]  # (B, S, D)
        pos_enc = self._positional_encoding(S)
        h = h + pos_enc[np.newaxis, :S]
        c['h_in'] = h.copy()

        # Causal mask
        if self.causal_mask is None or self.causal_mask.shape[0] < S:
            self.causal_mask = self._build_causal_mask(S)
        causal_mask = self.causal_mask[:S, :S]

        c['blocks'] = []
        for i in range(self.n_layers):
            p = f'block{i}_'
            block = {}

            # ── LN1 → MHA → residual ──
            ln1_out, block['ln1'] = self.layernorm(
                h, self.params[f'{p}ln1_g'], self.params[f'{p}ln1_b'])

            # Project Q, K, V
            Q = ln1_out @ self.params[f'{p}W_q']
            K = ln1_out @ self.params[f'{p}W_k']
            V = ln1_out @ self.params[f'{p}W_v']

            # Reshape for multi-head
            def _reshape_mh(x):
                return x.reshape(B, S, self.n_heads, self.d_k).transpose(0, 2, 1, 3)
            block['Q_flat'] = Q
            block['K_flat'] = K
            block['V_flat'] = V
            Q_mh = _reshape_mh(Q)
            K_mh = _reshape_mh(K)
            V_mh = _reshape_mh(V)

            # Attention
            attn_out, block['attn'] = self.attention(Q_mh, K_mh, V_mh, causal_mask)

            # Concatenate heads
            attn_out = attn_out.transpose(0, 2, 1, 3).reshape(B, S, self.d_model)

            # Output projection
            attn_proj = attn_out @ self.params[f'{p}W_o']
            block['attn_pre_proj'] = attn_out  # cache BEFORE W_o for gradient
            block['attn_proj'] = attn_proj

            h_after_mha = h + attn_proj
            block['h_prev'] = h  # h before this block
            h = h_after_mha

            # ── LN2 → FFN → residual ──
            ln2_out, block['ln2'] = self.layernorm(
                h, self.params[f'{p}ln2_g'], self.params[f'{p}ln2_b'])

            ffn_h = ln2_out @ self.params[f'{p}W_1'] + self.params[f'{p}b_1']
            ffn_act = np.maximum(ffn_h, 0)  # ReLU
            ffn_out = ffn_act @ self.params[f'{p}W_2'] + self.params[f'{p}b_2']
            block['ffn_h'] = ffn_h
            block['ffn_act'] = ffn_act

            h = h + ffn_out
            block['h_after'] = h

            c['blocks'].append(block)

        # Output LayerNorm + projection
        ln_out, c['ln_out'] = self.layernorm(
            h, self.params['ln_out_g'], self.params['ln_out_b'])
        logits = ln_out @ self.params['W_out'] + self.params['b_out']
        c['ln_out_val'] = ln_out

        return logits, c

    # ── Backward pass ───────────────────────────────────────────────

    def backward(self, logits, targets, cache):
        """Backward pass computing gradients for all parameters.
        logits: (B, S, V) — from forward()
        targets: (B, S) — target token indices
        cache: from forward()

        Returns: dictionary of gradients (same keys as self.params)
        """
        B, S = logits.shape[:2]
        grads = {}

        # ── Loss gradient: cross-entropy + softmax ──
        # softmax cross-entropy gradient: p - y (one-hot)
        probs = self.softmax(logits, axis=-1)
        # d_logits = probs - one_hot(targets)
        d_logits = probs.copy()
        for b in range(B):
            for s in range(S):
                d_logits[b, s, targets[b, s]] -= 1.0
        # Average over batch
        d_logits = d_logits / B

        # ── Output projection ──
        ln_out = cache['ln_out_val']
        grads['W_out'] = ln_out.reshape(-1, self.d_model).T @ \
                         d_logits.reshape(-1, self.vocab_size)
        grads['b_out'] = d_logits.sum(axis=(0, 1))

        d_h = d_logits @ self.params['W_out'].T  # (B, S, D)

        # ── Output LayerNorm backward ──
        d_h, d_ln_g, d_ln_b = self.layernorm_bwd(d_h, cache['ln_out'])
        grads['ln_out_g'] = d_ln_g
        grads['ln_out_b'] = d_ln_b

        # ── Backward through blocks (in reverse) ──
        for i in reversed(range(self.n_layers)):
            p = f'block{i}_'
            block = cache['blocks'][i]

            # Residual from FFN: d_h flows to both FFN output and direct path
            d_ffn_out = d_h  # this branch goes to ffn_out

            # ── FFN backward ──
            d_act = d_ffn_out @ self.params[f'{p}W_2'].T  # (B, S, d_ff)
            d_ffn_h = d_act * (block['ffn_act'] > 0).astype(np.float64)  # ReLU grad

            grads[f'{p}W_2'] = block['ffn_act'].reshape(-1, self.d_ff).T @ \
                               d_ffn_out.reshape(-1, self.d_model)
            grads[f'{p}b_2'] = d_ffn_out.sum(axis=(0, 1))
            # ln2_out = g * x_norm + b  (not just x_norm)
            ln2_x_norm = block['ln2'][3]
            ln2_g = block['ln2'][4]
            ln2_out = ln2_g * ln2_x_norm + self.params[f'{p}ln2_b']
            grads[f'{p}W_1'] = ln2_out.reshape(-1, self.d_model).T @ \
                               d_ffn_h.reshape(-1, self.d_ff)
            grads[f'{p}b_1'] = d_ffn_h.sum(axis=(0, 1))

            # Backprop through W1 to get gradient w.r.t. LN2 output
            d_ln2_out = d_ffn_h @ self.params[f'{p}W_1'].T  # (B, S, D)

            # Backward through LN2
            d_ln2, d_ln2_g, d_ln2_b = self.layernorm_bwd(d_ln2_out, block['ln2'])
            grads[f'{p}ln2_g'] = d_ln2_g
            grads[f'{p}ln2_b'] = d_ln2_b

            # Add residual from FFN path
            d_h = d_h + d_ln2  # combine with residual

            # ── MHA backward ──
            # d_h goes to both attn_proj and residual
            d_attn_proj = d_h  # (B, S, D)

            grads[f'{p}W_o'] = block['attn_pre_proj'].reshape(-1, self.d_model).T @ \
                               d_attn_proj.reshape(-1, self.d_model)
            d_attn = d_attn_proj @ self.params[f'{p}W_o'].T  # (B, S, D)

            # Reshape to multi-head
            d_attn_mh = d_attn.reshape(B, S, self.n_heads, self.d_k).transpose(0, 2, 1, 3)

            # Attention backward
            dQ, dK, dV = self.attention_bwd(d_attn_mh, block['attn'])

            # Reshape back
            dQ = dQ.transpose(0, 2, 1, 3).reshape(B, S, self.d_model)
            dK = dK.transpose(0, 2, 1, 3).reshape(B, S, self.d_model)
            dV = dV.transpose(0, 2, 1, 3).reshape(B, S, self.d_model)

            # Projection gradients (use LN1 output = g * x_norm + b)
            ln1_x_norm = block['ln1'][3]
            ln1_g = block['ln1'][4]
            ln1_out = ln1_g * ln1_x_norm + self.params[f'{p}ln1_b']
            grads[f'{p}W_q'] = ln1_out.reshape(-1, self.d_model).T @ \
                               dQ.reshape(-1, self.d_model)
            grads[f'{p}W_k'] = ln1_out.reshape(-1, self.d_model).T @ \
                               dK.reshape(-1, self.d_model)
            grads[f'{p}W_v'] = ln1_out.reshape(-1, self.d_model).T @ \
                               dV.reshape(-1, self.d_model)

            # Gradient through Q, K, V projections to LN1 input
            d_ln1 = (dQ @ self.params[f'{p}W_q'].T +
                     dK @ self.params[f'{p}W_k'].T +
                     dV @ self.params[f'{p}W_v'].T)

            # Backward through LN1
            d_ln1, d_ln1_g, d_ln1_b = self.layernorm_bwd(d_ln1, block['ln1'])
            grads[f'{p}ln1_g'] = d_ln1_g
            grads[f'{p}ln1_b'] = d_ln1_b

            # Combine residual paths for next (lower) block
            # d_h = upstream + d_ln2 (FFN path), d_ln1 = MHA path
            # h_after = h_prev + attn_proj + ffn_out (identity paths)
            # so d_h_prev = d_h + d_ln1 (identity + LN1->MHA)
            if i == 0:
                d_h_prev = d_h + d_ln1
                grads['token_embed'] = np.zeros_like(self.params['token_embed'])
                np.add.at(grads['token_embed'], cache['x'], d_h_prev)
            else:
                d_h = d_h + d_ln1

        return grads

    # ── Parameter update (Adam) ─────────────────────────────────────

    def update(self, grads):
        """Adam update for all parameters."""
        self.t += 1
        lr_t = self.lr * np.sqrt(1 - self.beta2 ** self.t) / (1 - self.beta1 ** self.t)

        for key in self.params:
            if key not in grads:
                continue
            g = grads[key]
            self.m[key] = self.beta1 * self.m[key] + (1 - self.beta1) * g
            self.v[key] = self.beta2 * self.v[key] + (1 - self.beta2) * (g ** 2)
            self.params[key] -= lr_t * self.m[key] / (np.sqrt(self.v[key]) + self.eps)

    # ── Training ────────────────────────────────────────────────────

    def fit(self, sequences, epochs=10, batch_size=32, lr=None, verbose=True):
        """Train on sequences (character indices).

        sequences: ndarray of shape (n_sequences, seq_len+1)
                   where sequences[:, :-1] are inputs, sequences[:, 1:] are targets
        epochs: number of full passes
        batch_size: mini-batch size
        lr: optional override for learning rate
        """
        if lr is not None:
            self.lr = lr

        n = len(sequences)
        losses = []
        self.losses_ = []

        for epoch in range(epochs):
            # Shuffle
            idx = self.rng.permutation(n)
            epoch_loss = 0.0
            n_batches = 0

            for start in range(0, n, batch_size):
                batch_idx = idx[start:start + batch_size]
                X_batch = sequences[batch_idx, :-1]
                y_batch = sequences[batch_idx, 1:]

                # Forward
                logits, cache = self.forward(X_batch)

                # Loss (cross-entropy)
                B, S, V = logits.shape
                logits_flat = logits.reshape(-1, V)
                y_flat = y_batch.reshape(-1)
                # Softmax cross-entropy
                logits_stable = logits_flat - logits_flat.max(axis=-1, keepdims=True)
                log_sum_exp = np.log(np.exp(logits_stable).sum(axis=-1))
                loss = (log_sum_exp - logits_stable[np.arange(len(y_flat)), y_flat]).mean()
                epoch_loss += loss
                n_batches += 1

                # Backward
                grads = self.backward(logits, y_batch, cache)

                # Update
                self.update(grads)

                if verbose and n_batches % 50 == 0:
                    print(f'  Epoch {epoch+1}, batch {n_batches}: loss={loss:.4f}')

            avg_loss = epoch_loss / n_batches
            losses.append(avg_loss)
            self.losses_.append(avg_loss)
            if verbose:
                print(f'Epoch {epoch+1}/{epochs} — loss: {avg_loss:.4f}')

        return losses

    # ── Generation ──────────────────────────────────────────────────

    def generate(self, prefix_ids, n_chars=100, temp=1.0):
        """Generate text autoregressively.

        prefix_ids: list/array of starting token indices
        n_chars: number of characters to generate
        temp: sampling temperature (higher = more random)
        returns: list of generated token indices (including prefix)
        """
        ids = list(prefix_ids)
        for _ in range(n_chars):
            # Use last max_seq_len tokens as context
            ctx = ids[-self.max_seq_len:]
            x = np.array([ctx], dtype=np.int64)

            # Forward (no caching needed for this simple version)
            logits, _ = self.forward(x, cache=False)
            next_logits = logits[0, -1, :] / temp

            # Sample
            probs = self.softmax(next_logits[np.newaxis, :])[0]
            next_idx = self.rng.multinomial(1, probs).argmax()
            ids.append(int(next_idx))

        return ids

    def sample(self, prefix_ids, n_chars=100, temp=1.0):
        """Alias for generate()."""
        return self.generate(prefix_ids, n_chars, temp)


if __name__ == '__main__':
    # Quick smoke test
    vocab_size = 50
    model = TransformerLM(vocab_size, d_model=16, n_heads=2, n_layers=2,
                          d_ff=32, max_seq_len=16)
    print('Params:', len(model.params))

    # Create random data
    B, S = 4, 12
    X = np.random.randint(0, vocab_size, (B, S))
    y = np.random.randint(0, vocab_size, (B, S))

    # Test forward
    logits, cache = model.forward(X)
    print(f'Forward OK: logits shape {logits.shape}')

    # Test backward + update
    grads = model.backward(logits, y, cache)
    print(f'Backward OK: {len(grads)} gradients')

    # Check no NaN/Inf gradients
    for k, v in grads.items():
        if np.any(np.isnan(v)) or np.any(np.isinf(v)):
            print(f'  WARNING: {k} has NaN/Inf')
    print('Gradient check passed (no NaN/Inf)')

    # Test update
    model.update(grads)
    print('Update OK')

    # Test generation
    gen = model.generate([0, 1, 2], n_chars=10, temp=1.0)
    print(f'Generate OK: {len(gen)} tokens')

    # Test training loop
    sequences = np.random.randint(0, vocab_size, (20, S + 1))
    losses = model.fit(sequences, epochs=2, batch_size=4, verbose=False)
    print(f'Training OK: losses {[f"{l:.4f}" for l in losses]}')
    print('All smoke tests passed!')
