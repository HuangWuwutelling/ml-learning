---
name: netstat
category: 网络
syntax: "netstat [-a] [-b] [-e] [-n] [-o] [-p <proto>] [-r] [-s]"
tags: ["网络", "连接", "端口"]
aliases: []
level: 进阶
popularity: 70
---

显示活动的 TCP 连接、监听端口、网卡统计、IP 路由表、IPv4/IPv6 协议统计。`-a` 显示所有连接和监听端口，`-n` 数字形式显示地址和端口（不解析域名，跳 DNS 更快），`-o` 显示关联的进程 PID，`-b` 显示使用该连接的进程（需要管理员权限）。

## 示例

```cmd
netstat
netstat -an
netstat -ano
netstat -ano | findstr :80
netstat -r
```
