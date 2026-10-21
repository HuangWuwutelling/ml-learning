# rust_embedding_service

副线 3 Stage 3：async Rust embedding 服务。

设计文档：`docs/superpowers/specs/rust-stage2-3/2026-10-21-pyo3-candle-design.md` §2

---

## 当前进度

| 步骤 | 内容 | 状态 |
|---|---|---|
| 6 | 探雷 candle 在 MSVC 下能否编过 | ✅ exit 0，5m12s，142 个依赖 |
| 7 | 骨架 + `/healthz` `/readyz` | ✅ 本目录 |
| 8 | 模型加载 + `/v1/embeddings` | ⬜ |
| 9 | `spawn_blocking` 并发测试 + 压测 | ⬜ |

## 跑起来

```bash
cd D:/Workspace/ml-learning/projects/rust_embedding_service

cargo test                    # 3 个 in-process 用例，不占端口
cargo run --release           # 监听 127.0.0.1:8080
```

另开一个终端：

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/readyz
```

## 目录

```
src/
├── lib.rs          Router + AppState（放在 lib 里，tests/ 要用）
├── main.rs         tokio main + 优雅关闭
├── config.rs       环境变量，全部带默认值
├── schema.rs       请求/响应 struct
└── routes/
    ├── mod.rs
    └── health.rs   /healthz + /readyz
tests/
└── api_tests.rs    tower::ServiceExt::oneshot，不起真端口
```

## 三个刻意的决定

### 1. 骨架里没有 candle

设计文档 §2.1 的 Cargo.toml 一次列了 candle-core / candle-transformers /
tokenizers。step 7 没引。**candle-core 单独编译就要 5 分 12 秒** —— 拉进来之后，
每改一行路由都要等 5 分钟才能看到报错。骨架不碰它们，编译是秒级的。

依赖清单以注释形式留在 `Cargo.toml` 里，step 8 取消注释即可。
探雷结果（exit 0）说明这一步不会再卡住。

### 2. `/healthz` 和 `/readyz` 分开

不是凑数，两个探针的失败后果完全不同：

- `/healthz` = 进程活着吗。失败 → **重启容器**。所以它不能掺任何模型状态 ——
  模型没加载好，重启一百次也没用。
- `/readyz` = 现在能接流量吗。失败 → **从负载均衡摘掉**。

step 7 没有模型，所以 `model_loaded: true`，一绑定就 ready。step 8 会在启动时
置 `false`、权重加载完再翻成 `true` —— 这就是这层间接存在的理由。加载 0.5B 权重
要几秒，滚动发布时不分开就会被打到还没准备好的实例上。

`tests/api_tests.rs` 里 `readyz_is_ok_with_no_model_to_wait_for` 断言了当前的
`true`，step 8 会**故意让它失败一次**，那是行为真的变了，不是测试坏了。

### 3. `axum::serve` 在 tokio 上，candle 推理走 `spawn_blocking`

还没实现，但这是本阶段最关键的工程判断，先记在这里：candle 是 **CPU-bound 同步**的，
直接写进 `async fn` handler 会堵死整个 executor。step 9 会用「不 spawn_blocking」
的版本做对照，实测两者总耗时的差。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `EMBED_ADDR` | `127.0.0.1:8080` | 监听地址 |
| `EMBED_SHUTDOWN_GRACE_SECS` | `10` | 收到信号后等在途请求的秒数 |
| `RUST_LOG` | `info` | 日志级别，`debug` 能看到 TraceLayer 的每条路由 |

变量值解析失败会 `warn` 一条日志然后用默认值，不会让容器起不来。

## 关联

- Stage 1：`projects/rust_dbscan/`（Rust vs Python 5.1×）
- Stage 2：`projects/rust_pyo3_dbscan/`（PyO3 + GIL 释放 3.50×）
- 模型来源：`data/README.md`