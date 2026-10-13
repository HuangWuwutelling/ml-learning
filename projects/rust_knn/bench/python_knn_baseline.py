"""Stage 1 baseline: same KNN predict timing, in pure Python/numpy.

Generates the same 5000 x 8 train set (3 classes) and 500 query points with
the same seed, then times the predict step. Run with:

    python bench/python_knn_baseline.py
"""
import sys
import time
import numpy as np

# Make the Python KNN importable from the repo root.
# This script is run from projects/rust_knn/, so 2 levels up reaches the repo root.
sys.path.insert(0, "../..")
from models.knn import KNN

N_TRAIN = 5_000
N_QUERY = 500
N_FEATURES = 8
N_CLASSES = 3
K = 5
SEED = 42


def main():
    rng = np.random.default_rng(SEED)
    x_train = rng.uniform(-1.0, 1.0, size=(N_TRAIN, N_FEATURES))
    y_train = rng.integers(0, N_CLASSES, size=N_TRAIN)
    x_query = rng.uniform(-1.0, 1.0, size=(N_QUERY, N_FEATURES))

    model = KNN(k=K, weights="uniform", metric="euclidean")
    model.fit(x_train, y_train)

    # Warm-up
    _ = model.predict(x_query)

    start = time.perf_counter()
    preds = model.predict(x_query)
    elapsed = time.perf_counter() - start

    print("Python KNN predict (numpy):")
    print(f"  n_train={N_TRAIN} n_query={N_QUERY} n_features={N_FEATURES} k={K}")
    print(f"  elapsed: {elapsed*1000:.1f} ms")
    print(f"  per query: {elapsed*1000/N_QUERY:.3f} ms")
    print(f"  predicted {len(preds)} labels (first 5: {list(preds[:5])})")


if __name__ == "__main__":
    main()
