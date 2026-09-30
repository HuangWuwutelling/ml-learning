"""Fig 3 for ai-history #12: prompt (2021) vs Agent (2026) paradigm."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# CJK 字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(9, 4), dpi=100)
ax.set_xlim(0, 9)
ax.set_ylim(0, 4)
ax.axis('off')

INTL_BLUE = '#1F77B4'
ACCENT = '#C8102E'
LIGHT_GRAY = '#F0F0F0'

# ---- 左半：2021 ----
# 对话框
box1 = FancyBboxPatch((0.5, 1.4), 3.0, 1.5,
                      boxstyle='round,pad=0.05',
                      linewidth=2, edgecolor='#888', facecolor='white')
ax.add_patch(box1)
ax.text(2.0, 2.6, '2021', fontsize=11, color='#888', ha='center', va='center')
ax.text(2.0, 2.15, '学 prompt', fontsize=18, fontweight='bold',
        color='#444', ha='center', va='center')
ax.text(2.0, 1.65, '"你好，帮我写首诗..."', fontsize=10, color='#666',
        ha='center', va='center', style='italic')

# ---- 中间大字「5 年」----
# 移除箭头：「2021 学 prompt → 2026 做 Agent」标题已有箭头，正文里箭头和「5 年」撞位置
ax.text(4.5, 2.15, '5 年', fontsize=42, fontweight='bold',
        color=ACCENT, ha='center', va='center')

# ---- 右半：2026 ----
# 主屏幕
box2 = FancyBboxPatch((5.5, 1.4), 3.0, 1.5,
                      boxstyle='round,pad=0.05',
                      linewidth=2, edgecolor=INTL_BLUE, facecolor='white')
ax.add_patch(box2)
ax.text(7.0, 2.6, '2026', fontsize=11, color=INTL_BLUE, ha='center', va='center')
ax.text(7.0, 2.15, '做 Agent', fontsize=18, fontweight='bold',
        color=INTL_BLUE, ha='center', va='center')

# 工具节点（屏幕内）
tools = ['搜索', '文件', '终端', '浏览器']
for i, t in enumerate(tools):
    x = 5.85 + i * 0.65
    tool_box = FancyBboxPatch((x, 1.55), 0.55, 0.32,
                              boxstyle='round,pad=0.02',
                              linewidth=1, edgecolor=INTL_BLUE,
                              facecolor=LIGHT_GRAY)
    ax.add_patch(tool_box)
    ax.text(x + 0.275, 1.71, t, fontsize=8, ha='center', va='center',
            color=INTL_BLUE)

# ReAct 循环箭头（屏幕外底部）
react_arrow = FancyArrowPatch((6.5, 0.9), (7.5, 0.9),
                             connectionstyle='arc3,rad=0.3',
                             arrowstyle='->', mutation_scale=15,
                             color=INTL_BLUE, linewidth=1.5)
ax.add_patch(react_arrow)
ax.text(7.0, 0.55, 'ReAct 循环', fontsize=9, color=INTL_BLUE,
        ha='center', va='center')

# 标题
ax.text(0.5, 3.6, '2021 学 prompt  →  2026 做 Agent', fontsize=14,
        fontweight='bold', color='#222', ha='left', va='center')

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_5year_prompt2agent.png')
plt.savefig(out_path, dpi=100)
print('fig3 saved:', out_path)
