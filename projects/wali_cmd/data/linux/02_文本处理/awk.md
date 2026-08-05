---
name: awk
category: 文本处理
syntax: "awk [options] 'program' [file...]"
tags: ["文本", "字段处理", "脚本"]
aliases: []
level: 进阶
popularity: 80
---

按行扫描输入、按字段（默认空白分割）处理的脚本语言。`$1`~`$NF` 表示各字段，`-F` 指定分隔符，`BEGIN/END` 是首尾处理块。常用来做列抽取、求和统计、格式化输出、报告生成。gawk 是 GNU 增强版。

## 示例

```bash
awk '{print $1, $NF}' file.txt
awk -F: '{print $1}' /etc/passwd
awk '{sum+=$1} END {print sum}' data.txt
awk '$3 > 100' file.txt
awk -F, 'NR>1 {print $1, $3}' data.csv
```
