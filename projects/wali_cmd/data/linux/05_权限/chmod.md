---
name: chmod
category: 权限修改
syntax: "chmod [options] MODE FILE..."
tags: ["权限", "文件"]
aliases: []
level: 入门
popularity: 92
---

修改文件/目录的访问权限。MODE 两种写法：八进制数字（r=4、w=2、x=1，如 755 = rwxr-xr-x）或符号（u/g/o/a 配 +/-/= 与 r/w/x）。`-R` 递归。常见组合：脚本 755、配置文件 644、SSH 私钥 600。

## 示例

```bash
chmod 755 script.sh
chmod +x script.sh
chmod -R 644 dir/
chmod u+rw,g-r file.txt
chmod 600 ~/.ssh/id_rsa
```
