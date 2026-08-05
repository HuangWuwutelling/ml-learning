---
name: find
category: 文件查找
syntax: "find [path] [expression]"
tags: ["搜索", "文件系统"]
aliases: []
level: 入门
popularity: 95
---

递归搜索目录树，按名称/大小/时间/类型等条件过滤文件或目录。GNU find 支持丰富的表达式（test、action、operator），是日常排查、日志归档、清理大文件时最常用的工具。

## 示例

```bash
find /home -name '*.txt'
find . -type f -name '*.py'
find . -size +100M
find . -mtime -7
find . -maxdepth 2 -name '*.log' -delete
```
