from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class RecallRecord:
    """统一的召回记录 dataclass，3 源爬虫输出对齐到此结构"""
    recall_id_external: str       # 外部公告编号（去重 key）
    source_type: str              # 'samrdprc_gg' / 'samrdprc_news' / 'samr_zhdt'
    source_url: str
    raw_html_path: str
    recall_date: str              # YYYY-MM-DD
    quantity: int
    manufacturer_name: str
    manufacturer_uscc: str
    product_name: str
    product_brand: str
    product_model: str
    product_category: str
    defect_description: str
    consequence: str
    remedy_method: str
    status: str = 'active'

    def to_dict(self):
        return asdict(self)
