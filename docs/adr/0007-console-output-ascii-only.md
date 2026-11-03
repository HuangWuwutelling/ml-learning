# ADR-0007 · 控制台输出只用 ASCII

- 状态: accepted
- 登记日期: 2026-11-01

## 约束

Windows 控制台默认 GBK 编码，`print()` 遇到 `²` `×` `−` `Σ` `∞` 会抛
`UnicodeEncodeError`。这个坑在环境模型脚本里踩过。

## 裁定

**脚本的 `print` 只用 ASCII。** 中文和特殊符号留给 matplotlib 出图（配 CJK 字体），
不进控制台。

## 后果

脚本日志的标签要重新想措辞（英文或拼音 ASCII），换来在 Windows 上不崩。
写新脚本时先定好标签怎么用 ASCII，不要等跑挂了再回头改。
