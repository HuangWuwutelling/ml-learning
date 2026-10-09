import json
from langchain_core.tools import tool
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path
from qms_app.models import Recall

CHROMA_DIR = str(Path('knowledge/chroma_db'))
EMBEDDING_MODEL = 'BAAI/bge-small-zh-v1.5'

def _get_chroma(collection: str = 'qms_knowledge'):
    embeddings = HuggingFaceBgeEmbeddings(model_name=EMBEDDING_MODEL,
                                          model_kwargs={'device': 'cpu'},
                                          encode_kwargs={'normalize_embeddings': True})
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings,
                  collection_name=collection)

@tool
def assess_severity(complaint_text: str) -> dict:
    """根据投诉文本评估严重程度。
    输入：投诉文本
    输出：{'severity': 'high'|'medium'|'low', 'confidence': 0-1, 'similar_cases': [...]}
    """
    chroma = _get_chroma('recall_history')
    results = chroma.similarity_search_with_score(complaint_text, k=5)
    if not results:
        return {'severity': 'medium', 'confidence': 0.0, 'similar_cases': []}
    # 严重度判定：高=含"起火/触电/中毒/死亡"等高危词；低=小问题；中=其他
    high_kw = ['起火', '触电', '中毒', '死亡', '重伤', '燃烧', '爆炸']
    med_kw = ['烫伤', '划伤', '破损', '失效', '故障']
    if any(kw in complaint_text for kw in high_kw):
        severity = 'high'
        confidence = 0.9
    elif any(kw in complaint_text for kw in med_kw):
        severity = 'medium'
        confidence = 0.7
    else:
        severity = 'low'
        confidence = 0.5
    return {
        'severity': severity, 'confidence': confidence,
        'similar_cases': [{'id': r[0].metadata.get('recall_id'), 'desc': r[0].page_content[:100],
                           'score': float(r[1])} for r in results[:3]],
    }

@tool
def search_recall_history(query: str, top_k: int = 5) -> list[dict]:
    """从历史召回中找相似案例。
    输入：自然语言查询 + top_k
    输出：召回详情列表
    """
    chroma = _get_chroma('recall_history')
    results = chroma.similarity_search(query, k=top_k)
    out = []
    for r in results:
        rid = r.metadata.get('recall_id')
        if rid:
            try:
                rec = Recall.objects.get(id=int(rid))
                out.append({
                    'id': rec.id, 'product': rec.product.name,
                    'defect_description': rec.defect_description,
                    'consequence': rec.consequence, 'remedy': rec.remedy_method,
                    'source_url': rec.source_url, 'recall_date': str(rec.recall_date),
                })
            except (Recall.DoesNotExist, ValueError):
                pass
    return out

@tool
def query_quality_manual(question: str, top_k: int = 3) -> list[dict]:
    """从 GB/T 19001 + CQI 摘要中查相关条款。
    输入：自然语言问题
    输出：Top-K 条款 + 引用
    """
    chroma = _get_chroma('qms_knowledge')
    results = chroma.similarity_search(question, k=top_k,
                                        filter={'doc_id': {'$in': ['gbt_19001', 'cqi_9', 'cqi_11', 'cqi_12']}})
    return [{'content': r.page_content, 'source': r.metadata.get('title'),
             'doc_id': r.metadata.get('doc_id')} for r in results]

@tool
def query_regulation(question: str, top_k: int = 3) -> list[dict]:
    """从 SAMR 官方文件中查监管口径。
    输入：自然语言问题
    输出：Top-K 段落 + 引用
    """
    chroma = _get_chroma('qms_knowledge')
    results = chroma.similarity_search(question, k=top_k,
                                        filter={'doc_id': {'$in': ['samr_2025_stats', 'samr_2025_21']}})
    return [{'content': r.page_content, 'source': r.metadata.get('title'),
             'doc_id': r.metadata.get('doc_id')} for r in results]

@tool
def draft_capa(complaint_summary: str) -> dict:
    """根据投诉摘要起草 CAPA 5W2H 初稿。
    输入：投诉摘要
    输出：5W2H 结构化 JSON
    """
    severity_info = assess_severity.invoke({'complaint_text': complaint_summary})
    similar = search_recall_history.invoke({'query': complaint_summary, 'top_k': 2})
    manual_refs = query_quality_manual.invoke({'question': complaint_summary})
    return {
        'problem_what': f'客户投诉：{complaint_summary}',
        'root_cause_why': '需现场调查（参考类似案例：' + (similar[0]['defect_description'][:50] if similar else '无') + '）',
        'action_who': '质量经理 + 责任工程师',
        'target_date_when': 'T+30 天',
        'location_where': '生产现场 + 客户使用环境',
        'method_how': '1) 隔离库存 2) 抽样复检 3) 工艺追溯 4) 客户通知',
        'cost_howmuch': 50000,
        'severity': severity_info['severity'],
        'references': [r['source'] for r in manual_refs[:2]],
    }
