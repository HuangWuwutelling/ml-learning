# 模型来源

Stage 3 step 8 加载的权重来自本机 HuggingFace cache，**不需要联网下载**。

## 缓存路径

`D:\Workspace\.cache\huggingface`（由 `HF_HOME` / `HF_HUB_CACHE` 环境变量指定，
用 `setx` 写入，需要新开终端才生效）。

## 已缓存的模型

| 模型 | 用途 | 状态 |
|---|---|---|
| `Qwen/Qwen2.5-0.5B-Instruct` | Stage 3 embedding 服务 | ✅ 已缓存 |
| `BAAI/bge-small-zh-v1.5` | env-rag 的 dense 检索（对照用） | ✅ 已缓存 |

## Qwen2.5-0.5B 的关键参数

| 项 | 值 |
|---|---|
| hidden_size（embedding 维度） | **896** |
| 层数 | 24 |
| 词表 | 151,936 |
| 权重大小（bf16） | ~1 GB |

`dimensions: 896` 写死在 `/v1/embeddings` 的响应 schema 里（设计文档 §2.2）。
若换模型，这个数和 `Qwen2.5-0.5B` 的 `model` 字段都要跟着改 —— 建议改成从
模型 config 读，别硬编码。

## 权重格式

candle 用 safetensors，不读 PyTorch `.bin`。cache 里 `Qwen2.5-0.5B-Instruct`
的 `model.safetensors` 可直接用 `VarBuilder::from_mmaped_safetensors` 加载，
零拷贝映射。

## tokenizer

tokenizer 文件（`tokenizer.json` / `tokenizer_config.json`）在同一个 snapshot
目录下，`Tokenizer::from_file` 直接指向它。

**版本注意**：`tokenizers` crate 最新发布是 `1.0.0-rc.3`，是 RC。
Step 8 引入时锁 **0.21**（最后一个稳定线）。