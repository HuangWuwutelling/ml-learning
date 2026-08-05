---
name: chown
category: 所有权修改
syntax: "chown [options] [OWNER][:[GROUP]] FILE..."
tags: ["权限", "所有者", "文件"]
aliases: []
level: 入门
popularity: 80
---

修改文件/目录的所有者和所属组。`OWNER` 改所有者，`OWNER:GROUP` 同时改两者，`:GROUP` 只改组（用户名留空）。`-R` 递归。常需要 `sudo` 提升权限。

## 示例

```bash
chown user file.txt
chown user:group file.txt
sudo chown -R www-data:www-data /var/www/
chown :devs project/
sudo chown -R root:root /etc/
```
