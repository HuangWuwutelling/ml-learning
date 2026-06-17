"""
Word2Vec — Skip-gram with Negative Sampling, numpy only.

Architecture
  Center word one-hot  →  Embedding lookup (W_in)  →  Dot product with
  context embeddings (W_out)  →  Sigmoid binary classification

Trained with negative sampling: for each positive (center, context) pair,
sample k negative (center, random) pairs as binary classification
training examples.

References
  - Mikolov et al. (2013). Efficient Estimation of Word Representations
    in Vector Space.
  - Mikolov et al. (2013). Distributed Representations of Words and
    Phrases and their Compositionality.
  - Rong (2014). word2vec Parameter Learning Explained.
"""
import numpy as np
from collections import Counter
import re


class Word2Vec:
    """Skip-gram with Negative Sampling.

    Parameters
    ----------
    embedding_dim : int
        Dimensionality of word vectors.
    lr : float
        Learning rate for SGD.
    epochs : int
        Number of training passes over the corpus.
    window : int
        Maximum distance between center and context word (half-window).
    n_negative : int
        Number of negative samples per positive pair.
    min_count : int
        Minimum word frequency to include in vocabulary.
    subsample_threshold : float
        Threshold for frequent word subsampling (1e-3 typical).
        Words with frequency > threshold are downsampled during training.
    random_state : int
        Seed for reproducibility.
    """

    def __init__(self, embedding_dim=50, lr=0.01, epochs=5, window=3,
                 n_negative=5, min_count=5, subsample_threshold=1e-3,
                 random_state=42):
        self.embedding_dim = embedding_dim
        self.lr = lr
        self.epochs = epochs
        self.window = window
        self.n_negative = n_negative
        self.min_count = min_count
        self.subsample_threshold = subsample_threshold
        self.random_state = random_state

        self.word_to_idx = {}
        self.idx_to_word = {}
        self.vocab_size = 0
        self.W_in = None       # (vocab_size, embedding_dim)  — word vectors
        self.W_out = None      # (embedding_dim, vocab_size) — context vectors
        self.losses_ = []

    # ── Tokenization & vocabulary ─────────────────────────

    def _tokenize(self, text):
        """Lowercase and split into word tokens."""
        text = text.lower()
        return re.findall(r"[a-z']+|[.!?;,:]", text)

    def _build_vocab(self, tokens):
        """Build vocabulary, filtering by min_count."""
        counts = Counter(tokens)
        vocab_words = [w for w, c in counts.items() if c >= self.min_count]
        self.word_to_idx = {w: i for i, w in enumerate(vocab_words)}
        self.idx_to_word = {i: w for i, w in enumerate(vocab_words)}
        self.vocab_size = len(vocab_words)

        # Build training token sequence (only words in vocab)
        self._train_tokens = [t for t in tokens if t in self.word_to_idx]

        # Unigram distribution ^ 0.75 for negative sampling
        freqs = np.array([counts[w] for w in vocab_words], dtype=float)
        noise = freqs ** 0.75
        self._noise_probs = noise / noise.sum()

        # Subsampling probabilities
        total = sum(freqs)
        self._subsample_probs = {}
        for w, f in zip(vocab_words, freqs):
            rate = f / total
            if rate > self.subsample_threshold:
                # P(keep) = (sqrt(rate/t) + 1) * t/rate
                t = self.subsample_threshold
                self._subsample_probs[w] = (np.sqrt(rate / t) + 1) * (t / rate)
            else:
                self._subsample_probs[w] = 1.0

        print(f'[Word2Vec] Vocab: {self.vocab_size} words '
              f'({len(self._train_tokens)} training tokens)')

    # ── Initialization ────────────────────────────────────

    def _init_params(self):
        rng = np.random.RandomState(self.random_state)
        scale = 0.5 / self.embedding_dim
        self.W_in = rng.uniform(-scale, scale,
                                (self.vocab_size, self.embedding_dim))
        # Both matrices need random init — zero W_out makes all
        # negative gradients identical and hurts differentiation.
        self.W_out = rng.uniform(-scale, scale,
                                 (self.embedding_dim, self.vocab_size))

    # ── Negative sampling ─────────────────────────────────

    def _sample_negative(self, exclude_idx):
        """Sample n_negative indices excluding exclude_idx."""
        n_vocab = self.vocab_size
        samples = []
        # Over-sample to handle collisions
        pool = np.random.choice(n_vocab, size=self.n_negative * 3,
                                p=self._noise_probs)
        for idx in pool:
            if idx != exclude_idx:
                samples.append(int(idx))
                if len(samples) == self.n_negative:
                    break
        # Fallback: fill with random uniform
        while len(samples) < self.n_negative:
            idx = np.random.randint(0, n_vocab)
            if idx != exclude_idx:
                samples.append(idx)
        return samples

    # ── Training ──────────────────────────────────────────

    def fit(self, corpus):
        """Train word embeddings on a text corpus.

        Parameters
        ----------
        corpus : str
            Training text.
        """
        # Tokenize
        if isinstance(corpus, str):
            tokens = self._tokenize(corpus)
        else:
            tokens = []
            for line in corpus:
                tokens.extend(self._tokenize(line))

        self._build_vocab(tokens)
        self._init_params()

        N = len(self._train_tokens)
        rng = np.random.RandomState(self.random_state)
        idx_arr = np.arange(N)

        for epoch in range(self.epochs):
            rng.shuffle(idx_arr)
            total_loss = 0.0
            n_pairs = 0

            for pos in idx_arr:
                word = self._train_tokens[pos]

                # Frequent word subsampling (skip word entirely)
                if rng.uniform() > self._subsample_probs.get(word, 1.0):
                    continue

                center_idx = self.word_to_idx[word]

                # Build context window
                context_idxs = []
                for w in range(-self.window, self.window + 1):
                    if w == 0:
                        continue
                    p = pos + w
                    if 0 <= p < N:
                        cw = self._train_tokens[p]
                        if cw in self.word_to_idx:
                            context_idxs.append(self.word_to_idx[cw])

                # Train each (center, context) pair
                for ctx_idx in context_idxs:
                    loss = self._train_pair(center_idx, ctx_idx)
                    total_loss += loss
                    n_pairs += 1

            avg_loss = total_loss / max(n_pairs, 1)
            self.losses_.append(avg_loss)
            print(f'  Epoch {epoch+1}/{self.epochs}  '
                  f'pairs={n_pairs}  loss={avg_loss:.4f}')

        return self

    def _train_pair(self, center_idx, context_idx):
        """Single (center, context) pair training step.

        All gradients computed before any weight update (mini-batch
        of 1 with all negatives as a simultaneous batch).
        """
        h = self.W_in[center_idx]                     # (embedding_dim,)

        # ── Forward ──
        # Positive context
        pos_score = h @ self.W_out[:, context_idx]
        pos_prob = 1.0 / (1.0 + np.exp(-pos_score))

        # Negative samples
        neg_idxs = self._sample_negative(context_idx)
        neg_scores = h @ self.W_out[:, neg_idxs]      # (n_negative,)
        neg_probs = 1.0 / (1.0 + np.exp(-neg_scores))

        # BCE loss
        eps = 1e-10
        loss = -np.log(max(pos_prob, eps))
        loss += -np.sum(np.log(np.maximum(1.0 - neg_probs, eps)))

        # ── Backward (compute all gradients first) ──
        delta_pos = pos_prob - 1.0                    # sigmoid - target(1)

        # Gradient for W_in: accumulate over all samples
        grad_h = (delta_pos * self.W_out[:, context_idx]
                  + neg_probs @ self.W_out[:, neg_idxs].T)  # (embedding_dim,)

        # Update output weights
        self.W_out[:, context_idx] -= self.lr * delta_pos * h
        for i, nidx in enumerate(neg_idxs):
            self.W_out[:, nidx] -= self.lr * neg_probs[i] * h

        # Update input (embedding) weights
        self.W_in[center_idx] -= self.lr * grad_h

        return loss

    # ── Inference ─────────────────────────────────────────

    def get_embedding(self, word):
        """Return the embedding vector for a word."""
        idx = self.word_to_idx.get(word)
        if idx is None:
            raise KeyError(f"Word '{word}' not in vocabulary")
        return self.W_in[idx].copy()

    def most_similar(self, word, top_n=10):
        """Return list of (word, cosine_similarity) most similar to query."""
        idx = self.word_to_idx.get(word)
        if idx is None:
            return []
        vec = self.W_in[idx]

        norms = np.linalg.norm(self.W_in, axis=1)
        sims = (self.W_in @ vec) / (norms * np.linalg.norm(vec) + 1e-10)

        # Top results, excluding self
        top = np.argsort(sims)[::-1]
        top = top[top != idx]
        return [(self.idx_to_word[int(i)], float(sims[i]))
                for i in top[:top_n]]

    def analogy(self, a, b, c, top_n=5):
        """Classic analogy: a:b as c:? → find d = b - a + c.

        Example: word2vec.analogy('king', 'man', 'queen')
        """
        for w in (a, b, c):
            if w not in self.word_to_idx:
                return []
        va = self.W_in[self.word_to_idx[a]]
        vb = self.W_in[self.word_to_idx[b]]
        vc = self.W_in[self.word_to_idx[c]]
        target = vb - va + vc

        norms = np.linalg.norm(self.W_in, axis=1)
        sims = (self.W_in @ target) / (norms * np.linalg.norm(target) + 1e-10)

        top = np.argsort(sims)[::-1]
        # Exclude a, b, c
        exclude = {self.word_to_idx[w] for w in (a, b, c)}
        top = [i for i in top if i not in exclude]
        return [(self.idx_to_word[int(i)], float(sims[i]))
                for i in top[:top_n]]
