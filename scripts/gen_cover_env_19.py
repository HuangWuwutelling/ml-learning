"""
Cover for article 19: 西电东输：UHVDC 物理 (env/19).
figsize=(9, 3.83), dpi=100, no bbox_inches='tight' (per CLAUDE.md).

Style reference: cover_env_17.py (PV sister article, "发输配" 完整能源链).
Visual: left = UHVDC 输电塔 + 西部电源图标 + 4 电源容量系数柱状图;
        right = 标题 + 关键数字 (12000 MW = 12 个百万千瓦级核电机组).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import (
    FancyBboxPatch, Circle, Rectangle, Polygon, FancyArrowPatch,
)

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

np.random.seed(19)

OUT = os.path.join(os.path.dirname(__file__), "..", "articles", "env",
                   "cover_env_19.png")

# 4 电源容量系数 (与 fig_env_19_4sources_capacity.png 一致)
SOURCE_CF = [50, 55, 25, 17]   # 水/火/风/光
SOURCE_LABELS = ["水电", "火电", "风电", "光伏"]
# 配色 (与 fig1 一致, 可调度性 高绿 → 低红)
SOURCE_COLORS = ["#1a9850", "#66bd63", "#fee08b", "#d73027"]


def draw_pylon(ax, cx, cy, h):
    """绘制一个简化输电塔 (梯形塔身 + 横担 + 双极导线)。
    cx, cy 为塔底中心; h 为总高。
    """
    w_top = h * 0.18
    w_bot = h * 0.55
    # 塔身 (梯形)
    body = Polygon([
        (cx - w_top / 2, cy + h * 0.45),
        (cx + w_top / 2, cy + h * 0.45),
        (cx + w_bot / 2, cy),
        (cx - w_bot / 2, cy),
    ], closed=True, facecolor="#9ca3af", edgecolor="#1f2328",
       lw=0.6, zorder=4)
    ax.add_patch(body)
    # 塔身内部 X 形桁架 (2 层)
    for fy in (0.15, 0.30):
        y0 = cy + fy * h
        ax.plot([cx - w_bot / 2 + 0.02, cx + w_bot / 2 - 0.02],
                [y0, y0 + h * 0.15], color="#1f2328",
                lw=0.4, zorder=5)
        ax.plot([cx - w_bot / 2 + 0.02, cx + w_bot / 2 - 0.02],
                [y0 + h * 0.15, y0], color="#1f2328",
                lw=0.4, zorder=5)
    # 横担 (顶部, 3 层, 长)
    arm_w = h * 1.10
    for i, frac in enumerate((0.85, 0.70, 0.55)):
        y = cy + frac * h
        ax.plot([cx - arm_w / 2, cx + arm_w / 2], [y, y],
                color="#1f2328", lw=1.0, zorder=5)
        # 绝缘子小竖线
        for sx in (-arm_w / 2, 0, arm_w / 2):
            ax.plot([cx + sx, cx + sx], [y, y - h * 0.06],
                    color="#1f2328", lw=0.5, zorder=5)
            ax.add_patch(Circle((cx + sx, y - h * 0.07), 0.012,
                                facecolor="#1f2328", edgecolor="none",
                                zorder=5))
    # 塔尖
    tip = Polygon([
        (cx - 0.02, cy + h * 0.95),
        (cx + 0.02, cy + h * 0.95),
        (cx, cy + h * 1.05),
    ], closed=True, facecolor="#1f2328", edgecolor="#1f2328",
       lw=0.4, zorder=4)
    ax.add_patch(tip)


def draw_source_icon(ax, cx, cy, kind, size=0.30):
    """绘制 4 种西部电源简化图标 (小圆形 + 标签)。"""
    if kind == "hydro":     # 水: 蓝色水滴
        ax.add_patch(Circle((cx, cy), size * 0.55,
                            facecolor="#3b82f6", edgecolor="#1f2328",
                            lw=0.6, alpha=0.9, zorder=5))
        ax.text(cx, cy, "H2O", fontsize=6, color="white",
                ha="center", va="center", fontweight="bold", zorder=6)
    elif kind == "thermal":  # 火: 红色火焰三角形
        flame = Polygon([
            (cx, cy + size * 0.55),
            (cx + size * 0.40, cy - size * 0.30),
            (cx - size * 0.40, cy - size * 0.30),
        ], closed=True, facecolor="#d73027", edgecolor="#1f2328",
           lw=0.6, zorder=5)
        ax.add_patch(flame)
        ax.add_patch(Circle((cx, cy - size * 0.10), size * 0.18,
                            facecolor="#fde68a", edgecolor="none",
                            zorder=6))
    elif kind == "wind":     # 风: 3 叶风扇
        for ang in (90, 210, 330):
            rad = np.deg2rad(ang)
            x_tip = cx + size * 0.55 * np.cos(rad)
            y_tip = cy + size * 0.55 * np.sin(rad)
            ax.plot([cx, x_tip], [cy, y_tip], color="#1f2328",
                    lw=1.5, zorder=5)
            ax.add_patch(Circle((x_tip, y_tip), size * 0.10,
                                facecolor="#1f2328", edgecolor="none",
                                zorder=6))
        ax.add_patch(Circle((cx, cy), size * 0.12,
                            facecolor="#1f2328", edgecolor="none",
                            zorder=6))
    else:  # solar: 黄方块 + 太阳
        ax.add_patch(Rectangle((cx - size * 0.45, cy - size * 0.45),
                               size * 0.90, size * 0.90,
                               facecolor="#1f4e9c", edgecolor="#1f2328",
                               lw=0.6, zorder=5))
        # 2x2 格子
        for ix in (0, 1):
            for iy in (0, 1):
                ax.add_patch(Rectangle(
                    (cx - size * 0.45 + ix * size * 0.45,
                     cy - size * 0.45 + iy * size * 0.45),
                    size * 0.45, size * 0.45,
                    facecolor="#3b82f6", edgecolor="#cfd8dc",
                    lw=0.3, zorder=6))


def draw_capacity_bars(ax, x0, y0, w, h):
    """在 (x0,y0) 起宽 w 高 h 的矩形内绘制 4 电源容量系数柱状图."""
    # 背景浅色面板
    panel = FancyBboxPatch((x0, y0), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.05",
                           facecolor="#ffffff", edgecolor="#d0d7de",
                           lw=0.8, zorder=2)
    ax.add_patch(panel)

    pad_l, pad_r, pad_t, pad_b = 0.32, 0.14, 0.20, 0.32
    plot_x0 = x0 + pad_l
    plot_y0 = y0 + pad_b
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    v_min, v_max = 0, 65

    def v_to_y(v):
        return plot_y0 + (v - v_min) / (v_max - v_min) * plot_h

    # 坐标轴边框
    ax.plot([plot_x0, plot_x0 + plot_w], [plot_y0, plot_y0],
            color="#9ca3af", lw=0.8, zorder=3)
    ax.plot([plot_x0, plot_x0], [plot_y0, plot_y0 + plot_h],
            color="#9ca3af", lw=0.8, zorder=3)

    # 水平网格 (20/40/60)
    for v in (20, 40, 60):
        gy = v_to_y(v)
        ax.plot([plot_x0, plot_x0 + plot_w], [gy, gy],
                color="#e5e7eb", lw=0.4, ls=":", zorder=2)
        ax.text(plot_x0 - 0.04, gy, f"{v}", fontsize=6,
                color="#4a525e", ha="right", va="center", zorder=5)

    # 4 个柱
    n = len(SOURCE_CF)
    bar_w = plot_w / n * 0.55
    gap = plot_w / n * 0.45
    for i, (v, color, lab) in enumerate(
            zip(SOURCE_CF, SOURCE_COLORS, SOURCE_LABELS)):
        bx = plot_x0 + (i + 0.5) * (bar_w + gap)
        bar = Rectangle((bx, plot_y0), bar_w, v_to_y(v) - plot_y0,
                        facecolor=color, edgecolor="#1f2328",
                        lw=0.5, alpha=0.9, zorder=4)
        ax.add_patch(bar)
        # 柱顶数值
        ax.text(bx + bar_w / 2, v_to_y(v) + 0.03,
                f"{v}%", fontsize=7, color="#1f2328",
                ha="center", va="bottom", fontweight="bold", zorder=5)
        # 柱底标签 (含 电源图标 微缩)
        draw_source_icon(ax, bx + bar_w / 2 - 0.10,
                         plot_y0 - 0.08, SOURCE_LABELS[i].replace(
                             "电", "").replace("光", "solar").replace(
                             "风", "wind").replace("水", "hydro").replace(
                             "火", "thermal"),
                         size=0.13)
        ax.text(bx + bar_w / 2 + 0.08, plot_y0 - 0.08, lab,
                fontsize=8, color="#1f2328", ha="left", va="center",
                fontweight="bold", zorder=5)

    # y 轴标题
    ax.text(plot_x0 - 0.20, plot_y0 + plot_h / 2,
            "容量系数 (%)", fontsize=7.5, color="#4a525e",
            ha="right", va="center", rotation=90, zorder=5)
    # 面板标题
    ax.text(plot_x0, plot_y0 + plot_h + 0.05,
            "4 种电源容量系数",
            fontsize=9.5, color="#1f2328", ha="left", va="bottom",
            fontweight="bold", zorder=5)


def draw_west_east_schematic(ax, x0, y0, w, h):
    """绘制 西部电源 + 双极直流线路 + 东部负荷 简化示意."""
    # 左侧 西部电源方块
    west_box = FancyBboxPatch((x0, y0), 0.55, h,
                              boxstyle="round,pad=0.02,rounding_size=0.04",
                              facecolor="#1a9850", edgecolor="#1f2328",
                              lw=0.6, alpha=0.85, zorder=4)
    ax.add_patch(west_box)
    ax.text(x0 + 0.275, y0 + h * 0.65, "西", fontsize=11,
            color="white", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(x0 + 0.275, y0 + h * 0.35, "电源", fontsize=7,
            color="white", ha="center", va="center", zorder=5)

    # 中间 输电塔 + 双极线
    pylon_x = x0 + 0.40
    pylon_h = h * 0.85
    pylon_y = y0
    draw_pylon(ax, pylon_x, pylon_y, pylon_h)

    # 双极导线 (从塔顶横担引出, 向左连西, 向右连东)
    line_top = y0 + pylon_h * 0.85
    line_bot = y0 + pylon_h * 0.70
    ax.plot([x0 + 0.55, x0 + 0.80], [line_top, line_top],
            color="#0d3b66", lw=1.0, zorder=3)
    ax.plot([x0 + 0.55, x0 + 0.80], [line_bot, line_bot],
            color="#0d3b66", lw=1.0, zorder=3)

    # 右侧 东部负荷方块
    east_x = x0 + w - 0.55
    east_box = FancyBboxPatch((east_x, y0), 0.55, h,
                              boxstyle="round,pad=0.02,rounding_size=0.04",
                              facecolor="#d73027", edgecolor="#1f2328",
                              lw=0.6, alpha=0.85, zorder=4)
    ax.add_patch(east_box)
    ax.text(east_x + 0.275, y0 + h * 0.65, "东", fontsize=11,
            color="white", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(east_x + 0.275, y0 + h * 0.35, "负荷", fontsize=7,
            color="white", ha="center", va="center", zorder=5)

    # 直流线从塔右侧引出
    ax.plot([x0 + 0.80, east_x], [line_top, line_top],
            color="#0d3b66", lw=1.0, zorder=3)
    ax.plot([x0 + 0.80, east_x], [line_bot, line_bot],
            color="#0d3b66", lw=1.0, zorder=3)

    # ±1100 kV 标注
    ax.text(x0 + w / 2, line_top + 0.05, "+1100 kV",
            fontsize=6.5, color="#0d3b66", ha="center",
            va="bottom", fontweight="bold", zorder=5)
    ax.text(x0 + w / 2, line_bot - 0.05, "-1100 kV",
            fontsize=6.5, color="#0d3b66", ha="center",
            va="top", fontweight="bold", zorder=5)

    # 距离标签
    ax.text(x0 + w / 2, y0 - 0.10, "≈ 3000 km",
            fontsize=7, color="#4a525e", ha="center",
            va="top", style="italic", zorder=5)


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

    # ── Left top: 西部-塔-东部 输电示意 ────────────────────────────────
    draw_west_east_schematic(ax, x0=0.50, y0=2.60, w=4.00, h=0.85)

    # ── Left bottom: 4 电源容量系数柱状图 ─────────────────────────────
    draw_capacity_bars(ax, x0=0.30, y0=0.50, w=4.20, h=1.55)

    # ── Right: 标题 + 关键数字 ───────────────────────────────────────
    # 副标题 (上方一行, 紫色斜体, 与 cover_env_17 一致)
    ax.text(7.10, 3.32, "12 个百万千瓦级核电机组的体量",
            fontsize=10, color="#7b1fa2", ha="center", va="center",
            fontweight="bold", zorder=5, style="italic")

    # 主标题 (两行)
    ax.text(7.10, 2.95, "西电东输",
            fontsize=24, color="#1f2328", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 2.55, "UHVDC 物理",
            fontsize=17, color="#1f2328", ha="center", va="center",
            fontweight="bold", zorder=5)

    # 关键数字 1: 12000 MW 容量
    ax.text(7.10, 2.00, "12000 MW",
            fontsize=22, color="#d73027", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 1.72, "（±1100 kV 单极满载）",
            fontsize=7.5, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    # 关键数字 2: 年减 CO2 (绿色, 减碳)
    ax.text(7.10, 1.30, "8500 万 t / 年",
            fontsize=14, color="#1a9850", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 1.05, "替代东部燃煤减碳 (容量系数 0.95)",
            fontsize=7, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    # 关键数字 3: P_loss ∝ 1/V²
    ax.text(7.10, 0.78, "P$_{\\mathrm{loss}}$ ∝ 1/V²",
            fontsize=11, color="#0d3b66", ha="center", va="center",
            fontweight="bold", zorder=5)
    ax.text(7.10, 0.58, "电压升 2.2 倍, 损耗降到 1/4.85",
            fontsize=7, color="#4a525e", ha="center", va="center",
            zorder=5, style="italic")

    # ── Bottom tag ───────────────────────────────────────────────────
    ax.plot([4.5, 8.7], [0.32, 0.32], color="#d0d7de", lw=0.5, zorder=2)
    ax.text(7.10, 0.18,
            "国家电网 2024  ·  IEA Renewables 2024  ·  "
            "CIGRE B4-52  ·  IEEE Std 1764  ·  IPCC 2006",
            fontsize=5.5, color="#9ca3af",
            ha="center", alpha=0.65, fontweight="bold", zorder=5)

    plt.savefig(OUT, dpi=100, facecolor="#fafbfc")
    plt.close(fig)
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    article_cover()
    print("\n=== cover generated ===")