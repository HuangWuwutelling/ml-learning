"""Fig 3 for ai-history #12: parenting travel anxiety radar (5 dims)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# CJK fonts
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 5 维焦虑（1-5 分）
dims = ['攻略过期', '抢票焦虑', '餐厅踩雷', '导航迷路', '孩子哭闹']
v_2021 = [4, 5, 4, 3, 4]
v_2026 = [1, 1, 2, 1, 3]

# 角度
N = len(dims)
angles = [n / N * 2 * np.pi for n in range(N)]
angles += angles[:1]

v_2021_plot = v_2021 + v_2021[:1]
v_2026_plot = v_2026 + v_2026[:1]

GRAY_2021 = '#999999'
ORANGE_2026 = '#E8804A'
BG_FILL_2021 = '#D9D9D9'
BG_FILL_2026 = '#FCE3D5'

# 9×4 画布：左侧方块雷达 (0..4)，右侧文字注解 (4..9)
fig = plt.figure(figsize=(9, 4), dpi=100)
ax = fig.add_subplot(111, projection='polar', position=[0.02, 0.08, 0.45, 0.84])

# 2021
ax.plot(angles, v_2021_plot, color=GRAY_2021, linewidth=2, label='2021')
ax.fill(angles, v_2021_plot, color=BG_FILL_2021, alpha=0.6)

# 2026
ax.plot(angles, v_2026_plot, color=ORANGE_2026, linewidth=2, label='2026')
ax.fill(angles, v_2026_plot, color=BG_FILL_2026, alpha=0.6)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(dims, fontsize=11)
ax.set_ylim(0, 5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=8, color='#888')
ax.set_rlabel_position(90)
ax.grid(color='#CCCCCC', linewidth=0.5)
ax.spines['polar'].set_color('#CCCCCC')

# 右侧文字说明区
ax_text = fig.add_subplot(111, position=[0.50, 0.0, 0.48, 1.0])
ax_text.axis('off')

# 标题
ax_text.text(0.5, 0.95, '5 个焦虑点', fontsize=20, fontweight='bold',
             color='#222', ha='center', va='center')
ax_text.text(0.5, 0.85, '4 个变 1 个', fontsize=20, fontweight='bold',
             color=ORANGE_2026, ha='center', va='center')

# 数字对比
ax_text.text(0.5, 0.70, '2021 总分：20', fontsize=12, color=GRAY_2021,
             ha='center', va='center', fontweight='bold')
ax_text.text(0.5, 0.64, '2026 总分：8', fontsize=12, color=ORANGE_2026,
             ha='center', va='center', fontweight='bold')

# 剩余 4 项明细
notes = [
    ('攻略过期', '4 → 1', '实时拉数据'),
    ('抢票焦虑', '5 → 1', 'AI 监控自动改签'),
    ('餐厅踩雷', '4 → 2', 'AI 筛高赞避雷'),
    ('导航迷路', '3 → 1', 'AR 实时导航'),
]
for i, (name, delta, why) in enumerate(notes):
    y = 0.50 - i * 0.085
    ax_text.text(0.05, y, name, fontsize=10, color='#444', ha='left', va='center')
    ax_text.text(0.55, y, delta, fontsize=10, color=ORANGE_2026,
                 ha='left', va='center', fontweight='bold')
    ax_text.text(0.80, y, why, fontsize=9, color='#888',
                 ha='left', va='center')

# 孩子哭闹标注（唯一没怎么降的）
ax_text.text(0.05, 0.13, '孩子哭闹 4 → 3', fontsize=10, color='#666',
             ha='left', va='center', style='italic')
ax_text.text(0.05, 0.07, '（AI 故事机能挡一点）', fontsize=8, color='#888',
             ha='left', va='center')

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_travel_anxiety.png')
plt.savefig(out_path, dpi=100)
print('anxiety fig saved:', out_path)
