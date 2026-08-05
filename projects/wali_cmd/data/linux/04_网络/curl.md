---
name: curl
category: 网络请求
syntax: "curl [options] URL"
tags: ["HTTP", "下载", "网络"]
aliases: []
level: 入门
popularity: 92
---

命令行数据传输工具，支持 HTTP/HTTPS/FTP/SCP/SFTP 等多种协议。`-O` 按 URL 保存文件，`-L` 跟随重定向，`-I` 只看响应头，`-d` POST 数据，`-H` 自定义 header，`-X` 指定方法，`-k` 跳过证书校验，`-u` 用户认证。API 调试与下载必备。

## 示例

```bash
curl -I https://example.com
curl -O https://example.com/file.zip
curl -L -o page.html https://example.com
curl -X POST -d '{"name":"bob"}' -H "Content-Type: application/json" http://api.example.com/users
curl -u user:pass ftp://ftp.example.com/file
```
