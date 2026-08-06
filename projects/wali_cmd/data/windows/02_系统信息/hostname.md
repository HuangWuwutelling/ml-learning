---
name: hostname
category: 系统信息
syntax: "hostname"
tags: ["系统", "主机名"]
aliases: []
level: 入门
popularity: 70
---

显示计算机的主机名（全计算机名中的主机名部分）。除 `/?` 外不接受任何参数；任何其他参数都会产生错误并把 errorlevel 设为 1。`%COMPUTERNAME%` 环境变量通常打印相同字符串但为大写；如果定义了 `_CLUSTER_NETWORK_NAME_` 环境变量，则打印该值。

## 示例

```cmd
hostname
echo %COMPUTERNAME%
```
