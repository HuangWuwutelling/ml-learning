import pytest
import threading
from unittest.mock import patch, MagicMock
from agent.tools import search_recall_history, assess_severity, query_quality_manual

@pytest.mark.django_db
def test_search_recall_history_returns_list(sample_recall):
    # Mock the FK lookup so the test doesn't depend on test DB having all 130 prod recalls
    fake_recall = MagicMock()
    fake_recall.id = sample_recall.id
    fake_recall.product.name = 'p'
    fake_recall.defect_description = '测试缺陷描述'
    fake_recall.consequence = '可能烫伤'
    fake_recall.remedy_method = '退货'
    fake_recall.source_url = 'u'
    fake_recall.recall_date = '2025-01-01'
    with patch('qms_app.models.Recall.objects.get', return_value=fake_recall):
        result = search_recall_history.invoke({'query': sample_recall.defect_description[:30]})
    assert isinstance(result, list)
    assert len(result) >= 1
    assert 'defect_description' in result[0]

@pytest.mark.django_db
def test_assess_severity(sample_recall):
    result = assess_severity.invoke({'complaint_text': sample_recall.defect_description})
    assert 'severity' in result
    assert result['severity'] in ('high', 'medium', 'low')
    assert 0 <= result['confidence'] <= 1

def test_assess_severity_does_not_depend_on_recall_index():
    """召回索引缺失或损坏时，严重度判定照旧，只是没有相似案例可附。

    改之前是「先查索引，查不到就返回 medium」，于是同一个指标在灌了召回
    历史和没灌的机器上跑出两个数。
    """
    with patch('agent.tools._get_chroma', side_effect=RuntimeError('no index')):
        result = assess_severity.invoke({'complaint_text': '电池起火'})
    assert result['severity'] == 'high'
    assert result['similar_cases'] == []


def test_embedding_model_is_built_once():
    """embedding 模型必须进程内只建一次。

    transformers 4.57 的 from_pretrained 走 meta device 加载，同一个模型并发
    加载会 race，参数全留在 meta 上，抛 "Cannot copy out of meta tensor"，
    而且坏状态留在进程里，之后每次加载都失败。LangGraph 的 ToolNode 同一轮
    里并发跑多个工具，正好会踩到。
    """
    from agent.tools import get_embeddings
    assert get_embeddings() is get_embeddings()


def test_get_chroma_under_concurrent_threads():
    """并发取向量库不能炸（以前会抛 Cannot copy out of meta tensor）。"""
    from agent.tools import _get_chroma
    errors = []

    def worker():
        try:
            _get_chroma('qms_knowledge')
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors

@pytest.fixture
def sample_recall(db):
    from qms_app.models import Manufacturer, Product, Recall
    m = Manufacturer.objects.create(name='m', uscc_code='91110000X')
    p = Product.objects.create(manufacturer=m, name='p', brand='b', model='M')
    return Recall.objects.create(
        product=p, source_type='samrdprc_gg', source_url='u',
        recall_date='2025-01-01', quantity=10,
        defect_description='测试缺陷描述：电池过热导致外壳融化',
        consequence='可能烫伤', remedy_method='退货', status='active',
    )
