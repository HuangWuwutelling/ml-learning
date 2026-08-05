---
name: ssh
category: 远程登录
syntax: "ssh [options] [user@]host [command]"
tags: ["SSH", "远程", "网络"]
aliases: []
level: 入门
popularity: 90
---

OpenSSH 远程登录客户端，建立加密通道登录远程主机或执行命令。`-p` 指定端口（默认 22），`-i` 指定私钥文件，`-L` 本地端口转发，`-D` 动态转发（SOCKS 代理），`-N` 不执行远程命令，`-t` 强制分配 tty。`~/.ssh/config` 可配置别名简化参数。

## 示例

```bash
ssh user@host
ssh -p 2222 user@host
ssh -i ~/.ssh/id_ed25519 user@host
ssh user@host "ls -la /var/log"
ssh -L 8080:localhost:80 user@host
```
