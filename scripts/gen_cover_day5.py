"""
Generate cover for Day 5 — Random Forest visual concept.
Light theme, high contrast. 900×383px, no bbox_inches='tight', no title.
"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

plt.rcParams['font.family'] = 'Microsoft YaHei'
plt.rcParams['axes.unicode_minus'] = False

np.random.seed(42)
fig, ax = plt.subplots(figsize=(9, 3.83))
fig.patch.set_facecolor('#f5f7fa')
ax.set_xlim(0, 9)
ax.set_ylim(0, 3.83)
ax.axis('off')

# ── Subtle background grid dots ──────────────────────────────────────────
for x in np.arange(0.2, 9, 0.35):
    for y in np.arange(0.15, 3.83, 0.35):
        a = np.random.uniform(0.3, 0.7)
        ax.scatter(x, y, s=0.8, color='#c8d0da', alpha=a * 0.15, linewidths=0)

# ── Data points (bottom) ─────────────────────────────────────────────────
n_points = 90
data_x = np.random.uniform(0.5, 8.5, n_points)
data_y = np.random.uniform(0.2, 0.7, n_points)
data_c = np.random.choice([0, 1, 2], n_points)
colors = ['#2ea043', '#d29922', '#e74c3c']
for c in range(3):
    mask = data_c == c
    ax.scatter(data_x[mask], data_y[mask], s=18, color=colors[c],
               alpha=0.6, edgecolors='white', linewidth=0.5, zorder=2)

# Bootstrap circles — centered on actual data clusters
bootstrap_groups = [
    (1.8, 0.35, 0.40, 0, '#1f6feb'),   # green cluster
    (3.8, 0.40, 0.45, 1, '#1f6feb'),   # mixed cluster
    (5.8, 0.30, 0.35, 2, '#1f6feb'),   # yellow cluster
    (7.5, 0.45, 0.40, 0, '#1f6feb'),   # red cluster
]
for cx, cy, r, _, color in bootstrap_groups:
    circle = plt.Circle((cx, cy), r, color=color, fill=False,
                        lw=1.0, alpha=0.4, ls='--', zorder=1)
    ax.add_patch(circle)
    # Small "boot" label
    ax.text(cx, cy + r + 0.08, 'bootstrap', ha='center', va='bottom',
            fontsize=6, color=color, alpha=0.6, style='italic')

# ── Helper: draw a decision tree ─────────────────────────────────────────
def draw_tree(ax, cx, cy, scale=1.0, color='#1f6feb', highlight_feat=None):
    dx = 0.35 * scale
    dy = 0.30 * scale
    nodes = []

    root = (cx, cy)
    nodes.append(root)

    l1_left = (cx - dx, cy - dy)
    l1_right = (cx + dx, cy - dy)
    nodes.extend([l1_left, l1_right])

    l2_ll = (cx - dx * 1.6, cy - dy * 2)
    l2_lr = (cx - dx * 0.4, cy - dy * 2)
    l2_rl = (cx + dx * 0.4, cy - dy * 2)
    l2_rr = (cx + dx * 1.6, cy - dy * 2)
    nodes.extend([l2_ll, l2_lr, l2_rl, l2_rr])

    for parent, child in [(root, l1_left), (root, l1_right),
                          (l1_left, l2_ll), (l1_left, l2_lr),
                          (l1_right, l2_rl), (l1_right, l2_rr)]:
        ax.plot([parent[0], child[0]], [parent[1], child[1]],
                color=color, lw=0.8 + 0.3 * scale, alpha=0.6)

    for i, (nx, ny) in enumerate(nodes):
        if i == 0:
            sz = 40 * scale
            fc = color
            ec = '#ffffff'
            lw = 1.0
            alpha = 0.85
        elif i in [1, 2]:
            sz = 25 * scale
            fc = color
            ec = '#ffffff'
            lw = 0.8
            alpha = 0.6
        else:
            sz = 15 * scale
            fc = color
            ec = '#ffffff'
            lw = 0.5
            alpha = 0.4
        ax.scatter(nx, ny, s=sz, color=fc, edgecolors=ec,
                   linewidth=lw, alpha=alpha, zorder=3)

    if highlight_feat is not None:
        ax.text(root[0], root[1] + 0.1, f'f{highlight_feat}', ha='center', va='bottom',
                fontsize=6, color=color, alpha=0.85, fontweight='bold')

    return nodes

# ── Trees ────────────────────────────────────────────────────────────────
tree_specs = [
    (1.2, 2.6, 0.85, '#1f6feb', 3),
    (2.9, 2.4, 0.75, '#2ea043', 7),
    (4.9, 2.6, 0.85, '#d29922', 1),
    (6.9, 2.4, 0.75, '#e74c3c', 5),
]

for cx, cy, scale, color, feat in tree_specs:
    draw_tree(ax, cx, cy, scale, color, highlight_feat=feat)

# ── Random feature subset labels ────────────────────────────────────────
for cx, cy, _, color, feat in tree_specs:
    ax.text(cx, cy + 0.25, f'subset [{feat}, …]', ha='center', va='bottom',
            fontsize=6, color=color, alpha=0.75, style='italic')

# ── Arrows: data → each tree ────────────────────────────────────────────
for cx, cy, _, color, _ in tree_specs:
    ax.annotate('', xy=(cx, cy - 0.4 * (cy / 2.6)),
                xytext=(cx, 0.8),
                arrowprops=dict(arrowstyle='->', color=color, lw=0.8,
                                alpha=0.3, mutation_scale=7))

# ── Voting (right side) ─────────────────────────────────────────────────
# Each tree casts a vote → colored circles → majority wins
vote_colors = ['#2ea043', '#d29922', '#2ea043', '#2ea043']  # 3 greens, 1 yellow
tree_ends = [(1.3, 2.55), (2.95, 2.35), (5.0, 2.55), (6.95, 2.35)]
vote_x = 7.55  # x position of vote circles
vote_dy = 0.28

# Converging arrows from each tree to its vote circle
for i, (sx, sy) in enumerate(tree_ends):
    target_y = 1.4 + i * vote_dy
    ax.annotate('', xy=(vote_x, target_y),
                xytext=(sx + 0.2, sy - 0.05),
                arrowprops=dict(arrowstyle='->', color='#6b7688', lw=0.6,
                                alpha=0.35, connectionstyle='arc3,rad=0.10',
                                mutation_scale=5))

# Vote circles (each tree's prediction)
for i in range(4):
    vy = 1.4 + i * vote_dy
    circle = plt.Circle((vote_x, vy), 0.07, color=vote_colors[i],
                        ec='#ffffff', lw=0.8, alpha=0.85, zorder=4)
    ax.add_patch(circle)

# Equals sign
ax.text(vote_x + 0.2, 1.4 + 1.5 * vote_dy, '=', ha='center', va='center',
        fontsize=16, color='#0d1117', alpha=0.7, fontweight='bold')

# Result: majority class (green wins)
result_x = vote_x + 0.5
result_y = 1.4 + 1.5 * vote_dy
result_circle = plt.Circle((result_x, result_y), 0.13, color='#2ea043',
                           ec='#ffffff', lw=1.5, alpha=0.9, zorder=5)
ax.add_patch(result_circle)

# Tally text
ax.text(result_x, result_y - 0.22, '3/4', ha='center', va='top',
        fontsize=9, color='#0d1117', fontweight='bold', alpha=0.85)

# Small "votes" label
ax.text(vote_x, 1.4 + 4 * vote_dy + 0.08, '各树预测', ha='center', va='bottom',
        fontsize=6, color='#1f2328', alpha=0.65)
ax.text(result_x, 1.4 + 4 * vote_dy + 0.08, '最终结果', ha='center', va='bottom',
        fontsize=6, color='#1f2328', alpha=0.65)

# ── Bottom labels ────────────────────────────────────────────────────────
# Top border
ax.plot([1.0, 8.0], [3.55, 3.55], color='#d0d7de', lw=0.5)
ax.plot([1.0, 1.0], [3.55, 3.35], color='#d0d7de', lw=0.5)
ax.plot([8.0, 8.0], [3.55, 3.35], color='#d0d7de', lw=0.5)

# Bottom bar
ax.plot([1.5, 7.5], [1.05, 1.05], color='#d0d7de', lw=0.5)

labels = [('#1f6feb', 'Bootstrap\n有放回抽样'),
          ('#2ea043', '特征子集\n随机选择'),
          ('#d29922', '多树投票\n方差降低'),
          ('#e74c3c', 'OOB 验证')]
for i, (color, label) in enumerate(labels):
    x = 1.8 + i * 1.7
    ax.plot([x - 0.12, x + 0.12], [0.82, 0.82], color=color, lw=3)
    ax.text(x, 0.62, label, ha='center', va='center', fontsize=7,
            color='#0d1117', fontweight='bold', linespacing=1.4)

# ── Small decorative elements ───────────────────────────────────────────
# Feature cubes top-left
for i, (lx, col) in enumerate([(0.25, '#1f6feb'), (0.55, '#2ea043'), (0.85, '#d29922')]):
    rect = FancyBboxPatch((lx, 3.1), 0.15, 0.15, boxstyle="round,pad=0.02",
                           facecolor=col, edgecolor='#ffffff', lw=0.5, alpha=0.4)
    ax.add_patch(rect)
    ax.text(lx + 0.075, 3.0, f'feat_{i+1}', fontsize=5, color='#1f2328',
            ha='center', va='top', alpha=0.7)

# Subtle "n_estimators=100" annotation
ax.text(4.5, 3.3, 'n_estimators = 100     max_features = sqrt(n)',
        ha='center', va='center', fontsize=7, color='#0d1117', alpha=0.6,
        fontweight='bold')

# ── Save ─────────────────────────────────────────────────────────────────
import os
out = os.path.join(os.path.dirname(__file__), '..', 'articles', 'ml', 'cover_day5.png')
plt.savefig(out, dpi=100, facecolor='#f5f7fa')
print(f'Saved → {out}')
