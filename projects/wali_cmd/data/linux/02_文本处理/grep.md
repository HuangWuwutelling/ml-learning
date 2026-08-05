---
name: grep
category: 文本搜索
syntax: "grep [options] PATTERN [FILE...]"
tags: ["搜索", "正则", "文本"]
aliases: []
level: 入门
popularity: 98
---

按模式（默认基本正则）在文件或 stdin 中查找匹配行并输出。`-i` 忽略大小写，`-r` 递归目录，`-n` 显示行号，`-c` 统计次数，`-v` 反向匹配，`-E` 扩展正则，`--color` 高亮匹配。GNU grep 是日志排查的瑞士军刀。

## 示例

```bash
grep -rn "TODO" --include="*.py" .
grep -i "error" log.txt
grep -c "404" access.log
grep -E "warn|error" app.log
grep -v "^#" /etc/ssh/sshd_config
```
