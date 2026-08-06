---
name: set
category: 系统信息
syntax: "set [/p] <variable>=<string>"
tags: ["环境变量", "配置"]
aliases: []
level: 入门
popularity: 75
---

显示或设置 cmd 的环境变量。不带任何参数时列出当前所有环境变量；`set VAR=value` 把变量设为指定值；`set VAR` 列出以 VAR 开头的所有变量（用于查询）；`set /p VAR=prompt` 提示用户输入并把输入存入变量。注意：cmd 中默认是会话级变量，关闭 cmd 即消失；要持久化用 `setx`。

## 示例

```cmd
set
set PATH
set MY_VAR=hello
set /p ANSWER=Enter your choice:
```
