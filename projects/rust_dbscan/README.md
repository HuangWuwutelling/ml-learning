# rust_dbscan

DBSCAN clustering ported from Python (`models/dbscan.py`) to Rust. Stage 1 of the Rust 渐进式学习 side track (副线 3 — 不进简历、不主动跑).

## Why DBSCAN (not KNN)

Stage 1 originally ported KNN. KNN is BLAS-friendly (Python/numpy uses `X @ X_train.T` matrix multiplication + `np.argpartition` + `np.bincount`), so naive Rust only beat Python by 10% (109 ms vs 120 ms on n=5000×500×8). KNN doesn't exercise the Rust-for-loop vs Python-for-loop gap.

DBSCAN is control-flow dense (three-level nested: per point → per neighbour → cluster expansion), with no BLAS opportunity for numpy to hide the Python loop overhead. Naive Rust achieves **5.1× @ n=5000** and **3.1× @ n=10000** on a 2D 3-Gaussian dataset, confirming the structural reason for the switch.

## Results

See [BENCHMARK.md](BENCHMARK.md) for full numbers, dataset, and reproduction commands.

## Learnings

Full learning notes (Rust touches, gotchas, Stage 2/3 hooks) live at `_local/article_notes/rust/01_stage1_dbscan_notes.md` — **local-only, gitignored** as the canonical fact source.

## Status

| Stage | Crate | State |
|---|---|---|
| 1 — Rust basics | `projects/rust_dbscan/` | ✅ done (2026-10-15, 11 tests, 5.1× speedup @ n=5000) |
| 2 — PyO3 | `projects/rust_pyo3_dbscan/` | ⏳ pending |
| 3 — candle + axum | `projects/rust_embedding_service/` | ⏳ pending (解 env-rag 285s/查询 性能瓶颈) |

The full 3-stage plan lives in `_local/plan.md` 「副线 3」段.

## Build / Test / Benchmark

```bash
cd projects/rust_dbscan
cargo test                              # 11 integration tests
cargo run --release --example benchmark # Rust timing
python bench/python_dbscan_baseline.py  # Python timing (对比)
```

## 降级条件

整 3 阶段暂停 if: ownership/编译问题反复超过 2 天 / 找不到与已有项目差异化价值.
Rust vs Python 优势 < 3× → 切回原 KNN 案例或升级到 SIMD 案例.
