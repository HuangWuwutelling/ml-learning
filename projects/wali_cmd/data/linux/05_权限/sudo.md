---
name: sudo
category: 特权执行
syntax: "sudo [options] command"
tags: ["权限", "提权", "root"]
aliases: []
level: 入门
popularity: 95
---

以超级用户（root）或其他用户的身份执行命令，前提是当前用户在 `/etc/sudoers` 中被授权。`-u` 指定目标用户，`-i` 启动登录 shell（加载 .profile 等），`-s` 启动非登录 shell，`-E` 保留环境变量。`!!` 可重跑上一条命令并加 sudo。

## 示例

```bash
sudo apt update
sudo !!
sudo -i
sudo -u postgres psql
sudo systemctl restart nginx
sudo -E bash -c 'echo $PATH'
```
