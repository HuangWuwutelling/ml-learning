import pytest
from unittest.mock import patch, MagicMock
from scrapers.parse_recall import RecallRecord
from scrapers.base import RecallSpider

def test_recall_record_to_dict():
    r = RecallRecord(
        recall_id_external='X1', source_type='samrdprc_gg', source_url='u',
        raw_html_path='p', recall_date='2025-01-01', quantity=10,
        manufacturer_name='m', manufacturer_uscc='91110000X',
        product_name='p', product_brand='b', product_model='M',
        product_category='c', defect_description='d', consequence='c',
        remedy_method='r',
    )
    d = r.to_dict()
    assert d['recall_id_external'] == 'X1'
    assert d['source_type'] == 'samrdprc_gg'

def test_recall_spider_sleep_called(tmp_path):
    spider = RecallSpider(raw_html_root=tmp_path, sleep_seconds=0)
    with patch.object(spider, '_fetch_html', return_value='<html></html>'):
        with patch('time.sleep') as mock_sleep:
            spider.fetch_with_pause('http://x')
    mock_sleep.assert_called_once_with(0)
