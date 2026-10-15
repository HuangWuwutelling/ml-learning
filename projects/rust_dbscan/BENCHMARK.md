# Stage 1 Benchmark

2026-10-15, 同台机器 (Windows 11, rustc 1.99.0 GNU toolchain, Python + numpy), seed=42。

## 数据集

2D 3-Gaussian 团簇（每团簇中心 (0,0)/(5,5)/(-5,5), 标准差 0.5），`n_per = n / 3` 整除对齐。

## 数字

| n | Rust release | Python/numpy | 优势 |
|---|---|---|---|
| 5000  | **705 ms** | 3607 ms | **5.1×** |
| 10000 | **4412 ms** | 13644 ms | **3.1×** |

## 跑法

```bash
cd projects/rust_dbscan
cargo run --release --example benchmark      # Rust 705 ms / 4412 ms
python bench/python_dbscan_baseline.py      # Python 3607 ms / 13644 ms
```

## 结论

达到 Stage 1 预期 ≥5× 优势（n=5000）。n=10000 时优势缩到 3.1× 但仍拉开真实差距。

## 为什么 DBSCAN 能拉开差距

**DBSCAN 是控制流密集型算法**，三层嵌套（每个点 → 每个邻居 → 簇扩展种子队列）+ 每步都跑条件分支。numpy 的 vectorized 路径是 `X - X[i]` 算全部距离 → O(n² × d) vectorized，单次开销小但摊到整个 fit 主循环的 Python `for i in range(n)` 上仍要重复做小数据。

Rust 的 for 循环**常数开销是 Python 的 1/5 到 1/10**（这是经验值，Stage 1 KNN 案例 Python `X @ X_train.T` BLAS 矩阵乘优化版反而掩盖了 Python for 慢的本质——109ms vs 120ms 仅快 10%）。这次 DBSCAN 没有 BLAS 全局优化机会，Python 端的常数开销暴露出来，Rust 5× 优势就出来了。

完整学习笔记 + Rust 触点 + 踩坑：`../../_local/article_notes/rust/01_stage1_dbscan_notes.md`（本机唯一事实源，gitignored）。
