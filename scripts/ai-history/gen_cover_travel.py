"""Cover for ai-history #12: 5-year parenting travel (2021 vs 2026)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# CJK fonts
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(9, 3.83), dpi=100)
ax.set_xlim(0, 9)
ax.set_ylim(0, 3.83)
ax.axis('off')

BG = '#FAFAFA'
ACCENT = '#C8102E'   # 国庆红
GOLD = '#D4A017'
GRAY_2021 = '#999999'
ORANGE_2026 = '#E8804A'

fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# 顶端细红条
ax.add_patch(plt.Rectangle((0, 3.65), 9, 0.06, color=ACCENT))

# 大字标题（左右双块：2021 vs 2026）
# 左：2021（灰）
ax.text(1.5, 2.5, '2021', fontsize=32, fontweight='bold',
        color=GRAY_2021, ha='center', va='center')
ax.text(1.5, 1.9, '12 个 App\n34 小时', fontsize=11, color='#666',
        ha='center', va='center')

# 中间箭头
ax.text(4.5, 2.5, '→', fontsize=42, fontweight='bold',
        color=ACCENT, ha='center', va='center')

# 右：2026（橙）
ax.text(7.5, 2.5, '2026', fontsize=32, fontweight='bold',
        color=ORANGE_2026, ha='center', va='center')
ax.text(7.5, 1.9, '1 个 AI\n3 小时', fontsize=11, color=ORANGE_2026,
        ha='center', va='center', fontweight='bold')

# 副标
ax.text(0.5, 1.05, '国庆亲子游 5 天', fontsize=18, color='#333',
        ha='left', va='center', fontweight='bold')
ax.text(0.5, 0.55, '2021 vs 2026，看三个数字变化', fontsize=13, color='#666',
        ha='left', va='center')

# 右下角小标
ax.text(8.5, 0.3, 'ai-history #12', fontsize=10, color='#999',
        ha='right', va='center')

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_travel_cover.png')
plt.savefig(out_path, dpi=100, facecolor=BG)
print('cover saved:', out_path)
