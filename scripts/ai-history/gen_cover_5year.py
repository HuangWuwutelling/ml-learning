"""Cover for ai-history #12: 5-year AI comparison (2021.10 -> 2026.10)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# CJK 字体（CLAUDE.md Windows 平台笔记）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# CLAUDE.md / spec §5 硬约定
fig, ax = plt.subplots(figsize=(9, 3.83), dpi=100)
ax.set_xlim(0, 9)
ax.set_ylim(0, 3.83)
ax.axis('off')

# 国庆配色（红 + 金），点到为止
BG = '#FAFAFA'
ACCENT = '#C8102E'  # 中国红
GOLD = '#D4A017'

fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# 大字标题
ax.text(0.5, 2.3, '5 年 AI 对比', fontsize=42, fontweight='bold',
        color=ACCENT, ha='left', va='center')
# 副标
ax.text(0.5, 1.3, '2021.10  →  2026.10', fontsize=20, color='#333',
        ha='left', va='center')
ax.text(0.5, 0.7, '五个数字看变化', fontsize=16, color='#666',
        ha='left', va='center')
# 右下角小标
ax.text(8.5, 0.3, 'ai-history #12', fontsize=10, color='#999',
        ha='right', va='center')

# 顶端细红条
ax.add_patch(plt.Rectangle((0, 3.65), 9, 0.06, color=ACCENT))

# 保存（CLAUDE.md 硬约定：no bbox_inches='tight'）
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_5year_cover.png')
plt.savefig(out_path, dpi=100, facecolor=BG)
print('cover saved:', out_path)
