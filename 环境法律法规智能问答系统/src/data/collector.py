"""
环境法律法规数据收集模块
从《中华人民共和国生态环境法典》DOCX 文件提取文本数据
"""

import os
import json
import re
from pathlib import Path

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")

# 生态环境法典 DOCX 文件名
CODEC_DOCX = "中华人民共和国生态环境法典_20260312.docx"


def extract_from_docx(docx_path: str) -> str:
    """从 DOCX 文件中提取法典全文"""
    try:
        import docx
    except ImportError:
        raise ImportError("需要安装 python-docx: pip install python-docx")

    doc = docx.Document(docx_path)
    paragraphs = doc.paragraphs

    # 找到正文起始位置（跳过标题、日期、目录）
    # 正文从 第一编 总则 / 第一章 一般规定 开始
    content_start = 0
    toc_markers_seen = 0
    for i, p in enumerate(paragraphs):
        text = p.text.strip()
        # 跳过目录：找到第二个"第一编 总则"之后的内容（第一个在目录中）
        if text == "第一编　总则":
            toc_markers_seen += 1
            if toc_markers_seen == 2:
                content_start = i
                break

    # 如果没有找到，从第一个"第一编"开始
    if content_start == 0:
        for i, p in enumerate(paragraphs):
            if p.text.strip() == "第一编　总则":
                content_start = i
                break

    lines = []
    for p in paragraphs[content_start:]:
        text = p.text.strip()
        if text:
            lines.append(text)

    return "\n".join(lines)


def get_codec_text() -> str:
    """获取生态环境法典全文"""
    docx_path = os.path.join(RAW_DIR, CODEC_DOCX)
    if not os.path.exists(docx_path):
        # 从项目根目录查找
        docx_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data", "raw", CODEC_DOCX
        )

    if not os.path.exists(docx_path):
        raise FileNotFoundError(
            f"未找到《中华人民共和国生态环境法典》文件，请将 {CODEC_DOCX} 放入 data/raw/ 目录"
        )

    return extract_from_docx(docx_path)


def save_raw_text(output_dir=None):
    """将法典全文保存到文件"""
    if output_dir is None:
        output_dir = RAW_DIR
    os.makedirs(output_dir, exist_ok=True)

    text = get_codec_text()
    save_path = os.path.join(output_dir, "中华人民共和国生态环境法典.txt")
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(text)

    # 保存索引
    index_path = os.path.join(output_dir, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(["中华人民共和国生态环境法典"], f, ensure_ascii=False, indent=2)

    return [save_path]


if __name__ == "__main__":
    files = save_raw_text()
    print(f"已保存法典文本到 {files[0]}")
    # 统计字数
    text = open(files[0], "r", encoding="utf-8").read()
    articles = re.findall(r'第[一二三四五六七八九十百千零]+条', text)
    print(f"总字数: {len(text):,} 字")
    print(f"总条数: {len(articles)} 条")
