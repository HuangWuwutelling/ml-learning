# rust_embedding_service

副线 3 Stage 3：async Rust embedding 服务。

设计文档：`docs/superpowers/specs/rust-stage2-3/2026-10-21-pyo3-candle-design.md` §2

---

## 当前进度

| 步骤 | 内容 | 状态 |
|---|---|---|
| 6 | 探雷 candle 在 MSVC 下能否编过 | ✅ exit 0，5m12s，142 个依赖 |
| 7 | 骨架 + `/healthz` `/readyz` | ✅ 本目录 |
| 8 | 模型加载 + `/v1/embeddings` | ✅ 10 个用例（6 路由 + 4 推理） |
| 9 | `spawn_blocking` 并发测试 + 压测 | ⬜ |

## 跑起来

```bash
cd D:/Workspace/ml-learning/projects/rust_embedding_service

cargo test                    # 6 个路由用例，不占端口不碰模型，0.06s
cargo run --release           # 监听 127.0.0.1:8080
```

另开一个终端：

```bash
curl http://127.0.0.1:8080/healthz
curl http://127.0.0.1:8080/readyz          # 模型加载完之前是 503
curl -X POST http://127.0.0.1:8080/v1/embeddings \
  -H 'content-type: application/json' \
  -d '{"input":["排污单位应当按证排污","今天天气很好"]}'
```

四个**真跑模型**的用例默认 `#[ignore]`（要 mmap 约 1 GB 权重，debug 构建下
0.5B 模型慢到没法用），单独跑：

```bash
cargo test --release --test model_tests -- --ignored --nocapture --test-threads=1
```

## 目录

```
src/
├── lib.rs          Router + AppState（放在 lib 里，tests/ 要用）
├── main.rs         tokio main + 先绑端口再加载模型 + 优雅关闭
├── config.rs       环境变量，全部带默认值
├── model.rs        Embedder：config.json → qwen2::Config → mmap 权重 → forward
├── error.rs        AppError → OpenAI 风格错误信封
├── schema.rs       请求/响应 struct
└── routes/
    ├── mod.rs
    ├── health.rs   /healthz + /readyz
    └── embed.rs    /v1/embeddings
tests/
├── api_tests.rs    tower::ServiceExt::oneshot，不起真端口、不碰模型
└── model_tests.rs  真推理，#[ignore]，--test-threads=1
```

## 五个刻意的决定

### 1. step 7 的骨架里没有 candle

设计文档 §2.1 的 Cargo.toml 一次列了 candle-core / candle-transformers /
tokenizers。step 7 没引。**candle-core 单独编译就要 5 分 12 秒** —— 拉进来之后，
每改一行路由都要等 5 分钟才能看到报错。骨架不碰它们，编译是秒级的（1m04s → 2.91s）。
探雷结果（exit 0）说明这一步不会再卡住。

### 2. `/healthz` 和 `/readyz` 分开

不是凑数，两个探针的失败后果完全不同：

- `/healthz` = 进程活着吗。失败 → **重启容器**。所以它不能掺任何模型状态 ——
  模型没加载好，重启一百次也没用。
- `/readyz` = 现在能接流量吗。失败 → **从负载均衡摘掉**。

加载 0.5B 权重要几秒，滚动发布时不分开就会被打到还没准备好的实例上。所以模型
加载完之前 `/readyz` **返回 503**。

写第一版的时候我给了它 200 + `{"status":"loading"}` —— 这是个真 bug：k8s 只看
状态码，200 就等于 ready，于是实例在被流量打到的同时还在 mmap 权重。探针要能失败
才有意义，加载中就是没准备好。

对应的 `main.rs` 也因此**先 `bind()` 再加载模型**：慢加载期间端口已经在了，
liveness 探针拿得到 200，不会因为「还没 ready」把正在加载的容器重启一遍。

### 3. candle 推理走 `spawn_blocking`

candle 是 **CPU-bound 同步**的，直接写进 `async fn` handler 会占住 tokio 的
worker 线程不动，0.5B 模型的整个 forward pass 期间该 worker 上所有连接（含
`/healthz`）全部卡死。`spawn_blocking` 把它挪到阻塞线程池。

顺带一提，`Arc<Mutex<Model>>` 不是为了应付这个 API 的签名，是**真的需要**：
`qwen2::Model::forward` 收 `&mut self` 是因为它维护 KV cache，并发请求不串行化
会互相污染。step 9 会用「不 spawn_blocking」的版本做对照，实测差多少。

### 4. 每次 forward 之后 `clear_kv_cache()`

`candle_transformers` 0.11 的 `qwen2::Attention::forward`（model.rs:189）结尾是
一句**无条件**的 `self.kv_cache = Some(...)`，第一次调用也写。不清的话下一个请求的
key 会被 `cat` 到这一个上面。

我一开始以为这个 bug 是**悄悄错**的 —— 维度对、数值正常、只是语义偏了，所以专门写了
个测试拿同一句话问两遍比余弦相似度。**把 `clear_kv_cache()` 注释掉重跑一遍才发现
不是**：cache 只会变长，第二次调用之后 `k_len` 永远不可能等于 `q_len`，直接

```
shape mismatch in broadcast_add, lhs: [1, 14, 104, 111], rhs: [1, 1, 104, 104]
```

炸掉（14 是 Qwen2.5-0.5B 的 head 数，q_len 104 是那条长文本，k_len 111 = 104 旧的
+ 7 前一次留下的）。响亮失败，不是静默偏差。

测试还是留着，但理由变了：这个响亮的 panic 是**当前 candle 版本的 shape 检查**
顺带带来的，不是 API 承诺的性质。真换了版本它可能变成别的形态（比如截断到 cache
长度），所以把「同一输入给同一输出」这个不变量钉住。

### 5. 右侧 padding 只对因果注意力安全

batch 里长度不一就右侧补 0，然后取每行**自己最后一个真实 token** 的位置
（`rows[i].len() - 1`，不是 `seq_len - 1`）。

补 0 之所以安全，是因为因果注意力下位置 p 只 attend 到 ≤ p，pad 全在真实 token
右边，没有真实 token 会看到 pad。**换 BERT 这类双向注意力模型这段推理直接失效**，
必须上显式 attention mask —— 换模型时这里是要重写的地方，不是照抄。

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `EMBED_ADDR` | `127.0.0.1:8080` | 监听地址 |
| `EMBED_SHUTDOWN_GRACE_SECS` | `10` | 收到信号后等在途请求的秒数 |
| `EMBED_MODEL_DIR` | 自动探测 HF 缓存 | 装 `config.json` / `model.safetensors` / `tokenizer.json` 的目录 |
| `EMBED_MODEL_NAME` | `Qwen2.5-0.5B` | 响应里 `model` 字段的值，也是客户端必须带回来的值 |
| `EMBED_MAX_TOKENS` | `512` | 单条输入的 token 上限 |
| `RUST_LOG` | `info` | 日志级别，`debug` 能看到 TraceLayer 的每条路由 |

变量值解析失败会 `warn` 一条日志然后用默认值，不会让容器起不来。

默认探测是扫 `models--Qwen--Qwen2.5-0.5B-Instruct/snapshots/*` 找带
`model.safetensors` 的那个 —— snapshot 目录名是内容哈希，模型重下就变，写死路径
迟早失效。

## 模型怎么选的

`candle_transformers` 0.11 **没有 `from_pretrained`**，全 crate 都搜不到。config.json
只能自己 `serde_json` 反序列化成 `qwen2::Config`（字段全 pub、derive Deserialize、
未知字段忽略），权重用 `VarBuilder::from_mmaped_safetensors`。

两个坑：

- `Model::new` 内部自己会 `vb.pp("model")`，所以喂**根** builder。喂一个已经加了
  前缀的会去找 `model.model.embed_tokens.weight`，加载时直接失败。
- `from_mmaped_safetensors` 是 `unsafe`。

用 `qwen2::Model` 而不是 `ModelForCausalLM`：后者是给生成用的，会再过一层
`lm_head` 拿 logits。embedding 要的是 `forward` 返回的 normed hidden states，
也就是 `xs.apply(&self.norm)` 的结果。

## 关联

- Stage 1：`projects/rust_dbscan/`（Rust vs Python 5.1×）
- Stage 2：`projects/rust_pyo3_dbscan/`（PyO3 + GIL 释放 3.50×）
- 模型来源：`data/README.md`