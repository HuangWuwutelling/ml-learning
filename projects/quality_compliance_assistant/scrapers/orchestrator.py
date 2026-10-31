"""3 源爬虫编排与幂等入库。

调用::

    from scrapers.orchestrator import run_crawl
    run_crawl(start_year=2024, end_year=2024, sources=['samrdprc_gg'])

幂等 key: ``Recall.recall_id_external``。重复跑同一份列表（同一份 URL 断点）只
会更新已有记录，不新增行。``Manufacturer`` 按 ``uscc_code`` 去重，
``Product`` 按 ``(manufacturer, name)`` 去重——这些维表的唯一性由
``Manufacturer.uscc_code`` 唯一索引 + ``get_or_create`` 在单进程下保证。
"""
from pathlib import Path

from django.db import transaction

from qms_app.models import Manufacturer, Product, Recall
from scrapers.parse_recall import RecallRecord


def upsert_recall(rec: RecallRecord) -> tuple[Recall, bool]:
    """幂等写入 Recall：以 ``recall_id_external`` 为唯一 key。

    返回 ``(obj, created)``。``created=True`` 表示本轮新插入，``False`` 表示
    已存在并被 update_or_create 覆盖。``update_or_create`` 每次都会把所有
    ``defaults`` 重写一遍——这意味着重新爬同一 URL 会用最新解析结果覆盖旧行。
    对"每天定时跑一遍增量同步"的使用场景是期望行为；如果上游需要保留人工
    标注，请在调用前备份或加 dirty flag（本 orchestrator 不做）。
    """
    mfg, _ = Manufacturer.objects.get_or_create(
        uscc_code=rec.manufacturer_uscc,
        defaults={'name': rec.manufacturer_name, 'address': ''},
    )
    product, _ = Product.objects.get_or_create(
        manufacturer=mfg, name=rec.product_name,
        defaults={
            'brand': rec.product_brand,
            'model': rec.product_model,
            'category': rec.product_category,
        },
    )
    defaults = {
        'product': product,
        'source_type': rec.source_type,
        'source_url': rec.source_url,
        'raw_html_path': rec.raw_html_path,
        'recall_date': rec.recall_date,
        'quantity': rec.quantity,
        'defect_description': rec.defect_description,
        'consequence': rec.consequence,
        'remedy_method': rec.remedy_method,
        'status': rec.status,
    }
    obj, created = Recall.objects.update_or_create(
        recall_id_external=rec.recall_id_external,
        defaults=defaults,
    )
    return obj, created


def run_crawl(
    start_year: int = 2024,
    end_year: int = 2026,
    sources: list[str] | None = None,
    raw_html_root: Path | str = 'raw_html',
) -> int:
    """按 (year, month) 遍历调用 3 源爬虫并写入 DB。返回本轮新增条数。

    Args:
        start_year: 起始年份（含）。
        end_year: 结束年份（含）。
        sources: 要跑的源子集，默认 3 个全跑；可选值 ``samrdprc_gg`` /
            ``samrdprc_news`` / ``samr_zhdt``。
        raw_html_root: 详情页 HTML 落盘根目录（相对 manage.py 所在项目根）。

    Notes:
        - ``samr_zhdt.list_pages()`` 不接受 ``(year, month)`` 参数（主站列表是
          单一时间倒序全量分页）。为避免每个 month 都重新拉所有分页，仅在
          ``year == start_year`` 时跑一次，其他月份直接走空集。这对 ``update_or_create``
          的幂等性无影响（同一 URL 第二次跑会变成更新而非插入）。
        - 单条详情页失败用 try/except 包住，打印 ``[error]`` 后继续——一条错不
          影响整批。
    """
    from scrapers.sources.samrdprc_gg import SamrdprcGGSpider
    from scrapers.sources.samrdprc_news import SamrdprcNewsSpider
    from scrapers.sources.samr_zhdt import SamrZHDTSpider

    sources = sources or ['samrdprc_gg', 'samrdprc_news', 'samr_zhdt']
    spiders = {
        'samrdprc_gg': SamrdprcGGSpider,
        'samrdprc_news': SamrdprcNewsSpider,
        'samr_zhdt': SamrZHDTSpider,
    }
    raw_root = Path(raw_html_root)
    total_new = 0

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            for src in sources:
                cls = spiders[src]
                spider = cls(raw_html_root=raw_root, sleep_seconds=1.5)

                if src == 'samr_zhdt':
                    # 主站列表不分年月，只在第一年的第一月跑一次
                    if year == start_year and month == 1:
                        urls = spider.list_pages()
                    else:
                        urls = []
                else:
                    urls = spider.list_pages(year, month)

                for u in urls:
                    try:
                        html = spider.fetch_with_pause(u)
                        # page_id 用 URL 末段，扩展名去掉了；落盘后回填到 rec.raw_html_path
                        page_id = u.split('/')[-1].replace('.html', '')
                        p = spider.save_raw(html, src, year, month, page_id)
                        rec = spider.parse(html)
                        if rec is None:
                            continue
                        rec.raw_html_path = str(p.relative_to(raw_root))
                        # 单条 upsert 不需要大事务；一次失败不影响其他条
                        _, created = upsert_recall(rec)
                        if created:
                            total_new += 1
                    except Exception as e:
                        print(f'[error] {u}: {e}')

    print(f'[done] inserted {total_new} new recalls')
    return total_new