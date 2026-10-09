import os
import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base import RecallSpider
from scrapers.parse_recall import RecallRecord


class SamrZHDTSpider(RecallSpider):
    """国家市场监督管理总局主站召回动态 (samr.gov.cn:3030/zlfzj/qxcpzh/zhdt)。

    与 samrdprc.org.cn 的国内消费品召回公告 (xfpzhgg) 不同：
    - 主站是 CMS 文本内容 (TRS 文章)，不是 TRS_Editor 图片。
    - 详情页 URL 形如 ``/zlfzj/qxcpzh/zhdt/art/YYYY/art_<hex>.html``。
    - 主站聚合了召回简讯 / 工作动态，没有厂商级字段（缺陷描述 / 数量 / 后果 / 措施），
      因此本爬虫把这些字段留空，把整篇正文塞进 ``defect_description``，方便后续
      NLP 抽取或人工审阅。``manufacturer_*`` 字段也置为聚合占位（USCC 仍保留
      '91110000SAMR' 作为主站标识）。
    """

    BASE = 'https://www.samr.gov.cn'
    LIST_BASE = f'{BASE}:3030/zlfzj/qxcpzh/zhdt/index'
    SOURCE_TYPE = 'samr_zhdt'
    PROXY = os.environ.get('QMS_PROXY', 'http://127.0.0.1:7897')

    def __init__(self, raw_html_root: Path, sleep_seconds: float = 1.5, timeout: int = 30):
        super().__init__(raw_html_root, sleep_seconds, timeout)
        # 详情页 URL 在 parse() 里用来推断 recall_id_external
        self._last_url = ''
        # 本机/内网需走 7897 代理访问 samr.gov.cn:3030（QMS_PROXY 可覆盖或置空关闭）
        if self.PROXY:
            self.session.proxies.update({'http': self.PROXY, 'https': self.PROXY})

    # ---------------- 列表页 ----------------
    def list_pages(self, max_pages: int = 50) -> list[str]:
        """遍历分页直到无内容。

        主站分页 URL 形如 ``index_<page>.html``，首页 ``index.html``，从 page=1 开始递增。
        停止条件：当前页找不到 ``a[href*="/art/"]`` 链接，或少于 5 条（防止最后一页
        残页导致死循环）。
        """
        urls: list[str] = []
        seen: set[str] = set()
        for page in range(0, max_pages):
            url = f'{self.LIST_BASE}_{page}.html' if page > 0 else f'{self.LIST_BASE}.html'
            try:
                html = self.fetch_with_pause(url)
            except Exception:
                break
            soup = BeautifulSoup(html, 'lxml')
            links = soup.select('a[href*="/art/"]')
            if not links:
                break
            page_count = 0
            for a in links:
                href = a.get('href', '')
                if not href.startswith('/'):
                    continue
                full = urljoin(self.BASE + ':3030', href)
                if full not in seen:
                    seen.add(full)
                    urls.append(full)
                    page_count += 1
            if len(links) < 5:
                break
        return urls

    # ---------------- 详情页解析 ----------------
    def parse(self, html: str) -> RecallRecord | None:
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(separator='\n', strip=True)
        title_tag = soup.find(['h1', 'h2'])
        title = title_tag.get_text(strip=True) if title_tag else ''

        # external_id 从 URL /art/YYYY/art_<hex>.html 推断
        url = self._last_url or ''
        url_match = re.search(r'/art/(\d{4})/art_([0-9a-f]+)\.html', url)
        external_id = f'samr_{url_match.group(1)}_{url_match.group(2)}' if url_match else 'UNKNOWN'

        # 主站格式：标题 + 正文，日期常出现在标题或正文首段
        date_match = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', text[:300])
        if date_match:
            recall_date = f'{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}'
        else:
            recall_date = '1970-01-01'

        return RecallRecord(
            recall_id_external=external_id,
            source_type=self.SOURCE_TYPE,
            source_url=url,
            raw_html_path='',
            recall_date=recall_date,
            quantity=0,
            manufacturer_name='(主站聚合)',
            manufacturer_uscc='91110000SAMR',
            product_name=title[:50],
            product_brand='', product_model='', product_category='',
            defect_description=text[:500],
            consequence='', remedy_method='',
            status='active',
        )

    def fetch_with_pause(self, url: str) -> str:
        self._last_url = url
        return super().fetch_with_pause(url)
