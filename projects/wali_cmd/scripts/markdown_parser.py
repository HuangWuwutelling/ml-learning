"""解析命令 markdown 文件为 dict。"""
import re
from pathlib import Path
from typing import Any

import frontmatter
from markdown_it import MarkdownIt


def parse_frontmatter(text: str) -> dict[str, Any]:
    """解析 frontmatter 文本为 dict。"""
    post = frontmatter.loads(text)
    return dict(post.metadata)


def parse_command_file(path: str) -> dict[str, Any]:
    """解析命令 markdown 文件为结构化 dict。

    Returns:
        dict with keys: name, platform, category, subcategory, syntax,
        example (list[str]), description, tags (list[str]),
        aliases (list[str]), level, popularity (int)
    """
    md_path = Path(path)
    text = md_path.read_text(encoding="utf-8")

    # 解析 frontmatter
    meta = parse_frontmatter(text)
    body = frontmatter.loads(text).content

    # 平台从路径推断：data/linux/xxx.md → linux, data/windows/xxx.md → windows
    platform = "linux" if "/linux/" in str(md_path) else "windows"

    # 提取 description：body 第一段（非 ## 开头的段落）
    description = ""
    example: list[str] = []
    syntax = meta.get("syntax", "")

    md = MarkdownIt()
    tokens = md.parse(body)

    in_example = False
    current_para: list[str] = []

    for tok in tokens:
        if tok.type == "heading_open" and tok.tag == "h2":
            # 切到下一个 h2 之前的段落
            if current_para and not description:
                description = "".join(current_para).strip()
            current_para = []
            in_example = False
        elif tok.type == "heading_close":
            pass
        elif tok.type == "inline":
            txt = tok.content
            # 检查是否进入示例区
            if "示例" in txt:
                in_example = True
                continue
            if in_example and tok.children and tok.children[0].type == "code_inline":
                example.append(txt)
            else:
                current_para.append(txt)
        elif tok.type == "fence" or tok.type == "code_block":
            if in_example:
                for line in tok.content.strip().split("\n"):
                    line = line.strip()
                    if line:
                        example.append(line)

    # 收尾：如果还没填上 description
    if not description and current_para:
        description = "".join(current_para).strip()

    # syntax 兜底：从 description 第一句截取
    if not syntax and description:
        syntax = description.split("\n")[0].split("。")[0]

    return {
        "name": meta.get("name", md_path.stem),
        "platform": platform,
        "category": meta.get("category", "未分类"),
        "subcategory": meta.get("subcategory", ""),
        "syntax": syntax,
        "example": example,
        "description": description,
        "tags": meta.get("tags", []),
        "aliases": meta.get("aliases", []),
        "level": meta.get("level", "入门"),
        "popularity": int(meta.get("popularity", 0)),
    }