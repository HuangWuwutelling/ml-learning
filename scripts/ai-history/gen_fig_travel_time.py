"""Fig 1 for ai-history #12: parenting travel time comparison (5 stages)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# CJK fonts
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 5 环节：决策 / 规划 / 订票 / 导航（5天累计）/ 找餐厅（5天累计）
# 2021 数字（小时）：翻小红书+选目的地 8h / 行程 6h / 订票 4h / 每天导航 2h ×5=10h / 每天找餐厅 1.2h ×5=6h
# 2026 数字（小时）：5min + 10min + 5min + 每天 0.3h ×5=1.5h + 每天 0.3h ×5=1.5h ≈ 3h
stages = ['决策\n选目的地', '规划\n5 天行程', '订票\n机票酒店',
          '导航\n现场 5 天', '找餐厅\n现场 5 天']
v_2021 = [8.0, 6.0, 4.0, 10.0, 6.0]
v_2026 = [0.1, 0.2, 0.1, 1.5, 1.5]

# 总计
total_2021 = sum(v_2021)  # 34
total_2026 = sum(v_2026)  # 3.4

fig, ax = plt.subplots(figsize=(9, 4), dpi=100)
fig.subplots_adjust(left=0.18)
y = np.arange(len(stages))
h = 0.36

INTL_BLUE = '#1F77B4'
ORANGE_2026 = '#E8804A'
GRAY_2021 = '#999999'

bars1 = ax.barh(y - h/2, v_2021, h, color=GRAY_2021, label='2021')
bars2 = ax.barh(y + h/2, v_2026, h, color=ORANGE_2026, label='2026')

# 数值标签
for i, (v, _) in enumerate(zip(v_2021, stages)):
    ax.text(v + 0.3, i - h/2, f'{v}h', fontsize=10, va='center', color='#666')
for i, (v, _) in enumerate(zip(v_2026, stages)):
    label = f'{v}h' if v >= 1 else f'{int(v*60)}min'
    ax.text(max(v, 0.3) + 0.3, i + h/2, label, fontsize=10, va='center',
            color=ORANGE_2026, fontweight='bold')

# y 轴标签
ax.set_yticks(y)
ax.set_yticklabels(stages, fontsize=10)
ax.invert_yaxis()
ax.set_xlim(0, 12)
ax.set_xticks([])

for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(False)
ax.tick_params(axis='y', length=0)

# 总计标注（右上）
ax.text(11.5, -0.7, f'2021 合计：{total_2021}h', fontsize=11,
        color=GRAY_2021, ha='right', va='center', fontweight='bold')
ax.text(11.5, -1.2, f'2026 合计：{total_2026}h', fontsize=11,
        color=ORANGE_2026, ha='right', va='center', fontweight='bold')

ax.legend(loc='lower right', frameon=False, fontsize=10)

# 标题
ax.set_title('5 个环节，34 小时 → 3.4 小时', fontsize=14, fontweight='bold',
             color='#222', pad=10, loc='left')

# 副标
fig.text(0.02, 0.02,
         '注：2021 数字基于翻 App 实操估算；2026 数字基于 AI 助手实测',
         fontsize=7, color='#888', ha='left')

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_travel_time.png')
plt.savefig(out_path, dpi=100)
print('time fig saved:', out_path)
