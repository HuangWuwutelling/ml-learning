---
name: cp
category: 文件复制
syntax: "cp [options] source... dest"
tags: ["复制", "文件"]
aliases: []
level: 入门
popularity: 95
---

复制文件和目录。`-r` 递归复制目录，`-i` 覆盖前提示，`-v` 显示详情，`-p` 保留权限/时间戳，`-u` 只在源较新时覆盖。批量复制多个文件时 dest 必须是已存在的目录。

## 示例

```bash
cp file.txt backup.txt
cp -r src/ dst/
cp -i *.txt /target/
cp -p /etc/passwd ./passwd.bak
cp -rv /var/log/ ./logs/
```
