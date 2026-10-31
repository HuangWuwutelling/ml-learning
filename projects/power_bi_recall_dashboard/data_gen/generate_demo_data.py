# generate_demo_data.py
"""
演示用数据生成：500 行 recall + 50 行 manufacturer + 200 行 capa。
数据按粤湘两省集中生成（2024-2025），遵循 background_values.md 的占比。

⚠️ 数字字段（数量、行业占比）为演示值，公开来源在 background_values.md。
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT_DIR = Path(__file__).resolve().parent.parent / 'data'
OUT_DIR.mkdir(parents=True, exist_ok=True)

GD_CITIES = ['广州', '深圳', '佛山', '东莞', '中山', '惠州', '珠海', '汕头']
HN_CITIES = ['长沙', '株洲', '湘潭', '衡阳', '岳阳', '常德', '益阳']
DEFECTS = ['电气缺陷'] * 35 + ['机械安全'] * 25 + ['化学危害'] * 20 + ['烫伤'] * 12 + ['其他'] * 8
CATEGORIES = ['电子电器'] * 40 + ['儿童用品'] * 20 + ['家居用品'] * 15 + ['食品接触材料'] * 10 + ['其他'] * 15
REMEDIES = ['退货', '免费维修', '更换', '退货/维修', '补充警示说明']
SEVERITIES = ['high', 'medium', 'low']

def gen_manufacturers(n=50):
    rows = []
    for i in range(1, n + 1):
        is_gd = i <= 30  # 广东 30 家，湖南 20 家
        rows.append({
            'mfg_id': f'MFG{i:03d}',
            'name': f'演示公司{i}号',
            'province': '广东' if is_gd else '湖南',
            'city': random.choice(GD_CITIES if is_gd else HN_CITIES),
            'uscc_code': f'9144{"0000" if is_gd else "0100"}DEMO{i:04d}',
            'registered_capital_wan': random.choice([100, 500, 1000, 5000, 10000]),
        })
    return rows

def gen_recalls(mfgs, n=500):
    rows = []
    start = date(2024, 1, 1)
    for i in range(1, n + 1):
        mfg = random.choice(mfgs)
        defect = random.choice(DEFECTS)
        cat = random.choice(CATEGORIES)
        d = start + timedelta(days=random.randint(0, 600))
        rows.append({
            'recall_id': f'R{i:05d}',
            'recall_date': d.isoformat(),
            'mfg_id': mfg['mfg_id'],
            'product_name': f'{cat}产品#{i}',
            'product_brand': f'品牌{(i % 30) + 1:02d}',
            'product_category': cat,
            'defect_type': defect,
            'severity': random.choices(SEVERITIES, weights=[25, 50, 25])[0],
            'quantity': random.choice([random.randint(10, 500), random.randint(500, 5000)]),
            'remedy': random.choice(REMEDIES),
            'estimated_cost_wan': random.randint(1, 200),
            'source_type': 'samrdprc_gg' if random.random() < 0.6 else 'samr_zhdt',
        })
    return rows

def gen_capas(recalls, n=200):
    rows = []
    sample_recalls = random.sample(recalls, n)
    for i, r in enumerate(sample_recalls, 1):
        rows.append({
            'capa_id': f'CAPA{i:04d}',
            'recall_id': r['recall_id'],
            'opened_date': r['recall_date'],
            'target_close_date': (date.fromisoformat(r['recall_date']) + timedelta(days=random.randint(15, 90))).isoformat(),
            'status': random.choices(['draft', 'pending', 'effective', 'closed'], weights=[10, 30, 40, 20])[0],
            'effectiveness_score': random.randint(1, 5),
            'responsible_engineer': random.choice(['张工', '李工', '王工', '陈工', '刘工']),
        })
    return rows

def write_csv(name, rows):
    p = OUT_DIR / name
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f'[write] {p} ({len(rows)} rows)')

def main():
    print('[gen] manufacturers...')
    mfgs = gen_manufacturers()
    write_csv('manufacturers.csv', mfgs)
    print('[gen] recalls...')
    recalls = gen_recalls(mfgs)
    write_csv('recall_events.csv', recalls)
    print('[gen] capas...')
    capas = gen_capas(recalls)
    write_csv('capa_actions.csv', capas)
    print('[done]')

if __name__ == '__main__':
    main()