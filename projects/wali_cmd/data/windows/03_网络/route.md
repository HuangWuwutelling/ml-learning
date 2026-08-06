---
name: route
category: 网络
syntax: "route [-f] [-4|-6] PRINT | ADD | CHANGE | DELETE [destination_host] [MASK subnet_mask_value] [gateway] [METRIC metric] [IF interface_no.]"
tags: ["网络", "路由", "表"]
aliases: []
level: 进阶
popularity: 45
---

显示和修改网络路由表，控制数据包如何在子网间转发。`PRINT` 显示路由，`ADD` 添加，`CHANGE` 修改（只能改 gateway/metric），`DELETE` 删除。`-p` 创建永久路由（系统重启仍然存在），否则路由重启失效。`-4`/`-6` 强制 IPv4/IPv6；`-f` 配合使用时清空路由表再执行。

## 示例

```cmd
route PRINT
route PRINT -4
route ADD 10.0.0.0 MASK 255.0.0.0 192.168.1.1 METRIC 1
route ADD -p 0.0.0.0 MASK 0.0.0.0 192.168.1.1
route DELETE 10.0.0.0
```
