import time
import requests
from pathlib import Path
from typing import Optional
from .parse_recall import RecallRecord

class RecallSpider:
    def __init__(self, raw_html_root: Path, sleep_seconds: float = 1.5, timeout: int = 30):
        self.raw_html_root = Path(raw_html_root)
        self.sleep_seconds = sleep_seconds
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 QMS-Research (research@example.com)',
        })

    def _make_path(self, source: str, year: int, month: int, page_id: str) -> Path:
        d = self.raw_html_root / source / str(year) / f'{month:02d}'
        d.mkdir(parents=True, exist_ok=True)
        return d / f'{page_id}.html'

    def _fetch_html(self, url: str) -> str:
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text

    def fetch_with_pause(self, url: str) -> str:
        html = self._fetch_html(url)
        time.sleep(self.sleep_seconds)
        return html

    def save_raw(self, html: str, source: str, year: int, month: int, page_id: str) -> Path:
        p = self._make_path(source, year, month, page_id)
        p.write_text(html, encoding='utf-8')
        return p

    def parse(self, html: str) -> Optional[RecallRecord]:
        """子类必须实现"""
        raise NotImplementedError
