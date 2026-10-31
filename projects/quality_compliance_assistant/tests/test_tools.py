import pytest
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
