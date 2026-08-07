"""
Cover for article 17: 分布式光伏对配电网的影响 (4 种渗透率临界点).
figsize=(9, 3.83), dpi=100, no bbox_inches='tight' (per CLAUDE.md).

Style reference: cover_env_16.py (SEIR sister article).
Visual: left = 4-node 馈线 + 屋顶光伏 + 4 渗透率柱状图;
        right = 标题 + 关键数字 (临界渗透率 40.1%)。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (
    FancyBboxPatch, Circle, Rectangle, Polygon,
)

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

np.random.seed(17)

OUT = os.path.join(os.path.dirname(__file__), "..", "articles", "env",
                   "cover_env_17.png")

# 4 渗透率配色 (绿 -> 黄 -> 橙 -> 红, 由低到高)
PEN_COLORS = ["#27ae60", "#f1c40f", "#e67e22", "#d6532b"]
PEN_LABELS = ["10%", "30%", "50%", "70%"]
# 节点 3 电压 (noon 极端场景, 模型输出)
PEN_V3 = [1.017, 1.052, 1.087, 1.122]


def draw_house_pv(ax, cx, cy, w, h):
    """绘制一个简化屋顶光伏房屋图标: 屋顶三角形 + 屋顶光伏板."""
    # 房屋主体 (矩形)
    house = Rectangle((cx - w / 2, cy - h / 2), w, h * 0.85,
                      facecolor="#f4ecd8", edgecolor="#1f2328",
                      lw=0.8, zorder=3)
    ax.add_patch(house)
    # 屋顶 (三角形)
    roof_h = h * 0.45
    roof = Polygon([
        (cx - w / 2 - 0.02, cy - h / 2 + h * 0.85),
        (cx + w / 2 + 0.02, cy - h / 2 + h * 0.85),
        (cx, cy - h / 2 + h * 0.85 + roof_h),
    ], closed=True, facecolor="#c0392b", edgecolor="#1f2328",
       lw=0.8, zorder=4)
    ax.add_patch(roof)
    # 光伏板 (屋顶上的蓝色矩形, 网格)
    panel_w = w * 0.55
    panel_h = roof_h * 0.55
    panel = Rectangle((cx - panel_w / 2,
                      cy - h / 2 + h * 0.85 + roof_h * 0.30),
                     panel_w, panel_h,
                     facecolor="#1f4e9c", edgecolor="#1f2328",
                     lw=0.6, zorder=5)
    ax.add_patch(panel)
    # 板内 2x3 网格
    for ix in range(1, 3):
        xp = (cx - panel_w / 2) + ix * panel_w / 3
        ax.plot([xp, xp],
                [cy - h / 2 + h * 0.85 + roof_h * 0.30,
                 cy - h / 2 + h * 0.85 + roof_h * 0.30 + panel_h],
                color="#cfd8dc", lw=0.3, zorder=6)
    for iy in range(1, 2):
        yp = (cy - h / 2 + h * 0.85 + roof_h * 0.30) + iy * panel_h / 2
        ax.plot([cx - panel_w / 2, cx + panel_w / 2],
                [yp, yp],
                color="#cfd8dc", lw=0.3, zorder=6)


def draw_grid_schematic(ax, x0, y0):
    """绘制 4 节点串型馈线: 变压器 -> node1 -> node2 -> node3."""
    # 起点 (变压器) 坐标
    tx0, ty0 = x0, y0 + 0.05
    # 节点等间距
    spacing = 0.55
    node_y = y0 + 0.05

    # 馈线 (水平主线)
    ax.plot([tx0, tx0 + 3 * spacing], [node_y, node_y],
            color="#1f2328", lw=1.5, zorder=4)

    # 变压器符号 (双圆 + T 字母)
    tx = tx0 - 0.05
    ax.add_patch(Circle((tx, node_y), 0.10,
                        facecolor="#1f4e9c", edgecolor="#1f2328",
                        lw=0.8, zorder=5))
    ax.text(tx, node_y, "T", fontsize=9, color="white",
            ha="center", va="center", fontweight="bold", zorder=6)
    # 10 kV / 380 V 标注
    ax.text(tx, node_y + 0.20, "400 kVA", fontsize=6, color="#4a525e",
            ha="center", va="bottom", zorder=5)
    ax.text(tx, node_y - 0.20, "10kV/380V", fontsize=5.5,
            color="#9ca3af", ha="center", va="top", zorder=5,
            style="italic")

    # 3 个节点 (圆 + 编号)
    for i in range(3):
        nx = tx0 + (i + 1) * spacing
        ax.add_patch(Circle((nx, node_y), 0.08,
                            facecolor="#ffffff", edgecolor="#1f2328",
                            lw=1.0, zorder=5))
        ax.text(nx, node_y, f"N{i + 1}", fontsize=7, color="#1f2328",
                ha="center", va="center", fontweight="bold", zorder=6)

    # 4 个屋顶光伏房屋 (每个节点上方)
    house_w, house_h = 0.30, 0.28
    for i in range(4):
        if i == 0:
            # 变压器侧也代表 1 户
            hx = tx
        else:
            hx = tx0 + i * spacing
        hy = node_y + 0.55
        draw_house_pv(ax, hx, hy, house_w, house_h)


def draw_penetration_bars(ax, x0, y0, w, h):
    """在 (x0,y0) 起宽 w 高 h 的矩形内绘制 4 渗透率柱状图 + 1.07 pu 限位."""
    # 背景浅色面板
    panel = FancyBboxPatch((x0, y0), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.05",
                           facecolor="#ffffff", edgecolor="#d0d7de",
                           lw=0.8, zorder=2)
    ax.add_patch(panel)

    # 内嵌坐标轴范围
    pad_l, pad_r, pad_t, pad_b = 0.34, 0.18, 0.18, 0.30
    plot_x0 = x0 + pad_l
    plot_y0 = y0 + pad_b
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    # y 轴范围: 0.95 - 1.15 (包含 1.07 限位 + 数据)
    v_min, v_max = 0.95, 1.15

    def v_to_y(v):
        return plot_y0 + (v - v_min) / (v_max - v_min) * plot_h

    # 坐标轴边框
    ax.plot([plot_x0, plot_x0 + plot_w], [plot_y0, plot_y0],
            color="#9ca3af", lw=0.8, zorder=3)
    ax.plot([plot_x0, plot_x0], [plot_y0, plot_y0 + plot_h],
            color="#9ca3af", lw=0.8, zorder=3)

    # 水平网格 (0.95/1.00/1.05/1.10)
    for v in (0.95, 1.00, 1.05, 1.10):
        gy = v_to_y(v)
        ax.plot([plot_x0, plot_x0 + plot_w], [gy, gy],
                color="#e5e7eb", lw=0.4, ls=":", zorder=2)
        ax.text(plot_x0 - 0.04, gy, f"{v:.2f}", fontsize=6.5,
                color="#4a525e", ha="right", va="center", zorder=5)

    # 1.07 pu 红色虚线 (GB/T 12325 上限)
    y_limit = v_to_y(1.07)
    ax.plot([plot_x0, plot_x0 + plot_w], [y_limit, y_limit],
            color="#d6532b", lw=1.2, ls="--", zorder=4)
    ax.text(plot_x0 + plot_w + 0.02, y_limit, "1.07 pu",
            fontsize=6.5, color="#d6532b", ha="left", va="center",
            fontweight="bold", zorder=5)

    # 4 个柱
    n = len(PEN_V3)
    bar_w = plot_w / n * 0.55
    gap = plot_w / n * 0.45
    for i, (v, color, lab) in enumerate(zip(PEN_V3, PEN_COLORS, PEN_LABELS)):
        bx = plot_x0 + (i + 0.5) * (bar_w + gap)
        # 柱体
        bar = Rectangle((bx, plot_y0), bar_w, v_to_y(v) - plot_y0,
                        facecolor=color, edgecolor="#1f2328",
                        lw=0.5, alpha=0.85, zorder=4)
        ax.add_patch(bar)
        # 柱顶数值
        ax.text(bx + bar_w / 2, v_to_y(v) + 0.02,
                f"{v:.3f}", fontsize=6.5, color="#1f2328",
                ha="center", va="bottom", fontweight="bold", zorder=5)
        # 柱底渗透率标签
        ax.text(bx + bar_w / 2, plot_y0 - 0.08, lab,
                fontsize=8, color=color, ha="center", va="top",
                fontweight="bold", zorder=5)

    # y 轴标题
    ax.text(plot_x0 - 0.18, plot_y0 + plot_h / 2, "V$_3$ (pu)",
            fontsize=7.5, color="#4a525e", ha="right", va="center",
            rotation=90, zorder=5)
    # x 轴标题
    ax.text(plot_x0 + plot_w / 2, plot_y0 - 0.20, "渗透率 (PV 装机 / 峰值负荷)",
            fontsize=7, color="#4a525e", ha="center", va="top", zorder=5)
    # 面板标题
    ax.text(plot_x0, plot_y0 + plot_h + 0.05, "4 种渗透率下节点 3 电压",
            fontsize=9, color="#1f2328", ha="left", va="bottom",
            fontweight="bold", zorder=5)


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

    # ── Left top: 4-node 馈线示意 ─────────────────────────────────────
    draw_grid_schematic(ax, x0=0.60, y0=2.55)

    # ── Left bottom: 4 渗透率柱状图 ───────────────────────────────────
    draw_penetration_bars(ax, x0=0.30, y0=0.50, w=4.20, h=1.55)

    # ── Right: 标题 + 关键数字 ───────────────────────────────────────
    # 副标题 (上方一行)
    ax.text(7.10, 3.32, "配电网电压临界点",
            fontsize=11, color="#7b1fa2", ha="center", va="center",
            fontweight="bold", zorder=5, style="italic")

    # 主标题
    ax.text(7.10, 2.95, "分布式光伏",
            fontsize=22, color="#1f2328", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 2.55, "对配电网的影响",
            fontsize=17, color="#1f2328", ha="center", va="center",
            fontweight="bold", zorder=5)

    # 关键数字: 临界渗透率
    ax.text(7.10, 1.95, "临界渗透率",
            fontsize=9, color="#4a525e", ha="center", va="center",
            zorder=5)
    ax.text(7.10, 1.65, "40.1 %",
            fontsize=22, color="#d6532b", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 1.32, "（noon, V$_3$ 触 1.07 pu）",
            fontsize=7.5, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    # 副数字: 中国分布式光伏装机
    ax.text(7.10, 1.02, "370 GW",
            fontsize=12, color="#27ae60", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 0.78, "中国 2024 分布式光伏累计装机",
            fontsize=7, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    # ── Bottom tag ───────────────────────────────────────────────────
    ax.plot([4.5, 8.7], [0.32, 0.32], color="#d0d7de", lw=0.5, zorder=2)
    ax.text(7.10, 0.20,
            "GB/T 12325-2008  ·  IEEE 1547-2018  ·  国家能源局 2024  ·  "
            "Braun 2012 IET RPG",
            fontsize=5.5, color="#9ca3af",
            ha="center", alpha=0.65, fontweight="bold", zorder=5)

    plt.savefig(OUT, dpi=100, facecolor="#fafbfc")
    plt.close(fig)
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    article_cover()
    print("\n=== cover generated ===")