"""Fig 1 for ai-history #12: 5-year AI timeline (2021.10 -> 2026.10)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# CJK 字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 主节点（国际）
INTL_MAIN = [
    (datetime(2022, 11, 30), 'ChatGPT'),
    (datetime(2023, 3, 14), 'GPT-4\n多模态'),
    (datetime(2024, 3, 4), 'Claude 3\n三层模型'),
    (datetime(2024, 9, 12), 'o1\n(推理)'),  # 缩短：避免与下方 DeepSeek-R1 撞标签
    (datetime(2026, 6, 30), 'Sonnet 5\n1M 上下文'),
    (datetime(2026, 9, 22), 'Opus 5.5'),
]
# 次节点（国际），每项可指定 y_offset 避免标签撞车
INTL_MINOR = [
    # (datetime, label, y_offset, va)
    (datetime(2023, 11, 6), 'Assistants API', -0.3, 'top'),
    (datetime(2024, 5, 30), '工具调用 GA', +0.4, 'bottom'),   # y=+0.55 与 Claude 3 同 y 会撞 → 上抬至 +0.4
    (datetime(2024, 10, 22), 'Computer Use', -0.4, 'top'),     # y=-0.55 与 o1 同 y 会撞 → 下移至 -0.4
    (datetime(2026, 7, 24), 'Opus 5', -0.3, 'top'),
    # Sonnet 5.5 (2026-09-28) 已删：与 Opus 5.5 (2026-09-22) 仅隔 6 天，5 年轴上无法清晰呈现
]
# 国产节点（主节点大小，红色区分）
CN_MAIN = [
    (datetime(2024, 12, 26), 'DeepSeek-V3'),
    (datetime(2025, 1, 20), 'DeepSeek-R1'),
]
# 国庆端点
ENDS = [
    (datetime(2021, 10, 1), '2021 国庆'),
    (datetime(2026, 10, 1), '2026 国庆'),
]

START = datetime(2021, 8, 1)
END = datetime(2026, 11, 1)

fig, ax = plt.subplots(figsize=(9, 4), dpi=100)

# 主轴线
ax.axhline(y=0, color='#333', linewidth=2, zorder=1)

# 国际主节点（大蓝圆 + 上下交错标签）
INTL_BLUE = '#1F77B4'
for i, (dt, label) in enumerate(INTL_MAIN):
    ax.scatter(dt, 0, s=120, color=INTL_BLUE, zorder=3, edgecolor='white', linewidth=1.5)
    y = 0.55 if i % 2 == 0 else -0.55
    va = 'bottom' if y > 0 else 'top'
    ax.annotate(label, xy=(dt, 0), xytext=(dt, y),
                fontsize=9, ha='center', va=va, color='#222',
                arrowprops=dict(arrowstyle='-', color='#888', lw=0.6))

# 国际次节点（小灰点 + 简短描述）
for dt, label, y_off, va in INTL_MINOR:
    ax.scatter(dt, 0, s=40, color='#999', zorder=2)
    ax.annotate(label, xy=(dt, 0), xytext=(dt, y_off), fontsize=7,
                ha='center', va=va, color='#666')

# 国产主节点（大红圆 + 上下标签）
CN_RED = '#C8102E'
for i, (dt, label) in enumerate(CN_MAIN):
    ax.scatter(dt, 0, s=140, color=CN_RED, zorder=4, edgecolor='white', linewidth=1.5)
    y = 0.55 if i % 2 == 0 else -0.55
    va = 'bottom' if y > 0 else 'top'
    ax.annotate(label, xy=(dt, 0), xytext=(dt, y),
                fontsize=9, ha='center', va=va, color=CN_RED, fontweight='bold',
                arrowprops=dict(arrowstyle='-', color=CN_RED, lw=0.6, alpha=0.5))

# 国庆端点（黑边大点 + 醒目标签）
for dt, label in ENDS:
    ax.scatter(dt, 0, s=200, color='#FFD700', edgecolor='#222',
               linewidth=2, zorder=5)
    ax.annotate(label, xy=(dt, 0), xytext=(dt, 0.85), fontsize=11,
                ha='center', va='bottom', fontweight='bold', color='#222')

# 背景冷暖渐变（axvspan 模拟）
import matplotlib.colors as mcolors
cmap = mcolors.LinearSegmentedColormap.from_list(
    'coolwarm', ['#E8F0FA', '#FFF4E6'])
for x in [START, END]:
    pass
# 简单做法：左侧浅蓝矩形，右侧浅橙矩形
ax.axvspan(START, datetime(2024, 1, 1), alpha=0.15, color='#4A90D9', zorder=0)
ax.axvspan(datetime(2024, 1, 1), END, alpha=0.15, color='#E8A040', zorder=0)

# 轴范围 / 格式
ax.set_xlim(START, END)
ax.set_ylim(-1.0, 1.2)
ax.set_yticks([])
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.tick_params(axis='x', colors='#444', labelsize=10)
for spine in ['top', 'right', 'left']:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color('#888')

# 标题（caption 在文章里，不在图里）
ax.set_title('2021.10 - 2026.10 AI 大事时间线', fontsize=14,
             fontweight='bold', color='#222', pad=10)

# 保存
out_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                       'articles', 'ai-history', 'fig')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, '12_5year_timeline.png')
plt.savefig(out_path, dpi=100)
print('fig1 saved:', out_path)