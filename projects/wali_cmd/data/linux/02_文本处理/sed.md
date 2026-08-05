---
name: sed
category: 文本替换
syntax: "sed [options] 'script' [input-file...]"
tags: ["替换", "流编辑", "文本"]
aliases: []
level: 进阶
popularity: 85
---

流编辑器，按脚本对输入的每一行做替换/删除/打印/插入等操作。常用 `s/old/new/g` 替换，`-i` 直接修改文件，`-n` 静默模式（配合 `p` 打印指定行），`-E` 扩展正则。默认输出到 stdout，原文件不动。

## 示例

```bash
sed 's/old/new/g' file.txt
sed -i 's/foo/bar/g' file.txt
sed -n '10,20p' file.txt
sed -i '/^#/d' config.txt
sed -E 's/([0-9]+)/[\1]/g' data.txt
```
