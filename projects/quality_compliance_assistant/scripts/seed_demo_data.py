"""
演示数据一键灌库：50 召回 + 30 CAPA + 10 投诉
用于面试现场拉起 demo，不依赖爬虫跑完
"""
import os
import sys
import django
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qms_project.settings')
django.setup()

from qms_app.models import Manufacturer, Product, DefectType, Recall, Capa, Complaint

random.seed(42)
DEFECT_TYPES = ['CD_EXCESS', 'PB_EXCESS', 'HG_EXCESS', 'AS_EXCESS', 'CR_EXCESS',
                'ELECTRIC_SHOCK', 'FIRE_RISK', 'MECHANICAL_INJURY']
CITIES_GD = ['广州', '深圳', '佛山', '东莞', '中山', '惠州']
CITIES_HN = ['长沙', '株洲', '湘潭', '衡阳', '岳阳']

def seed():
    if Recall.objects.count() >= 50:
        print(f'[skip] already have {Recall.objects.count()} recalls')
        return
    print('[seed] creating 5 manufacturers / 10 products / 8 defect types...')
    mfgs = [Manufacturer.objects.create(name=f'演示公司 {i}', uscc_code=f'91440000DEMO{i:04d}')
            for i in range(1, 6)]
    products = []
    for i in range(10):
        products.append(Product.objects.create(
            manufacturer=random.choice(mfgs),
            name=f'产品 {i}', brand=f'品牌{i}', model=f'M{i:03d}',
            category=random.choice(['家电', '电子', '儿童用品']),
        ))
    defects = [DefectType.objects.create(code=code, name=code.replace('_', ' '))
               for code in DEFECT_TYPES]

    print('[seed] creating 50 recalls...')
    for i in range(50):
        r = Recall.objects.create(
            product=random.choice(products),
            defect_type=random.choice(defects),
            recall_id_external=f'DEMO-{i:04d}',
            source_type='samrdprc_gg',
            source_url=f'https://example.com/demo/{i}',
            raw_html_path=f'raw_html/demo/{i}.html',
            recall_date=date(2024, 1, 1) + timedelta(days=random.randint(0, 700)),
            quantity=random.randint(10, 5000),
            defect_description=f'缺陷描述 #{i}: 模拟召回详情...',
            consequence=random.choice(['可能造成灼伤', '存在触电风险', '影响健康']),
            remedy_method=random.choice(['免费维修', '更换', '退货']),
            status='active',
        )
    print('[seed] creating 30 CAPAs...')
    for r in random.sample(list(Recall.objects.all()), 30):
        Capa.objects.create(
            recall=r,
            problem_what=f'针对 {r.product.name} 召回的 CAPA',
            root_cause_why='演示根因',
            action_who='张工',
            target_date_when=date.today() + timedelta(days=30),
            method_how='返工 + 抽检',
            status='pending',
        )
    print('[seed] creating 10 complaints...')
    samples = [
        '产品外壳破裂导致电池过热',
        '充电时冒烟',
        '儿童误食小零件',
        '使用中突然断电',
        '按键失灵频繁',
        '屏幕闪烁伤眼',
        '包装标识不清',
        '说明书缺安全警示',
        '金属边缘锐利',
        '材质有刺鼻气味',
    ]
    for txt in samples:
        Complaint.objects.create(text=txt)
    print('[seed] done.')

if __name__ == '__main__':
    seed()
