---
name: cat
category: 文件查看
syntax: "cat [options] [file...]"
tags: ["查看", "拼接", "文件"]
aliases: []
level: 入门
popularity: 95
---

把一个或多个文件内容输出到 stdout（POSIX 中是 concatenate 拼接）。`-n` 显示行号，`-b` 只对非空行编号，`-A` 显示制表符/行尾等不可见字符。大文件用 `less`/`more` 更合适。

## 示例

```bash
cat file.txt
cat -n file.txt
cat file1.txt file2.txt
cat src/*.md > all.md
cat -A data.csv
```
