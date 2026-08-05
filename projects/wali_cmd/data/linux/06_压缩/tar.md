---
name: tar
category: 打包归档
syntax: "tar [options] [archive] [file...]"
tags: ["压缩", "打包", "归档"]
aliases: []
level: 入门
popularity: 90
---

归档工具，常与 gzip/bzip2/xz 组合实现打包+压缩。主选项：`c` 创建、`x` 解压、`t` 列表、`v` 详细、`f` 指定文件、`z` gzip、`j` bzip2、`J` xz。GNU tar 通过后缀自动识别格式，可省略压缩选项。

## 示例

```bash
tar czf archive.tar.gz dir/
tar cjf archive.tar.bz2 dir/
tar xzf archive.tar.gz
tar xf archive.tar.gz -C /target/
tar tf archive.tar.gz
```
