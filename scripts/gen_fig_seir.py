"""生成 env/16 SEIR 传染病传播模型的三张配图。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from models.seir import SEIR

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(__file__), "..", "articles", "env")
os.makedirs(OUT, exist_ok=True)

# 与 R0 大小对应的冷到暖配色，兼顾曲线识别和科普阅读。
R0_COLORS = {
    "common_cold": "#377eb8",
    "seasonal_flu": "#4daf4a",
    "covid_wuhan": "#ff7f00",
    "measles": "#e41a1c",
}
R0_LABELS = {
    "common_cold": "普通感冒 (R0=1.5)",
    "seasonal_flu": "季节性流感 (R0=1.5)",
    "covid_wuhan": "COVID-19 武汉原始株 (R0=3.0)",
    "measles": "麻疹 (R0=15.0)",
}


def _style_axes(ax):
    ax.set_facecolor("#fafbfc")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#d0d7de")
    ax.spines["bottom"].set_color("#d0d7de")
    ax.grid(True, axis="y", color="#e5e7eb", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)


def _save(fig, filename):
    path = os.path.join(OUT, filename)
    fig.savefig(path, dpi=100, facecolor="white")
    plt.close(fig)
    print(f"Saved -> {path}")


def fig1_r0_curves():
    """绘制四种病毒的感染比例曲线，并标注各自峰值。"""
    viruses = ["common_cold", "seasonal_flu", "covid_wuhan", "measles"]
    results = {}
    for virus in viruses:
        model = SEIR(virus=virus, N=100000)
        results[virus] = model.solve(days=200, dt=0.1)

    fig, ax = plt.subplots(figsize=(10, 6))
    _style_axes(ax)
    for virus in viruses:
        result = results[virus]
        line, = ax.plot(result["t"], result["I"] / 100000,
                        color=R0_COLORS[virus], linewidth=2.3,
                        label=R0_LABELS[virus], zorder=3)
        peak_idx = int(result["I"].argmax())
        peak_t = result["t"][peak_idx]
        peak_ratio = result["I"][peak_idx] / 100000
        ax.scatter([peak_t], [peak_ratio], color=line.get_color(),
                   edgecolor="white", linewidth=1.2, s=48, zorder=5)
        dx = 7 if virus != "measles" else -28
        dy = 12 if virus != "measles" else -28
        ax.annotate(f"峰值: {peak_t:.0f} 天, {peak_ratio:.1%}",
                    xy=(peak_t, peak_ratio), xytext=(dx, dy),
                    textcoords="offset points", fontsize=8.5,
                    color="#2d3748",
                    arrowprops=dict(arrowstyle="->", color=line.get_color(),
                                    linewidth=0.9), zorder=6)

    ax.set_xlim(0, 200)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("天数 (days)", fontsize=11, color="#2d3748")
    ax.set_ylabel("感染人数比例 I(t) / N", fontsize=11, color="#2d3748")
    ax.set_title("4 种病毒 R0 下的疫情曲线对比", fontsize=15,
                 fontweight="bold", color="#1f2328", pad=12)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.96,
              edgecolor="#d0d7de")
    fig.text(0.5, 0.018,
             "同一初始条件下，R0 越高，感染峰值越早且同时感染比例越高。",
             ha="center", fontsize=9, color="#4a525e", style="italic")
    fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.13)
    _save(fig, "fig_env_16_4R0_curves.png")


def fig2_compartments():
    """绘制 COVID-19 R0=3.0 场景的四仓室比例曲线。"""
    model = SEIR(virus="covid_wuhan", N=100000)
    result = model.solve(days=200, dt=0.1)
    t = result["t"]
    colors = {"S": "#377eb8", "E": "#ff7f00", "I": "#e41a1c", "R": "#4daf4a"}
    labels = {"S": "S(t)/N 易感", "E": "E(t)/N 暴露", "I": "I(t)/N 感染", "R": "R(t)/N 恢复"}

    fig, ax = plt.subplots(figsize=(10, 6))
    _style_axes(ax)
    for key in ("S", "E", "I", "R"):
        ax.plot(t, result[key] / model.N, color=colors[key], linewidth=2.2,
                label=labels[key], zorder=3)

    # S 下降到约 30% 的位置，作为图中群体免疫阶段的直观提示。
    s_ratio = result["S"] / model.N
    target_idx = int(abs(s_ratio - 0.30).argmin())
    target_t = t[target_idx]
    ax.axhline(0.30, color="#377eb8", linestyle=":", linewidth=1.0,
               alpha=0.8)
    ax.annotate("S 衰减到约 30%\n群体免疫阶段",
                xy=(target_t, s_ratio[target_idx]),
                xytext=(target_t + 18, 0.42), fontsize=9,
                color="#2d3748", ha="center",
                arrowprops=dict(arrowstyle="->", color="#377eb8",
                                linewidth=1.0), zorder=6)

    ax.set_xlim(0, 200)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("天数 (days)", fontsize=11, color="#2d3748")
    ax.set_ylabel("人数比例（各仓室 / N）", fontsize=11, color="#2d3748")
    ax.set_title("SEIR 4 仓室演化 (COVID-19 R0=3.0)", fontsize=15,
                 fontweight="bold", color="#1f2328", pad=12)
    ax.legend(loc="center right", fontsize=9, framealpha=0.96,
              edgecolor="#d0d7de")
    fig.text(0.5, 0.018,
             "S、E、I、R 四个仓室人数比例始终守恒，总和为 1。",
             ha="center", fontsize=9, color="#4a525e", style="italic")
    fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.13)
    _save(fig, "fig_env_16_4compartments.png")


def fig3_schematic():
    """绘制 SEIR 四仓室转移流程示意图。"""
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    ax.set_title("SEIR 4 仓室模型", fontsize=16, fontweight="bold",
                 color="#1f2328", pad=14)

    boxes = [
        ("S", "易感", "#377eb8", 0.7),
        ("E", "暴露\n潜伏期", "#ff7f00", 3.0),
        ("I", "感染\n有传染性", "#e41a1c", 5.3),
        ("R", "恢复\n免疫", "#4daf4a", 7.6),
    ]
    y, w, h = 1.85, 1.35, 1.05
    centers = []
    for letter, desc, color, x in boxes:
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08",
                               facecolor=color, edgecolor="white", linewidth=1.5,
                               alpha=0.92, zorder=3)
        ax.add_patch(patch)
        centers.append((x + w / 2, y + h / 2))
        ax.text(x + w / 2, y + h * 0.68, letter, ha="center", va="center",
                fontsize=22, fontweight="bold", color="white", zorder=4)
        ax.text(x + w / 2, y + h * 0.24, desc, ha="center", va="center",
                fontsize=9, color="white", zorder=4)

    transitions = [("β·S·I/N", 0), ("σ", 1), ("γ", 2)]
    for label, idx in transitions:
        x1 = centers[idx][0] + w / 2 - 0.03
        x2 = centers[idx + 1][0] - w / 2 + 0.03
        arrow = FancyArrowPatch((x1, centers[idx][1]), (x2, centers[idx + 1][1]),
                                arrowstyle="-|>", mutation_scale=16,
                                linewidth=1.7, color="#4b5563", zorder=2)
        ax.add_patch(arrow)
        ax.text((x1 + x2) / 2, centers[idx][1] + 0.27, label,
                ha="center", va="bottom", fontsize=10, color="#374151",
                fontweight="bold")

    ax.text(5.0, 0.78,
            "β = 传播率       σ = 1/潜伏期       γ = 1/感染期       R0 = β/γ",
            ha="center", va="center", fontsize=11, color="#2d3748",
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#f3f4f6",
                      edgecolor="#d1d5db"))
    ax.text(5.0, 4.22,
            "易感者接触感染者后进入暴露期，完成潜伏后具有传染性，最后恢复并获得免疫。",
            ha="center", va="center", fontsize=9.5, color="#4a525e")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.06)
    _save(fig, "fig_env_16_schematic.png")


if __name__ == "__main__":
    fig1_r0_curves()
    fig2_compartments()
    fig3_schematic()
    print("\n=== 3 figures generated ===")
