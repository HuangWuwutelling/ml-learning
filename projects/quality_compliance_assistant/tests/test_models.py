import pytest
from django.db import IntegrityError
from qms_app.models import Manufacturer, Product, DefectType, Recall, Capa, Complaint, AuditLog

@pytest.mark.django_db
def test_recall_cascade_delete():
    m = Manufacturer.objects.create(name='test mfg', uscc_code='91110000TEST')
    p = Product.objects.create(manufacturer=m, name='test prod', brand='T', model='M1')
    dt = DefectType.objects.create(code='CD_EXCESS', name='Cd 超标')
    r = Recall.objects.create(product=p, defect_type=dt, source_type='samrdprc_gg', source_url='http://x',
                              recall_date='2025-01-01', quantity=100, consequence='Cd 中毒风险',
                              remedy_method='退货', status='active')
    assert r.id is not None
    r.delete()
    with pytest.raises(Recall.DoesNotExist):
        Recall.objects.get(id=r.id)

@pytest.mark.django_db
def test_recall_source_type_choices():
    m = Manufacturer.objects.create(name='m', uscc_code='91110000AAA')
    p = Product.objects.create(manufacturer=m, name='p', brand='b', model='m')
    dt = DefectType.objects.create(code='X', name='x')
    r = Recall(product=p, defect_type=dt, source_type='bad_source', source_url='u',
               recall_date='2025-01-01', quantity=1, consequence='c', remedy_method='r')
    with pytest.raises(IntegrityError):
        r.save()