import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_recall_list(sample_recall):
    client = APIClient()
    r = client.get('/api/recalls/')
    assert r.status_code == 200
    assert r.data['count'] >= 1

@pytest.mark.django_db
def test_complaint_analyze(sample_recall):
    client = APIClient()
    r = client.post('/api/agent/complaint-analyze/',
                    {'text': '充电器冒烟'}, format='json')
    assert r.status_code == 200
    assert 'severity' in r.data
    assert 'capa_draft' in r.data

@pytest.fixture
def sample_recall(db):
    from qms_app.models import Manufacturer, Product, Recall
    m = Manufacturer.objects.create(name='m', uscc_code='91110000X')
    p = Product.objects.create(manufacturer=m, name='p', brand='b', model='M')
    return Recall.objects.create(
        product=p, source_type='samrdprc_gg', source_url='u',
        recall_date='2025-01-01', quantity=10,
        defect_description='充电器过热', consequence='可能烫伤', remedy_method='退货', status='active',
    )
