---
name: zip
category: 压缩解压
syntax: "zip [options] archive file..."
tags: ["压缩", "zip"]
aliases: []
level: 入门
popularity: 78
---

创建/更新 PKZIP 格式的压缩包，跨平台（Windows/macOS/Linux）兼容性好。`-r` 递归目录，`-e` 加密（提示输入密码），`-9` 最高压缩率，`-@` 从 stdin 读取文件名。解压对应 `unzip`：解压、`-l` 列表、`-d` 指定目录。

## 示例

```bash
zip -r archive.zip dir/
zip -e secret.zip file.txt
zip -9 max.zip file.txt
zip archive.zip file1 file2
unzip archive.zip
```
