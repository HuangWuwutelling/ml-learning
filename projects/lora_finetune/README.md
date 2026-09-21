# 环境违法严重程度识别（QLoRA 微调）

环境合规审核员收到违规检查报告后，要凭经验判定严重程度（高 / 中 / 低）。
同一条违规，不同审核员给出的等级可能不一致。

这里用 QLoRA 微调 `Qwen2.5-0.5B-Instruct` 做自动判定，
全程在一张 4GB 显存的普通显卡上完成。

## 结果

34 条留出测试题上的准确率：

| | 准确率 |
|---|---|
| 微调前（原始 Qwen2.5-0.5B-Instruct） | 29.4%（10/34） |
| **微调后** | **91.2%（31/34）** |

分类明细：

| 真实等级 | 题数 | 微调前 | 微调后 |
|---|---|---|---|
| 高 | 4 | 1 | 4 |
| 中 | 9 | 9 | 6 |
| 低 | 21 | 0 | 21 |
| **合计** | **34** | **10** | **31** |

原始模型 34 题里 33 题答「中」（另 1 题答「高」），低严重度 21 题一题没答对。
微调后低严重度 21/21 全对，中严重度从 9/9 掉到 6/9，是唯一退步的一项。

逐题预测在 `base_predictions.jsonl` / `lora_predictions.jsonl`。

## 对照组：只改输出格式，不微调

`structured_output.py` 在**原始模型**上试了三种让输出可解析的写法，各跑 34 题：

| 方法 | system prompt 要求 | 解析成功率 | 准确率 |
|---|---|---|---|
| 纯文本 | 只输出「高 / 中 / 低」 | 100%（34/34） | 20.6%（7/34） |
| JSON | `{"label": "高"}` | 100%（34/34） | 20.6%（7/34） |
| 工具调用 | `<tool_call>{...}</tool_call>` | 100%（34/34） | 35.3%（12/34） |

三种写法都能把答案解析出来（解析成功后用 Pydantic 校验取值只能是高 / 中 / 低），
准确率是 20.6% / 20.6% / 35.3%。

三种方法名对应 OpenAI / Anthropic API 里的 `response_format` 与 `tool_choice`，
这里是 transformers 直推场景下的模拟实现，都是「prompt + parse + Pydantic」。

**注意这组数是原始模型的**：`structured_output.py` 的 `_load_model()` 只加载底模，
不挂 LoRA adapter，所以它是「不微调」的基线。

## 怎么跑

```bash
pip install -r requirements.txt

python train.py     # 训练，输出 lora_adapter/
python eval.py      # 三种结构化输出方法在测试集上的对照
```

## 训练配置

| 项 | 值 |
|---|---|
| 底模 | `Qwen/Qwen2.5-0.5B-Instruct` |
| 量化 | 4-bit NF4 + double quant |
| LoRA | r=16 / alpha=32 / dropout=0.05，`q/k/v/o/gate/up/down_proj` 七个投影层 |
| 批大小 | 2 × 梯度累积 4 |
| 序列长度 | 128 token |
| 轮数 / 学习率 | 8 轮 / 2e-4，cosine + 5% warmup |
| 显存 | 4GB 卡可跑（4-bit + LoRA + 梯度检查点） |
| 训练量 | 140 步，约 11 分钟 |

loss 从 4.269 降到 0.0018，140 步的完整记录在 `logs/trainer_state.json`。

`train.py` 的 `tokenize_fn` 把 prompt 部分的 label 置成 -100，
只有答案那个汉字参与 loss 计算。

## 数据

`../../data/env_violations.jsonl`，174 条人工标注，覆盖印染、化工、造纸、钢铁、电镀 5 个行业：

| 等级 | 条数 |
|---|---|
| 低 | 113 |
| 中 | 31 |
| 高 | 30 |

`train.py` 用 `seed=42` 打乱后按 8:2 切：**140 条训练 / 34 条测试**。
测试集落盘成 `test_set.jsonl` 供 `eval.py` 用，不参与训练。

## 文件

| 文件 | 干什么 |
|---|---|
| `train.py` | QLoRA 训练，输出 `lora_adapter/` |
| `eval.py` | 三种结构化输出方法在 34 题上的对照，写 `eval_results.json` |
| `structured_output.py` | 三种方法的实现 + 模型加载 + 三个 Pydantic 解析器 |
| `lora_adapter/` | 训练好的 LoRA 权重（safetensors）+ tokenizer |
| `test_set.jsonl` | 34 条留出测试题 |
| `base_predictions.jsonl` | 原始模型逐题预测 |
| `lora_predictions.jsonl` | 微调后逐题预测 |
| `logs/trainer_state.json` | 140 步的 loss 记录 |

## 已知限制

- **训练集只有 140 条。** loss 降到 0.0018 已经很低，有过拟合风险；
  91.2% 是在 34 条留出集上测的，样本量小，换个数据分布不一定复现。
- **中严重度反而退步**（9/9 → 6/9）。9 条「中」测试题里有 3 条被微调后的模型判成了别的等级，
  另两类（高 4/4、低 21/21）都是满分。34 条测试题里只有 9 条是「中」，波动空间也小。
- **评测没有重复多次取均值**，单次运行的数字里含采样噪声；
  不过 `eval.py` 用的是 greedy（`do_sample=False`），摆动的来源只有模型本身。
