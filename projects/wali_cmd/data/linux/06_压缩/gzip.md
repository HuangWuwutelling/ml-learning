---
name: gzip
category: 压缩解压
syntax: "gzip [options] file..."
tags: ["压缩", "gzip"]
aliases: []
level: 入门
popularity: 75
---

GNU 单文件压缩工具，使用 LZ77 + Huffman，输出 `.gz` 后缀（默认会删除原文件）。`-k` 保留原文件，`-d` 解压（等同 `gunzip`），`-c` 输出到 stdout，`-1`~`-9` 调压缩率（默认 6）。`zcat` 直接查看压缩文件内容不解压。

## 示例

```bash
gzip file.txt
gzip -k file.txt
gzip -d file.txt.gz
gzip -c file.txt > file.txt.gz
zcat file.txt.gz
```
