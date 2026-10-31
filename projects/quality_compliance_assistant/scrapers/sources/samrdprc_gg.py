import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers.base import RecallSpider
from scrapers.parse_recall import RecallRecord


class SamrdprcGGSpider(RecallSpider):
    """国家市场监督管理总局缺陷产品召回技术中心 —— 国内消费品召回公告 (xfpzhgg)。

    实测页面结构（2024/2026 抽样）：
    - 文章标题在 ``.show_tit``（``<title>`` 只是站点通用名，不能用）。
    - 发布时间在 ``.show_tit2``。
    - 正文在 ``.show_txt``，但正文内容实际以**图片**（TRS_Editor 内的 ``<img>``）发布，
      页面上没有可选中的"由于/可能引起/涉及数量"文字 —— 因此正文类字段（缺陷/后果/措施/
      数量）大多为空，属站点现状，非解析 bug。若后续引入 OCR，可在此处补充。
    - 详情页 URL 形如 ``.../xfpzhgg/202402/t20240223_110851.html``。
    """

    BASE = 'https://www.samrdprc.org.cn'
    LIST_BASE = f'{BASE}/xfpzh/xfpzhgg/'
    PROXY = os.environ.get('QMS_PROXY', 'http://127.0.0.1:7897')

    def __init__(self, raw_html_root: Path, sleep_seconds: float = 1.5, timeout: int = 30):
        super().__init__(raw_html_root, sleep_seconds, timeout)
        # 详情页 URL 在 parse() 里用来推断 recall_date / recall_id_external
        self._last_url = ''
        # 本机/内网需走 7897 代理访问 samrdprc.org.cn（可用 QMS_PROXY 覆盖或置空关闭）
        if self.PROXY:
            self.session.proxies.update({'http': self.PROXY, 'https': self.PROXY})

    # ---------------- 列表页 ----------------
    def list_pages(self, year: int, month: int) -> list[str]:
        """返回 (year, month) 月份的所有详情页 URL。

        实测列表页详情链接形如 ``./202609/t20260928_116129.html``（相对路径，
        不含 ``xfpzhgg/``），因此按 ``tYYYYMMDD_NNNNNN.html`` 匹配。
        """
        page = 1
        urls: list[str] = []
        seen: set[str] = set()
        while page <= 20:  # 安全上限
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
                # href 形如 './202609/t...html'，相对当前列表页 /xfpzh/xfpzhgg/ 解析，
                # 因此必须相对 list_url（而非 BASE）拼接，保留 xfpzhgg 路径前缀。
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
            external_id = f't{day}_{seq}'          # 例：t20240223_110851
        else:
            recall_date = '1970-01-01'
            external_id = 'UNKNOWN'

        mfg_name, brand, model, product = self._split_title(title)

        # 正文类字段（该站正文多为图片，命中与否取决于是否含文字版正文）
        defect_match = re.search(r'(由于[^。]{5,200}?)[。\n]', text)
        consequence_match = re.search(r'可能(?:引起|造成|导致)([^。]{3,100})', text)
        remedy_match = re.search(r'(将为消费者(?:免费[^。]{3,100}))', text)
        quantity_match = re.search(r'涉及数量为?(\d+)\s*台', text)

        return RecallRecord(
            recall_id_external=external_id,
            source_type='samrdprc_gg',
            source_url=url,
            raw_html_path='',
            recall_date=recall_date,
            quantity=int(quantity_match.group(1)) if quantity_match else 0,
            manufacturer_name=mfg_name,
            manufacturer_uscc='91110000UNKNOWN',  # 公告通常不公开 USCC
            product_name=product,
            product_brand=brand,
            product_model=model,
            product_category='',  # 由后续分类补
            defect_description=defect_match.group(1) if defect_match else text[:500],
            consequence=consequence_match.group(1) if consequence_match else '',
            remedy_method=remedy_match.group(1) if remedy_match else '',
            status='active',
        )

    # ---------------- 内部工具 ----------------
    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """文章标题：优先 .show_tit，其次 <meta keywords>，最后 <title>。"""
        el = soup.select_one('.show_tit')
        if el:
            t = el.get_text(separator=' ', strip=True)
            if t:
                return t
        meta = soup.find('meta', attrs={'name': 'keywords'})
        if meta and meta.get('content'):
            # keywords 形如 "标题,国内消费品召回公告"
            return meta['content'].split(',')[0].strip()
        if soup.title:
            return soup.title.get_text(strip=True)
        return ''

    @staticmethod
    def _extract_body_text(soup: BeautifulSoup) -> str:
        """正文可见文字（限定在 .show_txt 内；该站正文常为图片，文字可能为空）。"""
        el = soup.select_one('.show_txt')
        if el:
            return el.get_text(separator='\n', strip=True)
        return soup.get_text(separator='\n', strip=True)

    @staticmethod
    def _split_title(title: str) -> tuple[str, str, str, str]:
        """把标题拆成 (manufacturer, brand, model, product_name)。

        标题形如 ``{厂商}召回部分{品牌}牌{品类}`` /
        ``{厂商}召回部分{型号}型号{品类}`` / ``{厂商}召回部分{品类}``。
        以 ``召回部分`` 为分界最稳，能同时覆盖"有限公司/厂"等不同后缀。
        """
        head, sep, tail = title.partition('召回部分')
        if not sep:
            # 兜底：无"召回部分"标记时用正则猜厂商
            m = re.search(r'^(.+?(?:有限公司|有限责任公司|股份有限公司|厂))', title)
            if m:
                return m.group(1).strip(), '', '', title
            return title.strip(), '', '', title

        mfg = head.strip()
        tail = tail.strip()
        brand = model = ''
        if '牌' in tail:
            brand, _, product = tail.partition('牌')
            brand, product = brand.strip(), product.strip()
        elif '型号' in tail:
            model, _, product = tail.partition('型号')
            model, product = model.strip(), product.strip()
        else:
            product = tail
        return mfg, brand, model, product

    def fetch_with_pause(self, url: str) -> str:
        self._last_url = url
        return super().fetch_with_pause(url)
