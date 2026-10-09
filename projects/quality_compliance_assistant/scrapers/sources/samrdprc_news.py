import os
import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scrapers.base import RecallSpider
from scrapers.parse_recall import RecallRecord


class SamrdprcNewsSpider(RecallSpider):
    """国家市场监督管理总局缺陷产品召回技术中心 —— 召回新闻 (xfpgnzh)。

    与 ``samrdprc_gg`` (xfpzhgg 召回公告) 共享域名 (``samrdprc.org.cn``)，但页面
    结构不同：

    - 列表页 URL 形如 ``/xfpzh/xfpgnzh/index_{page}.html``。
    - 详情页 URL 形如 ``/xfpzh/xfpgnzh/YYYYMM/tYYYYMMDD_NNNNNN.html``（与 xfpzhgg
      同结构，所以 ``_last_url`` 推断 ``recall_date`` / ``recall_id_external`` 的
      正则相同）。
    - 新闻页没有结构化字段（厂商/品牌/型号/数量/缺陷描述），整篇正文塞进
      ``defect_description``，厂商/产品字段留占位。这与 xfpzhgg "图文详情页"
      在解析粒度上不同，是新闻聚合本身的特性。
    """

    BASE = 'https://www.samrdprc.org.cn'
    LIST_BASE = f'{BASE}/xfpzh/xfpgnzh/'
    SOURCE_TYPE = 'samrdprc_news'
    PROXY = os.environ.get('QMS_PROXY', 'http://127.0.0.1:7897')

    def __init__(self, raw_html_root: Path, sleep_seconds: float = 1.5, timeout: int = 30):
        super().__init__(raw_html_root, sleep_seconds, timeout)
        # 详情页 URL 在 parse() 里用来推断 recall_date / recall_id_external
        self._last_url = ''
        # 与 samrdprc_gg 共享域名，代理设置保持一致
        if self.PROXY:
            self.session.proxies.update({'http': self.PROXY, 'https': self.PROXY})

    # ---------------- 列表页 ----------------
    def list_pages(self, year: int, month: int) -> list[str]:
        """返回 (year, month) 月份的所有详情页 URL。

        列表页分页形如 ``index_{page}.html``，首页 ``xfpgnzh/``，详情链接形如
        ``./YYYYMM/tYYYYMMDD_NNNNNN.html``（相对当前列表页，需用 ``list_url``
        作 ``urljoin`` 基准以保留 ``xfpgnzh`` 前缀）。
        """
        page = 1
        urls: list[str] = []
        seen: set[str] = set()
        while page <= 30:  # 安全上限
            list_url = f'{self.LIST_BASE}index_{page}.html' if page > 1 else self.LIST_BASE
            try:
                html = self.fetch_with_pause(list_url)
            except Exception:
                break
            soup = BeautifulSoup(html, 'lxml')
            month_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if not re.search(r't\d{8}_\d+\.html$', href):
                    continue
                if f'/{year}{month:02d}/' not in href:
                    continue
                full = urljoin(list_url, href)
                if full not in seen:
                    seen.add(full)
                    month_links.append(full)
            if not month_links:
                break
            urls.extend(month_links)
            page += 1
        return urls

    # ---------------- 详情页解析 ----------------
    def parse(self, html: str) -> RecallRecord | None:
        soup = BeautifulSoup(html, 'lxml')
        title = self._extract_title(soup)
        text = self._extract_body_text(soup)

        # 日期与外部 ID 从 URL 推断（/YYYYMM/tYYYYMMDD_NNNNNN.html）
        url = self._last_url or ''
        m = re.search(r'/(\d{4})(\d{2})/t(\d{8})_(\d+)\.html', url)
        if m:
            year, month, day, seq = m.groups()
            recall_date = f'{year}-{month}-{day[6:8]}'
            # 新闻用 news_ 前缀与 samrdprc_gg 的 t{day}_{seq} 区分（虽然同站点
            # tYYYYMMDD_NNNNNN 编号本身不重叠，但加前缀更显式，避免误判）
            external_id = f'news_t{day}_{seq}'
        else:
            recall_date = '1970-01-01'
            external_id = 'UNKNOWN'

        return RecallRecord(
            recall_id_external=external_id,
            source_type=self.SOURCE_TYPE,
            source_url=url,
            raw_html_path='',
            recall_date=recall_date,
            quantity=0,
            manufacturer_name='(新闻聚合)',
            manufacturer_uscc='91110000NEWS',
            product_name=title[:50],
            product_brand='', product_model='', product_category='',
            defect_description=text[:500],
            consequence='', remedy_method='',
            status='active',
        )

    # ---------------- 内部工具 ----------------
    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """文章标题：优先 h1，其次 meta keywords，最后 <title>。

        新闻页结构比 xfpzhgg 更扁平，多数情况下 ``<h1>`` 直接可用。
        """
        el = soup.find('h1')
        if el:
            t = el.get_text(separator=' ', strip=True)
            if t:
                return t
        meta = soup.find('meta', attrs={'name': 'keywords'})
        if meta and meta.get('content'):
            return meta['content'].split(',')[0].strip()
        if soup.title:
            return soup.title.get_text(strip=True)
        return ''

    @staticmethod
    def _extract_body_text(soup: BeautifulSoup) -> str:
        """正文可见文字（若新闻页有 .show_txt 用之，否则取整页文字）。"""
        el = soup.select_one('.show_txt')
        if el:
            return el.get_text(separator='\n', strip=True)
        return soup.get_text(separator='\n', strip=True)

    def fetch_with_pause(self, url: str) -> str:
        # 严格顺序：先记 _last_url，再调父类 fetch（参 Task 7 reviewer 提示：
        # 若 parse 在 fetch 之外被调用/缓存，external_id 会退化为 UNKNOWN）
        self._last_url = url
        return super().fetch_with_pause(url)