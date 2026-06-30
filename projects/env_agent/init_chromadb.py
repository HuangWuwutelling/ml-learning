"""
初始化 env_Agent 本地 ChromaDB。

从两份排污许可核心法规 HTML 文件中提取正文 → 分块 → BGE 嵌入 → 写入 ChromaDB。
数据存储在 projects/env_agent/data/chroma_db/，供 lookup_regulation 工具检索。

运行方式（从项目根目录）：
    python projects/env_agent/init_chromadb.py
"""

import os
import sys
import re
import hashlib
import io
import shutil
from html.parser import HTMLParser

# HuggingFace 模型缓存（BGE 已缓存在 D:\Workspace\.cache\huggingface）
# 显式设置 + 离线模式，避免中国网络访问 HuggingFace 超时
os.environ["HF_HOME"] = os.path.expanduser("D:\\Workspace\\.cache\\huggingface")
os.environ["HF_HUB_CACHE"] = os.path.join(os.environ["HF_HOME"], "hub")
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# Windows 终端编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ── 路径配置 ──

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")
COLLECTION_NAME = "env_laws"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

HTML_FILES = [
    {
        "name": "排污许可管理办法",
        "path": os.path.join(DATA_DIR, "排污许可管理办法.html"),
        "law_name": "排污许可管理办法",
        "source": "生态环境部部令 第32号 (2024)",
    },
    {
        "name": "排污许可管理条例",
        "path": os.path.join(DATA_DIR, "排污许可管理条例_中华人民共和国生态环境部.html"),
        "law_name": "排污许可管理条例",
        "source": "国务院令 第736号 (2021)",
    },
]


# ── HTML 正文提取 ──

class TextExtractor(HTMLParser):
    """提取 HTML 正文，跳过脚本/样式/导航等非内容区域。"""

    # 只含容器元素，不含 void 元素（如 meta、link 是 void，没有 endtag）
    SKIP_TAGS = {"script", "style", "head", "noscript"}
    BLOCK_TAGS = {
        "p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "tr", "li", "td", "th", "section", "blockquote",
    }

    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif tag in self.BLOCK_TAGS and self.skip_depth == 0:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)

    def handle_data(self, data):
        if self.skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.parts.append(stripped)


def extract_text(filepath: str) -> str:
    """读取 HTML 文件，返回干净的纯文本。"""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    parser = TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts)

    # 清理
    text = text.replace("\xa0", " ")           # &nbsp; → 空格
    text = re.sub(r"[ \t]+", " ", text)        # 压缩行内空白
    text = re.sub(r"\n{3,}", "\n\n", text)     # 压缩空行
    text = text.strip()

    return text


# ── 文本分块 ──

def chunk_text(text: str, law_name: str, source: str) -> list[dict]:
    """按章节→条款层级拆分，合并为约 CHUNK_SIZE 字一块，带 CHUNK_OVERLAP 重叠。"""
    chunks = []

    # 第1层：按章拆分
    sections = re.split(r"(第[一二三四五六七八九十百千零]+章\s*[^\n]*)", text)
    if len(sections) <= 1:
        sections = [text]

    step = 2 if len(sections) > 1 else 1
    start = 1 if len(sections) > 1 else 0

    for i in range(start, len(sections), step):
        if len(sections) > 1:
            header = sections[i].strip()
            body = sections[i + 1].strip() if i + 1 < len(sections) else ""
            section_text = header + "\n" + body
        else:
            section_text = sections[i]

        # 第2层：按条拆分
        articles = re.split(r"(第[一二三四五六七八九十百千零]+条)", section_text)

        paragraphs = []
        for j in range(0, len(articles) - 1, 2):
            paragraphs.append((articles[j] + articles[j + 1]).strip())
        if len(articles) % 2 == 1 and articles[-1].strip():
            paragraphs.append(articles[-1].strip())

        if not paragraphs:
            paragraphs = [section_text.strip()]

        # 第3层：合并短段落
        current = []
        cur_len = 0
        for para in paragraphs:
            para_len = len(para)
            if cur_len + para_len > CHUNK_SIZE and current:
                block = "\n".join(current)
                chunks.append(_make_entry(block, law_name, source))

                # 保留尾部段落作为 overlap
                retain = []
                retain_len = 0
                for p in reversed(current):
                    if retain_len + len(p) < CHUNK_OVERLAP:
                        retain.insert(0, p)
                        retain_len += len(p)
                    else:
                        break
                current = retain
                cur_len = retain_len

            current.append(para)
            cur_len += para_len

        if current:
            block = "\n".join(current)
            chunks.append(_make_entry(block, law_name, source))

    return chunks


def _make_entry(text: str, law_name: str, source: str) -> dict:
    """构建文档块条目，附带元数据。"""
    meta = {"law_name": law_name, "source": source}
    ch = re.search(r"第[一二三四五六七八九十百千零]+章", text)
    if ch:
        meta["chapter"] = ch.group()
    art = re.search(r"第[一二三四五六七八九十百千零]+条", text)
    if art:
        meta["article"] = art.group()
    return {"text": text, "metadata": meta}


# ── 主流程 ──

def main():
    print("=" * 54)
    print("  env_Agent — ChromaDB 初始化")
    print("  排污许可管理办法 + 排污许可管理条例")
    print("=" * 54)

    # ── 1. 提取 + 分块 ──
    all_chunks = []
    for info in HTML_FILES:
        if not os.path.isfile(info["path"]):
            print(f"\n! 文件不存在，跳过：{info['path']}")
            continue

        print(f"\n[1/3] 处理：{info['name']}")
        print(f"      文件：{info['path']}")

        text = extract_text(info["path"])
        print(f"      正文：{len(text):,} 字")

        chunks = chunk_text(text, info["law_name"], info["source"])
        print(f"      分块：{len(chunks)} 块")

        all_chunks.extend(chunks)

    if not all_chunks:
        print("\n! 没有可处理的文件，退出。")
        sys.exit(1)

    print(f"\n    共计：{len(all_chunks)} 个文档块")

    # ── 2. 向量化 ──
    print(f"\n[2/3] 加载嵌入模型：{EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [c["text"] for c in all_chunks]
    # BGE 规则：存库不加前缀，查询时才加
    embeddings = model.encode(texts, show_progress_bar=True)
    print(f"      向量维度：{embeddings.shape[1]}")

    # ── 3. 写入 ChromaDB ──

    # 完全重建：先删旧库避免脏数据累积
    if os.path.isdir(CHROMA_DB_DIR):
        shutil.rmtree(CHROMA_DB_DIR)
        print(f"\n[3/3] 清除旧数据库")
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    print(f"[3/3] 写入 ChromaDB：{CHROMA_DB_DIR}")
    client = chromadb.PersistentClient(
        path=CHROMA_DB_DIR,
        settings=Settings(anonymized_telemetry=False),
    )

    collection = client.create_collection(COLLECTION_NAME)

    # 生成唯一 ID
    ids = []
    seen = set()
    for i, c in enumerate(all_chunks):
        h = hashlib.md5(f"{i}_{c['text']}".encode("utf-8")).hexdigest()[:16]
        while h in seen:
            h = hashlib.md5(f"{h}_{i}".encode()).hexdigest()[:16]
        seen.add(h)
        ids.append(h)

    collection.add(
        documents=[c["text"] for c in all_chunks],
        metadatas=[c["metadata"] for c in all_chunks],
        embeddings=embeddings.tolist(),
        ids=ids,
    )

    count = collection.count()
    print(f"      已写入 {count} 个文档块")
    print(f"      集合：{COLLECTION_NAME}")

    # ── 验证 ──
    print(f"\n{'=' * 54}")
    print("  验证")
    print(f"  ChromaDB 文档数：{count}")

    test_cases = [
        "排污许可证申请需要什么材料",
        "排污许可证有效期多久",
        "什么情况下需要变更排污许可证",
        "无证排污的处罚是什么",
    ]
    for q in test_cases:
        q_vec = model.encode(
            f"为这个句子生成表示以用于检索相关文章：{q}"
        ).tolist()
        results = collection.query(query_embeddings=[q_vec], n_results=1)
        doc = results["documents"][0][0] if results["documents"][0] else "(无结果)"
        src = results["metadatas"][0][0].get("law_name", "?") if results["metadatas"][0] else "?"
        print(f"  ? {q}")
        print(f"    -> [{src}] {doc[:80]}...")

    print(f"\n{'=' * 54}")
    print(f"  OK  ChromaDB 初始化完成")
    print(f"  路径：{CHROMA_DB_DIR}")
    print(f"  说明：config.py 中 CHROMA_DB_PATH 已指向本地 ChromaDB")
    print(f"{'=' * 54}")


if __name__ == "__main__":
    main()
