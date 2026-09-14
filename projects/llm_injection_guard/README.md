# LLM Prompt Injection 6 层防线演示

配套文章：公众号「为什么 ChatGPT 会被骗：6 层防线抵御 Prompt Injection」（#18）。

## 6 层防线

1. **输入预处理**：去零宽字符、Unicode normalize、控制字符过滤
2. **攻击检测**：正则 + 关键词评分（production 可换 Prompt Guard 2）
3. **Prompt 隔离**：用 `<<USER_INPUT>>` 包裹，明确数据不是指令
4. **System prompt 加固**：最小权限 + 优先级声明
5. **输出验证**：JSON Schema + 正则 + 黑名单
6. **行动沙盒**：工具白名单 + 人工确认

## 跑实测

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python eval.py  # 跑 40 条 prompt × 7 配置 = 280 次，输出 eval_results.json
```

## 文件

- `defenses/layer1_preprocess.py` - 输入预处理
- `defenses/layer2_detect.py` - 攻击检测
- `defenses/layer3_spotlight.py` - Prompt 隔离
- `defenses/layer4_harden.py` - System prompt 加固
- `defenses/layer5_validate.py` - 输出验证
- `defenses/layer6_sandbox.py` - 行动沙盒
- `orchestrator.py` - 6 层管线拼装
- `eval.py` - 跑实测 + 写 eval_results.json
- `attack_set.jsonl` - 30 条攻击 prompt
- `normal_set.jsonl` - 10 条 normal prompt
