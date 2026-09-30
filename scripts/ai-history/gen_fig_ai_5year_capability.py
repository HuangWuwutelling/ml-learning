"""Fig 2 for ai-history #12: 5-dim capability comparison (2021 vs 2026)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# CJK 字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 5 维：每维 2021 vs 2026
# 数值：'实验级' = 1, '本科' = 2, '生产级' = 4, '接近 PhD' = 5
# 2K 上下文 -> 1M 上下文：1 -> 5（log scale 概念化）
# 工具调用 0% -> 100%：0 -> 5
# 模态 纯文本 -> 文图音视频：1 -> 4
# 推理 本科 -> 接近 PhD：2 -> 5
# Agent 实验级 -> 生产级：1 -> 4
dims = ['上下文长度', '工具调用', '模态', '推理 (数学/代码)', 'Agent 长程任务']
v_2021 = [1, 0, 1, 2, 1]
v_2026 = [5, 5, 4, 5, 4]
labels_2021 = ['2K', '0%', '纯文本', '本科', '实验级']
labels_2026 = ['1M (500x)', '100%', '文/图/音/视频', '~PhD', '~生产级']

fig, ax = plt.subplots(figsize=(9, 4), dpi=100)
y = np.arange(len(dims))
h = 0.36

INTL_BLUE = '#1F77B4'
ACCENT = '#C8102E'

bars1 = ax.barh(y - h/2, v_2021, h, color='#999', label='2021')
bars2 = ax.barh(y + h/2, v_2026, h, color=INTL_BLUE, label='2026')

# 数值标签
for i, (v, lbl) in enumerate(zip(v_2021, labels_2021)):
    ax.text(v + 0.15, i - h/2, lbl, fontsize=9, va='center', color='#666')
for i, (v, lbl) in enumerate(zip(v_2026, labels_2026)):
    ax.text(v + 0.15, i + h/2, lbl, fontsize=9, va='center',
            color=INTL_BLUE, fontweight='bold')

# 标签 / 美化
ax.set_yticks(y)
ax.set_yticklabels(dims, fontsize=11)
ax.set_xlim(0, 7.5)
ax.set_xticks([])
ax.invert_yaxis()
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.legend(loc='lower right', frameon=False, fontsize=10)

# 标题
ax.set_title('5 个数字看 AI 这五年', fontsize=14, fontweight='bold',
             color='#222', pad=10, loc='left')

# 说明副标
fig.text(0.02, 0.02,
         '注：上下文/模态/推理/Agent 为定性对比',
         fontsize=7, color='#888', ha='left')

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_5year_capability.png')
plt.savefig(out_path, dpi=100)
print('fig2 saved:', out_path)