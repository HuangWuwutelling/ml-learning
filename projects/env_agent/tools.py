"""Tool functions for environmental compliance Agent."""
import json
import sqlite3
import os

# HuggingFace 离线加载（BGE 已缓存在 D:\Workspace\.cache\huggingface）
os.environ.setdefault("HF_HOME", os.path.expanduser("D:\\Workspace\\.cache\\huggingface"))
os.environ.setdefault("HF_HUB_CACHE", os.path.join(os.environ["HF_HOME"], "hub"))
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from typing import Optional

import numpy as np
from langchain_core.tools import tool
from sentence_transformers import SentenceTransformer

from config import config

# ── Lazy-loaded embedding model ──

_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _embedder


# ── ChromaDB SQLite document loader ──

_CHROMA_DB_PATH = os.path.join(
    config.CHROMA_DB_PATH, "chroma.sqlite3"
)
_EMBEDDINGS_CACHE_PATH = os.path.join(
    config.CHROMA_DB_PATH, "..", "embeddings_cache.npz"
)


def _load_docs_from_chromadb():
    """Load document chunks directly from ChromaDB SQLite (bypass Python API bug)."""
    db_path = _CHROMA_DB_PATH
    if not os.path.isfile(db_path):
        print(f"ChromaDB not found at {db_path}, using fallback documents")
        return FALLBACK_DOCUMENTS

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # embedding_metadata stores document text as 'chroma:document' and chunk metadata
        cursor.execute("""
            SELECT em.string_value, em2.string_value, em3.string_value
            FROM embedding_metadata em
            LEFT JOIN embedding_metadata em2 ON em.id = em2.id AND em2.key = 'law_name'
            LEFT JOIN embedding_metadata em3 ON em.id = em3.id AND em3.key = 'source'
            WHERE em.key = 'chroma:document'
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No documents found in ChromaDB, using fallback")
            return FALLBACK_DOCUMENTS

        docs = []
        for text, law_name, source in rows:
            if not text or not text.strip():
                continue
            docs.append({
                "content": text.strip(),
                "metadata": {
                    "source": source or "中华人民共和国生态环境法典",
                    "law_name": law_name or "中华人民共和国生态环境法典",
                },
            })

        print(f"Loaded {len(docs)} documents from ChromaDB ({os.path.basename(db_path)})")
        return docs

    except Exception as e:
        print(f"Error loading ChromaDB: {e}, using fallback documents")
        return FALLBACK_DOCUMENTS


# ── In-memory document store ──

_documents = None
_doc_embeddings = None


def _get_documents():
    """Load documents from ChromaDB SQLite, falling back to built-in data."""
    global _documents
    if _documents is not None:
        return _documents
    _documents = _load_docs_from_chromadb()
    return _documents


def _get_doc_embeddings():
    """Get cached document embeddings, loading from disk cache or computing on first call."""
    global _doc_embeddings
    if _doc_embeddings is not None:
        return _doc_embeddings

    docs = _get_documents()
    doc_texts = [d["content"] for d in docs]
    n_docs = len(doc_texts)

    # Try loading from .npz cache
    cache_path = os.path.abspath(_EMBEDDINGS_CACHE_PATH)
    if os.path.isfile(cache_path):
        try:
            data = np.load(cache_path)
            if data["doc_count"] == n_docs and data["embeddings"].shape[0] == n_docs:
                _doc_embeddings = data["embeddings"]
                print(f"Loaded {n_docs} embeddings from cache ({cache_path})")
                return _doc_embeddings
            else:
                print(f"Cache stale (docs: {n_docs} vs cached: {data['doc_count']}), recomputing...")
        except Exception as e:
            print(f"Cache load failed ({e}), recomputing...")

    # Compute embeddings
    embedder = _get_embedder()
    _doc_embeddings = embedder.encode(doc_texts, show_progress_bar=False)
    print(f"Computed {len(_doc_embeddings)} document embeddings")

    # Save to cache
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        np.savez(cache_path, embeddings=_doc_embeddings, doc_count=n_docs)
        print(f"Saved embeddings to cache ({cache_path})")
    except Exception as e:
        print(f"Cache save failed ({e}), continuing without cache")

    return _doc_embeddings


def _search_documents(query: str, top_k: int = 3):
    """Search documents by embedding similarity."""
    docs = _get_documents()
    if not docs:
        return []

    embedder = _get_embedder()
    query_vec = embedder.encode(
        f"为这个句子生成表示以用于检索相关文章：{query}"
    )
    doc_vecs = _get_doc_embeddings()

    cos_sim = np.dot(doc_vecs, query_vec) / (
        np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec) + 1e-8
    )

    top_indices = np.argsort(cos_sim)[-top_k:][::-1]
    results = []
    for idx in top_indices:
        results.append({
            "content": docs[idx]["content"],
            "metadata": docs[idx]["metadata"],
            "score": float(cos_sim[idx]),
        })
    return results


# ── Emission factor data (for demo) ──

EMISSION_FACTORS = {
    "印染": {
        "废水": {"unit": "吨/天", "cod": 200, "nh3": 15, "description": "印染废水含 COD、氨氮、色度等污染物"},
        "废气": {"unit": "m³/h", "so2": 50, "nox": 30, "description": "定型机废气含 SO₂、NOₓ"},
    },
    "化工": {
        "废水": {"unit": "吨/天", "cod": 100, "nh3": 40, "description": "化工（石油化学）废水成分复杂，含高浓度 COD"},
        "废气": {"unit": "m³/h", "so2": 100, "nox": 80, "description": "化工废气含 SO₂、NOₓ、VOCs"},
    },
    "造纸": {
        "废水": {"unit": "吨/天", "cod": 100, "nh3": 10, "description": "造纸废水含 COD、悬浮物"},
        "废气": {"unit": "m³/h", "so2": 80, "nox": 60, "description": "造纸锅炉废气含 SO₂、NOₓ"},
    },
    "钢铁": {
        "废水": {"unit": "吨/天", "cod": 100, "nh3": 20, "description": "钢铁废水含悬浮物、重金属"},
        "废气": {"unit": "m³/h", "so2": 200, "nox": 150, "description": "烧结、炼焦废气含大量 SO₂"},
    },
    "污水处理厂": {
        "废水": {"unit": "万吨/天", "cod": 50, "nh3": 5, "description": "污水处理厂出水执行一级A标准"},
        "废气": {"unit": "m³/h", "so2": 0, "nox": 0, "description": "主要污染物为恶臭气体"},
    },
}

EMISSION_STANDARDS = {
    "印染": "《纺织染整工业水污染物排放标准》(GB 4287-2012) 间接排放：COD ≤ 200 mg/L，NH₃-N ≤ 20 mg/L",
    "化工": "《石油化学工业污染物排放标准》(GB 31571-2015) 间接排放：COD ≤ 100 mg/L，NH₃-N ≤ 40 mg/L",
    "造纸": "《制浆造纸工业水污染物排放标准》(GB 3544-2008) 表2标准：COD ≤ 100 mg/L，NH₃-N ≤ 10 mg/L",
    "钢铁": "《钢铁工业水污染物排放标准》(GB 13456-2012) 间接排放：COD ≤ 100 mg/L，NH₃-N ≤ 15 mg/L",
    "污水处理厂": "《城镇污水处理厂污染物排放标准》(GB 18918-2002) 一级A标准 COD ≤ 50 mg/L，NH₃-N ≤ 5 mg/L",
}


def _match_industry(industry: str) -> Optional[str]:
    """匹配行业类型，精确匹配优先，较长关键字优先避免误匹配。"""
    if industry in EMISSION_FACTORS:
        return industry
    for key in sorted(EMISSION_FACTORS.keys(), key=len, reverse=True):
        if key in industry:
            return key
    return None


# ── Tools ──


# ── Fallback documents if ChromaDB is not available ──

FALLBACK_DOCUMENTS = [
    {"content": "排放污染物的企业事业单位和其他生产经营者，应当采取措施防治环境污染。重点排污单位应当按照国家有关规定和监测规范安装使用监测设备，保证监测设备正常运行，保存原始监测记录。", "metadata": {"source": "通用环保条款"}},
    {"content": "排放水污染物，不得超过国家或者地方规定的水污染物排放标准和重点水污染物排放总量控制指标。", "metadata": {"source": "通用环保条款"}},
    {"content": "直接或者间接向水体排放工业废水和医疗污水以及其他按照规定应当取得排污许可证方可排放的废水、污水的企业事业单位和其他生产经营者，应当取得排污许可证。", "metadata": {"source": "通用环保条款"}},
    {"content": "禁止向水体排放油类、酸液、碱液或者剧毒废液。禁止在水体清洗装贮过油类或者有毒污染物的车辆和容器。", "metadata": {"source": "通用环保条款"}},
    {"content": "向大气排放污染物的单位，应当取得排污许可证。向大气排放污染物的单位，应当按照规定设置大气污染物排放口。", "metadata": {"source": "通用环保条款"}},
    {"content": "纺织染整工业水污染物排放标准(GB 4287-2012)规定：COD排放限值200mg/L，氨氮排放限值20mg/L，pH值6-9，色度80倍。", "metadata": {"source": "纺织染整工业水污染物排放标准"}},
    {"content": "石油化学工业污染物排放标准(GB 31571-2015)规定：COD排放限值100mg/L（间接排放），氨氮排放限值40mg/L（间接排放），总磷排放限值1.0mg/L。", "metadata": {"source": "石油化学工业污染物排放标准"}},
    {"content": "制浆造纸工业水污染物排放标准(GB 3544-2008)规定（表2，新建企业）：COD排放限值100mg/L，氨氮排放限值12mg/L。", "metadata": {"source": "制浆造纸工业水污染物排放标准"}},
    {"content": "钢铁工业水污染物排放标准(GB 13456-2012)规定：COD排放限值100mg/L，氨氮排放限值15mg/L，总铁排放限值10mg/L。", "metadata": {"source": "钢铁工业水污染物排放标准"}},
    {"content": "城镇污水处理厂污染物排放标准(GB 18918-2002)一级A标准：COD≤50mg/L，氨氮≤5mg/L，总磷≤0.5mg/L，总氮≤15mg/L。", "metadata": {"source": "城镇污水处理厂污染物排放标准"}},
]


@tool
def lookup_regulation(query: str) -> str:
    """查询环保法规相关条文。当用户询问排放标准、法规要求时调用此工具。

    Args:
        query: 用户关于环保法规的问题，如"印染行业COD排放限值"
    """
    try:
        results = _search_documents(query, top_k=config.TOP_K)
        if not results:
            return "未找到相关法规条文，请尝试换个关键词查询。"

        output = []
        for r in results:
            source = r["metadata"].get("source", "生态环境法典")
            output.append(f"【来源：{source}】\n{r['content']}\n")
        return "\n---\n".join(output)
    except Exception as e:
        return f"查询法规时出错：{str(e)}"


@tool
def calculate_emission(
    industry: str,
    daily_volume_ton: float,
    has_treatment: Optional[bool] = None,
) -> str:
    """计算企业污染物排放量。根据行业类型和生产规模估算各类污染物排放量。

    Args:
        industry: 行业类型（印染/化工/造纸/钢铁/污水处理厂）
        daily_volume_ton: 废水日排放量（吨/天）
        has_treatment: 是否有配套污水处理设施
    """
    industry_key = _match_industry(industry)
    if not industry_key:
        available = "、".join(EMISSION_FACTORS.keys())
        return f"暂不支持行业「{industry}」，目前支持的行业：{available}"

    factors = EMISSION_FACTORS[industry_key]
    standard = EMISSION_STANDARDS.get(industry_key, "")
    treatment_rate = 0.85 if has_treatment else 0.0

    water = factors["废水"]
    cod_raw = daily_volume_ton * water["cod"] / 1000
    nh3_raw = daily_volume_ton * water["nh3"] / 1000
    cod_emission = cod_raw * (1 - treatment_rate)
    nh3_emission = nh3_raw * (1 - treatment_rate)

    result = (
        f"【{industry_key}行业排放量计算】\n"
        f"废水日排放量：{daily_volume_ton:.0f} 吨/天\n"
        f"污水处理设施：{'有' if has_treatment else '无'}{'（去除率85%）' if has_treatment else ''}\n\n"
        f"COD 排放量：{cod_emission:.2f} kg/天"
        f" {'(已处理)' if has_treatment else '(未处理)'}\n"
        f"氨氮排放量：{nh3_emission:.2f} kg/天"
        f" {'(已处理)' if has_treatment else '(未处理)'}\n\n"
        f"参考标准：{standard}\n"
    )

    if has_treatment:
        result += (
            f"\n处理前 COD：{cod_raw:.2f} kg/天　氨氮：{nh3_raw:.2f} kg/天\n"
            f"处理后 COD：{cod_emission:.2f} kg/天　氨氮：{nh3_emission:.2f} kg/天"
        )

    return result


@tool
def calculate_air_emission(
    industry: str,
    exhaust_volume: float,
    running_hours: float = 720,
) -> str:
    """计算企业废气污染物排放量。根据行业类型和废气量估算 SO₂、NOₓ 月排放量。

    Args:
        industry: 行业类型（印染/化工/造纸/钢铁/污水处理厂）
        exhaust_volume: 废气排放量（m³/h）
        running_hours: 月运行小时数，默认 720（30 天 × 24 小时）
    """
    industry_key = _match_industry(industry)
    if not industry_key:
        available = "、".join(EMISSION_FACTORS.keys())
        return f"暂不支持行业「{industry}」，目前支持的行业：{available}"

    factors = EMISSION_FACTORS[industry_key]
    air = factors.get("废气")
    if not air or (air.get("so2", 0) == 0 and air.get("nox", 0) == 0):
        return f"「{industry_key}」行业暂无废气排放因子数据，暂无法计算废气排放量。"

    so2_rate = air["so2"]
    nox_rate = air["nox"]
    so2_emission = exhaust_volume * so2_rate / 1e6 * running_hours  # kg/月
    nox_emission = exhaust_volume * nox_rate / 1e6 * running_hours  # kg/月

    result = (
        f"【{industry_key}行业废气排放量计算】\n"
        f"废气排放量：{exhaust_volume:.0f} m³/h\n"
        f"月运行时间：{running_hours:.0f} 小时/月\n\n"
        f"SO₂ 排放量：{so2_emission:.2f} kg/月\n"
        f"NOₓ 排放量：{nox_emission:.2f} kg/月\n\n"
        f"说明：{air['description']}\n"
    )
    return result


@tool
def fill_form(data_json: str) -> str:
    """根据已收集的企业信息，生成排污申报表草稿。

    Args:
        data_json: 包含企业信息的 JSON 字符串，支持字段：
            company, contact, industry, apply_type(首次申请/延续/变更/重新申请),
            daily_volume, has_treatment, exhaust_volume, management_category
    """
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        return "数据格式错误，请提供有效的 JSON 格式信息。"

    industry = data.get("industry", "未填写")
    volume = data.get("daily_volume", "未填写")
    treatment = data.get("has_treatment", False)
    contact = data.get("contact", "未填写")
    company = data.get("company", "未填写")
    apply_type = data.get("apply_type", "")
    exhaust = data.get("exhaust_volume", "")
    management = data.get("management_category", "")

    form = (
        f"═══════════════════════════════════════\n"
        f"        排污许可证申报表（草稿）\n"
        f"═══════════════════════════════════════\n\n"
        f"一、企业基本信息\n"
        f"   企业名称：{company}\n"
        f"   联系人：{contact}\n"
        f"   所属行业：{industry}\n"
    )
    if apply_type:
        form += f"   申请类型：{apply_type}\n"
    if management:
        form += f"   管理类别：{management}\n"
    form += (
        f"\n二、排污信息\n"
        f"   废水日排放量：{volume} 吨/天\n"
        f"   污水处理设施：{'有' if treatment else '无'}\n"
    )
    if exhaust:
        form += f"   废气排放量：{exhaust}\n"

    form += "\n三、主要污染物\n"

    if industry in EMISSION_FACTORS:
        factors = EMISSION_FACTORS[industry]
        water = factors["废水"]
        form += (
            f"   - COD：{water['cod']} mg/L\n"
            f"   - 氨氮：{water['nh3']} mg/L\n"
        )

        if industry in EMISSION_STANDARDS:
            form += f"\n   参考标准：{EMISSION_STANDARDS[industry]}\n"

    form += (
        f"\n四、备注\n"
        f"   本表为 AI 自动生成的草稿，请核实后提交。\n"
        f"═══════════════════════════════════════\n"
    )
    return form


@tool
def generate_report(data_json: str) -> str:
    """根据完整的企业信息，生成排污申报报告。

    Args:
        data_json: 包含完整企业信息和排放量计算结果的 JSON 字符串
    """
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        return "数据格式错误，请提供有效的 JSON 格式信息。"

    industry = data.get("industry", "未填写")
    volume = data.get("daily_volume", "未填写")
    company = data.get("company", "未填写")
    contact = data.get("contact", "未填写")
    has_treatment = data.get("has_treatment", False)
    cod_emission = data.get("cod_emission", "待计算")
    nh3_emission = data.get("nh3_emission", "待计算")

    report = (
        f"# 排污许可申报报告\n\n"
        f"## 1. 企业概况\n"
        f"- 企业名称：{company}\n"
        f"- 联系人：{contact}\n"
        f"- 所属行业：{industry}\n"
        f"- 废水日排放量：{volume} 吨/天\n"
        f"- 污水处理设施：{'有' if has_treatment else '无'}\n\n"
        f"## 2. 排放量计算结果\n"
        f"- COD 排放量：{cod_emission} kg/天\n"
        f"- 氨氮排放量：{nh3_emission} kg/天\n\n"
        f"## 3. 执行标准\n"
    )

    if industry in EMISSION_STANDARDS:
        report += f"{EMISSION_STANDARDS[industry]}\n\n"

    report += (
        f"## 4. 结论\n"
        f"已完成排污许可申报材料整理，请核实后提交至当地生态环境局。\n\n"
        f"---\n"
        f"报告生成时间：AI 自动生成\n"
        f"本报告为草稿，需经环保专员确认。\n"
    )
    return report
