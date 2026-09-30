"""Fig 2 for ai-history #12: parenting travel tools (12 apps vs 1 AI)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# CJK fonts
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(9, 4), dpi=100)
ax.set_xlim(0, 9)
ax.set_ylim(0, 4.4)
ax.axis('off')

GRAY_2021 = '#999999'
ORANGE_2026 = '#E8804A'
BG_GRAY = '#F0F0F0'

# ---- 左半：2021，12 个 App icon ----
ax.text(2.0, 3.4, '2021', fontsize=20, fontweight='bold',
        color=GRAY_2021, ha='center', va='center')
ax.text(2.0, 3.0, '12 个 App', fontsize=12, color='#666',
        ha='center', va='center')

# 12 个 App 排成 4×3 网格
apps_2021 = [
    ('小红书', '攻略'),
    ('抖音', '攻略'),
    ('马蜂窝', '攻略'),
    ('大众点评', '餐厅'),
    ('美团', '团购'),
    ('携程', '订票'),
    ('飞猪', '订票'),
    ('12306', '火车'),
    ('航旅纵横', '航班'),
    ('高德', '导航'),
    ('百度地图', '导航'),
    ('支付宝', '支付'),
]
# 4 列 × 3 行
cols, rows = 4, 3
icon_w, icon_h = 0.85, 0.65
gap_x, gap_y = 0.1, 0.12
total_w = cols * icon_w + (cols - 1) * gap_x
start_x = 2.0 - total_w / 2
start_y = 0.4
for i, (name, sub) in enumerate(apps_2021):
    col = i % cols
    row = i // cols
    x = start_x + col * (icon_w + gap_x)
    y = start_y + (rows - 1 - row) * (icon_h + gap_y)
    # icon box
    box = FancyBboxPatch((x, y), icon_w, icon_h,
                         boxstyle='round,pad=0.02',
                         linewidth=1, edgecolor='#888', facecolor=BG_GRAY)
    ax.add_patch(box)
    # 名字
    ax.text(x + icon_w / 2, y + icon_h * 0.65, name, fontsize=9,
            ha='center', va='center', color='#444', fontweight='bold')
    # 副标
    ax.text(x + icon_w / 2, y + icon_h * 0.25, sub, fontsize=7,
            ha='center', va='center', color='#888')

# ---- 中间箭头 + 大字 ----
ax.text(4.5, 2.0, '→', fontsize=42, fontweight='bold',
        color='#C8102E', ha='center', va='center')

# ---- 右半：2026，1 个 AI ----
ax.text(7.0, 3.4, '2026', fontsize=20, fontweight='bold',
        color=ORANGE_2026, ha='center', va='center')
ax.text(7.0, 3.0, '1 个 AI', fontsize=12, color=ORANGE_2026,
        ha='center', va='center', fontweight='bold')

# 大 icon
big_box = FancyBboxPatch((6.0, 1.4), 2.0, 1.4,
                        boxstyle='round,pad=0.05',
                        linewidth=2, edgecolor=ORANGE_2026,
                        facecolor='white')
ax.add_patch(big_box)
ax.text(7.0, 2.45, 'AI 助手', fontsize=18, fontweight='bold',
        ha='center', va='center', color=ORANGE_2026)
ax.text(7.0, 2.0, '豆包 / 通义 / 文小言', fontsize=10,
        ha='center', va='center', color='#666')
ax.text(7.0, 1.65, '一个对话框搞定', fontsize=9,
        ha='center', va='center', color='#888', style='italic')

# 标题
ax.text(0.5, 4.2, '12 个 App → 1 个 AI', fontsize=14, fontweight='bold',
        color='#222', ha='left', va='center')

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_travel_tools.png')
plt.savefig(out_path, dpi=100)
print('tools fig saved:', out_path)
