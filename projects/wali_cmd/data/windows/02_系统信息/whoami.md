---
name: whoami
category: 系统信息
syntax: "whoami [/upn | /fqdn | /logonid | /user | /groups | /priv | /all]"
tags: ["用户", "权限"]
aliases: []
level: 入门
popularity: 80
---

显示当前用户的详细信息。`/groups` 列出所属用户组，`/priv` 列出用户权限（含 SeDebugPrivilege 等），`/all` 显示全部信息。常用场景：排查权限问题（脚本失败 / 访问拒绝），确认当前身份。

## 示例

```cmd
whoami
whoami /groups
whoami /priv
whoami /all
```
