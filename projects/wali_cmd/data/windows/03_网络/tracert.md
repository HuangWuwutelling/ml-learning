---
name: tracert
category: 网络
syntax: "tracert [-d] [-h <max_hops>] [-w <timeout>] [-4 | -6] <target>"
tags: ["网络", "诊断", "路由"]
aliases: []
level: 入门
popularity: 70
---

跟踪到目标主机的路由路径，显示每一跳的 RTT 和节点 IP。Linux 中 `traceroute` 的等价命令。`-d` 不解析主机名（更快），`-h <n>` 限制最大跳数，`-w <n>` 设置等待回应的超时（毫秒），`-4`/`-6` 强制使用 IPv4/IPv6。

## 示例

```cmd
tracert 8.8.8.8
tracert -d example.com
tracert -h 20 1.1.1.1
tracert -6 ipv6.google.com
```
