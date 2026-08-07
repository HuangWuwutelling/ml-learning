"""
Cover for article 16: SEIR virus transmission model with 4 R0 curves.
figsize=(9, 3.83), dpi=100, no bbox_inches='tight' (per CLAUDE.md).

Style reference: cover_env_20.py (POPs sister article).
Visual: left half = stylized 4 epidemic curves + virus particle icons.
Right half = title text + key stat (R0 1.3 -> 18).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge, Rectangle, FancyBboxPatch

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

np.random.seed(16)

OUT = os.path.join(os.path.dirname(__file__), "..", "articles", "env",
                   "cover_env_16.png")

# 4 R0 病毒 + 配色 (冷色到暖色)
# (name, R0, latent_days, infect_days, peak_day, peak_height, color)
VIRUSES = [
    ("普通感冒",   1.5,  2.0, 5.0, 120, 0.42, "#1f4e9c"),
    ("季节性流感", 1.5,  2.0, 4.0,  70, 0.40, "#4ea1d3"),
    ("COVID-19",   3.0,  5.0, 7.0,  35, 0.78, "#f39c12"),
    ("麻疹",      15.0, 12.0, 6.0,  16, 0.92, "#d6532b"),
]


def seir_curve(peak_day, peak_height, n=200):
    """生成一条形状合理的 SEIR 感染曲线 I(t)/N.

    peak_day: 峰值出现的时间 (天)
    peak_height: 峰值高度 (0-1), 与 R0 正相关
    用一个不对称的 bell 曲线近似 (logistic 上升 + 指数衰减),
    R0 越大峰值越高、出现越早。
    """
    t = np.linspace(0, 200, n)
    rise_rate = 5.0 / peak_day          # 上升斜率
    fall_rate = 0.04                    # 衰减斜率
    rise = 1.0 / (1.0 + np.exp(-rise_rate * (t - peak_day)))
    fall = np.exp(-fall_rate * (t - peak_day))
    fall = np.where(t < peak_day, 1.0, fall)
    curve = rise * fall
    curve = curve / curve.max() * peak_height
    return t, curve


def draw_curves_panel(ax, x0, y0, w, h):
    """在 (x0,y0) 起宽 w 高 h 的矩形内绘制 4 条 SEIR 疫情曲线."""
    # 背景浅色面板
    panel = FancyBboxPatch((x0, y0), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.05",
                           facecolor="#ffffff", edgecolor="#d0d7de",
                           lw=0.8, zorder=2)
    ax.add_patch(panel)

    # 内嵌坐标轴范围 (相对面板)
    pad_l, pad_r, pad_t, pad_b = 0.30, 0.10, 0.20, 0.30
    plot_x0 = x0 + pad_l
    plot_y0 = y0 + pad_b
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    # 绘制坐标轴边框 + 网格
    ax.plot([plot_x0, plot_x0 + plot_w], [plot_y0, plot_y0],
            color="#9ca3af", lw=0.8, zorder=3)
    ax.plot([plot_x0, plot_x0], [plot_y0, plot_y0 + plot_h],
            color="#9ca3af", lw=0.8, zorder=3)

    for frac in (0.25, 0.50, 0.75):
        gy = plot_y0 + frac * plot_h
        ax.plot([plot_x0, plot_x0 + plot_w], [gy, gy],
                color="#e5e7eb", lw=0.4, ls=":", zorder=2)

    # 绘制 4 条曲线
    for name, R0, lat, inf, peak, height, color in VIRUSES:
        t, I = seir_curve(peak, height, n=200)
        xs = plot_x0 + (t / 200.0) * plot_w
        ys = plot_y0 + I * plot_h
        ax.plot(xs, ys, color=color, lw=2.0, zorder=4)

    # 轴标签
    ax.text(plot_x0 + plot_w / 2, plot_y0 - 0.12, "时间 (天)",
            fontsize=8, color="#4a525e", ha="center", va="top",
            zorder=5)
    ax.text(plot_x0 - 0.10, plot_y0 + plot_h / 2, "I(t)/N",
            fontsize=8, color="#4a525e", ha="right", va="center",
            rotation=90, zorder=5)
    ax.text(plot_x0, plot_y0 + plot_h + 0.05, "4 种 R0 疫情曲线对比",
            fontsize=9, color="#1f2328", ha="left", va="bottom",
            fontweight="bold", zorder=5)

    # 曲线末端图例: 用曲线末端位置贴标签, 错开避免重叠
    label_offsets = [
        ("普通感冒",   1.5, "#1f4e9c", 0.06),
        ("季节性流感", 1.5, "#4ea1d3", 0.18),
        ("COVID-19",   3.0, "#f39c12", 0.30),
        ("麻疹",      15.0, "#d6532b", 0.42),
    ]
    for name, R0, color, dy in label_offsets:
        ax.plot([plot_x0 + plot_w + 0.02, plot_x0 + plot_w + 0.08],
                [plot_y0 + dy, plot_y0 + dy],
                color=color, lw=2.0, zorder=5)
        ax.text(plot_x0 + plot_w + 0.12, plot_y0 + dy,
                f"{name}  R$_0$={R0:g}",
                fontsize=6.8, color=color, ha="left", va="center",
                fontweight="bold", zorder=5)


def draw_virus(ax, cx, cy, r, color, n_spikes=8, spike_len=0.08):
    """绘制一个带 spike 的病毒粒子图标."""
    # 核心圆
    core = Circle((cx, cy), r, facecolor=color, edgecolor="#1f2328",
                  lw=0.8, zorder=4)
    ax.add_patch(core)
    # 内部小圆点 (代表遗传物质)
    inner = Circle((cx - r * 0.15, cy + r * 0.05), r * 0.25,
                   facecolor="#ffffff", edgecolor="none", alpha=0.6,
                   zorder=5)
    ax.add_patch(inner)
    # spike (刺突糖蛋白)
    for k in range(n_spikes):
        ang = np.deg2rad(360.0 * k / n_spikes)
        x1 = cx + r * np.cos(ang)
        y1 = cy + r * np.sin(ang)
        x2 = cx + (r + spike_len) * np.cos(ang)
        y2 = cy + (r + spike_len) * np.sin(ang)
        ax.plot([x1, x2], [y1, y2], color=color, lw=1.2, zorder=3)
        # spike 顶端小球
        ax.add_patch(Circle((x2, y2), 0.012, facecolor=color,
                            edgecolor="#1f2328", lw=0.4, zorder=4))


def draw_seir_boxes(ax, x0, y0):
    """在右下角画一个小的 SEIR 4 仓室流程示意."""
    box_w, box_h = 0.30, 0.22
    gap = 0.06
    labels = [("S", "#1f77b4"), ("E", "#f39c12"),
              ("I", "#d6532b"), ("R", "#27ae60")]
    n = len(labels)
    total_w = n * box_w + (n - 1) * gap
    start_x = x0 - total_w / 2
    cy = y0
    centers = []
    for i, (lab, col) in enumerate(labels):
        bx = start_x + i * (box_w + gap)
        box = FancyBboxPatch((bx, cy - box_h / 2), box_w, box_h,
                             boxstyle="round,pad=0.01,rounding_size=0.03",
                             facecolor=col, edgecolor="#1f2328",
                             lw=0.6, alpha=0.85, zorder=4)
        ax.add_patch(box)
        ax.text(bx + box_w / 2, cy, lab, fontsize=10, color="white",
                ha="center", va="center", fontweight="bold", zorder=5)
        centers.append((bx + box_w / 2, cy))

    # 箭头 S -> E -> I -> R, 并加一条 I -> R 的虚线箭头
    for i in range(n - 1):
        x_a = centers[i][0] + box_w / 2
        x_b = centers[i + 1][0] - box_w / 2
        ax.annotate("", xy=(x_b - 0.01, cy), xytext=(x_a + 0.01, cy),
                    arrowprops=dict(arrowstyle="->", color="#4a525e",
                                    lw=0.8, shrinkA=0, shrinkB=0),
                    zorder=5)


# ---------------------------------------------------------------------------
# Cover
# ---------------------------------------------------------------------------
def article_cover():
    fig, ax = plt.subplots(figsize=(9, 3.83))
    fig.patch.set_facecolor("#fafbfc")
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 3.83)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Subtle dot background ─────────────────────────────────────────
    for _ in range(150):
        x = np.random.uniform(0.2, 8.8)
        y = np.random.uniform(0.2, 3.6)
        ax.scatter(x, y, s=0.8, color="#4a525e",
                   alpha=np.random.uniform(0.04, 0.10),
                   linewidths=0, zorder=1)

    # ── Left: 4 R0 curves panel ───────────────────────────────────────
    draw_curves_panel(ax, x0=0.30, y0=1.20, w=4.20, h=2.20)

    # ── Virus icons (decorative) ──────────────────────────────────────
    # 流感病毒 (中等蓝)
    draw_virus(ax, cx=0.85, cy=0.55, r=0.18, color="#4ea1d3",
               n_spikes=8, spike_len=0.08)
    # 麻疹病毒 (红)
    draw_virus(ax, cx=2.10, cy=0.55, r=0.16, color="#d6532b",
               n_spikes=10, spike_len=0.07)
    # 感冒病毒 (深蓝)
    draw_virus(ax, cx=3.35, cy=0.55, r=0.14, color="#1f4e9c",
               n_spikes=7, spike_len=0.06)
    # COVID 病毒 (橙)
    draw_virus(ax, cx=4.30, cy=0.55, r=0.15, color="#f39c12",
               n_spikes=9, spike_len=0.07)

    # ── Right: title + key stat ───────────────────────────────────────
    # 副标题 (上方一行)
    ax.text(7.10, 3.32, "传染动力学经典",
            fontsize=11, color="#7b1fa2", ha="center", va="center",
            fontweight="bold", zorder=5, style="italic")

    # 主标题
    ax.text(7.10, 2.92, "麻疹为什么必须打疫苗",
            fontsize=19, color="#1f2328", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 2.50, "感冒不用？从病毒的传染力说起",
            fontsize=13, color="#1f2328", ha="center", va="center",
            fontweight="bold", zorder=5)

    # 关键数字 R0 范围
    ax.text(7.10, 1.85, "R$_0$  =  1.3  →  18",
            fontsize=14, color="#d6532b", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 1.55, "（感冒 R0 ~1.5，麻疹 R0 ~15）",
            fontsize=8, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    # ── SEIR 4 仓室 mini 流程图 (右下角) ─────────────────────────────
    draw_seir_boxes(ax, x0=7.10, y0=1.05)
    ax.text(7.10, 0.75, "4 仓室: 易感 → 暴露 → 感染 → 康复",
            fontsize=7.5, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    plt.savefig(OUT, dpi=100, facecolor="#fafbfc")
    plt.close(fig)
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    article_cover()
    print("\n=== cover generated ===")
