import os
import tempfile
from scripts.markdown_parser import parse_command_file, parse_frontmatter


def test_parse_frontmatter_basic():
    text = """---
name: find
category: 文件查找
tags: ["搜索", "文件系统"]
level: 入门
popularity: 90
---

body content"""
    result = parse_frontmatter(text)
    assert result["name"] == "find"
    assert result["category"] == "文件查找"
    assert result["tags"] == ["搜索", "文件系统"]
    assert result["level"] == "入门"
    assert result["popularity"] == 90


def test_parse_command_file_full():
    content = """---
name: find
category: 文件查找
syntax: "find [path] [options] [expression]"
tags: ["搜索", "文件系统"]
aliases: []
level: 入门
popularity: 90
---

递归搜索目录树，按名称/大小/时间等条件过滤文件。

## 示例

```bash
find /home -name '*.txt'
find . -size +100M
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        path = f.name
    try:
        result = parse_command_file(path)
        assert result["name"] == "find"
        assert result["category"] == "文件查找"
        assert result["syntax"] == "find [path] [options] [expression]"
        assert result["description"] == "递归搜索目录树，按名称/大小/时间等条件过滤文件。"
        assert len(result["example"]) == 2
        assert "find /home" in result["example"][0]
        assert "find . -size" in result["example"][1]
    finally:
        os.unlink(path)


def test_parse_command_file_default_values():
    content = """---
name: ls
---

列出目录内容。
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        path = f.name
    try:
        result = parse_command_file(path)
        assert result["name"] == "ls"
        assert result["tags"] == []
        assert result["aliases"] == []
        assert result["example"] == []
        assert result["popularity"] == 0
    finally:
        os.unlink(path)