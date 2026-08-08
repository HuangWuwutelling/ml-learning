"""wali_cmd 小程序头像生成器。

设计要点：
- 144x144 PNG（微信小程序头像标准）
- 黑底 + 绿色终端主题（呼应 tabBar 颜色 #3cc51f）
- 中央：>_ 提示符（命令行最具辨识度的符号）
- 上方短横线模拟终端窗口栏
- 简洁，对小尺寸也清晰

用法：python scripts/gen_avatar.py
输出：projects/wali_cmd/avatar.png
"""
import os

import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT = os.path.join(os.path.dirname(__file__), "..", "avatar.png")

# 主题色（与 tabBar / tab.active 保持一致）
BG = "#1f2328"          # 终端黑
FG_GREEN = "#3cc51f"    # 终端绿（小程序主色）
FG_MUTED = "#656d76"    # 窗口栏灰色
CURSOR_BG = "#3cc51f"   # 光标填充色

# 144×144 头像
SIZE = 144
DPI = 100


def draw_avatar():
    fig, ax = plt.subplots(figsize=(SIZE / DPI, SIZE / DPI), dpi=DPI)
    fig.patch.set_facecolor("white")  # 头像背景（小程序会自动裁圆，外面留白干净）
    ax.set_xlim(0, SIZE)
    ax.set_ylim(0, SIZE)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── 终端窗口圆角矩形（占据头像中心区域，留出圆角余量）──
    margin = 18
    terminal = patches.FancyBboxPatch(
        (margin, margin),
        SIZE - 2 * margin,
        SIZE - 2 * margin,
        boxstyle="round,pad=0,rounding_size=10",
        facecolor=BG,
        edgecolor="none",
        zorder=1,
    )
    ax.add_patch(terminal)

    # ── 顶部窗口栏（macOS 风格三圆点）──
    bar_h = 18
    bar = patches.Rectangle(
        (margin, SIZE - margin - bar_h),
        SIZE - 2 * margin,
        bar_h,
        facecolor="#2d3138",
        edgecolor="none",
        zorder=2,
    )
    ax.add_patch(bar)

    # 三个圆点（红黄绿）
    dot_y = SIZE - margin - bar_h / 2
    for i, color in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        ax.add_patch(patches.Circle(
            (margin + 12 + i * 12, dot_y),
            3.5, facecolor=color, edgecolor="none", zorder=3
        ))

    # ── 中央：cmd _（命令行速查主体）──
    cx = SIZE / 2
    cy = SIZE / 2 - 4

    # "cmd" 文字（绿色加粗，monospace）
    ax.text(
        cx, cy, "cmd",
        fontsize=42, color=FG_GREEN,
        fontfamily="monospace",
        fontweight="bold",
        ha="center", va="center",
        zorder=4,
    )

    # 下划线光标（绿色填充矩形，模拟闪烁光标，在 cmd 右侧）
    cursor = patches.Rectangle(
        (cx + 36, cy - 14),
        4, 22,
        facecolor=CURSOR_BG,
        edgecolor="none",
        zorder=5,
    )
    ax.add_patch(cursor)

    plt.savefig(OUT, dpi=DPI, facecolor="white", bbox_inches=None)
    plt.close(fig)
    print(f"Saved -> {OUT}")


if __name__ == "__main__":
    draw_avatar()