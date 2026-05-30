"""
Cleanup aftermath: where does the sediment Cd go?

Scenario: 南方小型河流（宽8m, 深0.6m, Q~1.9 m³/s）采矿废石影响后清理

Core question: after waste rock removal, the contaminated sediment in the riverbed
doesn't disappear — where does it go?

Three physical pathways (Fig 3 conceptual diagram):
  1. Vertical dilution — clean sediment from upstream covers the contaminated layer
  2. Downstream transport — flood events resuspend and carry Cd further downstream
  3. Deep burial — contaminated material is gradually buried below the active layer

River sediment recovery follows first-order active layer replacement:
  C(t) = C_bg + (C_0 - C_bg) * exp(-t / tau)
  tau = M_active / J_sed  (~10 yr for small river)

Farmland Cd is included as a short companion section (no natural recovery,
safe utilization needed for grain safety).

Three figures:
  Fig 1: River sediment Cd recovery curves (multiple distances + tau sensitivity)
  Fig 2: Farmland Cd and safe utilization effect
  Fig 3: Sediment profile concept diagram — the three destinations of Cd

Usage:
  python models/floodplain_recovery.py

Parameter source:
  [S]=standard, [L]=literature, [E]=estimated, [C]=calculated, [A]=assumed
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ====================================================================
# Global plot settings
# ====================================================================
plt.rcParams.update({
    'font.sans-serif': ['Microsoft YaHei', 'SimHei'],
    'axes.unicode_minus': False,
    'figure.dpi': 120,
})

# ====================================================================
# Constants
# ====================================================================
CD_BG = 0.15             # mg/kg, regional background S China [L]
SCREENING_VALUE = 0.3    # mg/kg, GB 15618-2018 pH<=5.5 [S]
GB_RICE_CD = 0.2         # mg/kg, GB 2762-2022 rice Cd limit [S]
FARM_CD_INITIAL = 0.55   # mg/kg, 50-yr floodplain accumulation from article 03 [C]

# Soil-to-grain transfer factors (Cd, rice)
TF_WITHOUT = 0.40        # no measures [L: typical 0.3-0.5 for acidic paddy]
TF_WITH = 0.18           # with safe utilization (lime+flooding+low-Cd variety) [L: 0.1-0.25]

# Output
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(OUT_DIR, exist_ok=True)


# ====================================================================
# Model A: River sediment recovery — first-order active layer replacement
# ====================================================================

def initial_river_profile(d_km):
    """Initial river sediment Cd (mg/kg) at distance d (km) from source.

    Small river profile (compressed vs the large-river model in article 01):
      - Peak at ~3 km due to faster settling in shallower water
      - Exponential decay after peak, L_decay ~12 km
      - Returns to near background by ~40 km
    """
    d_peak = 3.0        # km, peak location [E: small river, shallower = faster fining]
    c_peak = 4.5        # mg/kg, peak Cd [C: consistent with article 01 source strength]
    L_decay = 12.0      # km, decay length [E: ~1/3 of large river L_decay]

    if d_km <= d_peak:
        frac = d_km / d_peak
        return CD_BG + (c_peak - CD_BG) * frac
    else:
        return CD_BG + (c_peak - CD_BG) * np.exp(-(d_km - d_peak) / L_decay)


def river_cd(t_years, d_km, tau=10.0):
    """River sediment Cd after t years post-cleanup.

    First-order active layer replacement:
      C(t) = C_bg + (C_0 - C_bg) * exp(-t / tau)

    tau = M_active / J_sed  (active layer mass / sediment deposition flux)
    For small river with infrequent floods: tau ~10 yr [E]
    """
    c0 = initial_river_profile(d_km)
    return CD_BG + (c0 - CD_BG) * np.exp(-t_years / tau)


# ====================================================================
# Time constants
# ====================================================================
TAU_BASELINE = 10.0    # yr, baseline recovery time constant
TAU_FAST = 5.0         # yr, optimistic (frequent floods, fast replacement)
TAU_SLOW = 20.0        # yr, pessimistic (rare floods, slow replacement)


# ====================================================================
# Table output
# ====================================================================
def print_summary():
    """Print key parameters and results to console."""
    print("=" * 65)
    print("废石清理后底泥镉去向 — 参数与结果")
    print("=" * 65)

    print("\n── 河流底泥初始 Cd 沿程分布 (小河流) ──")
    print(f"{'距源(km)':>8} | {'Cd(mg/kg)':>8}")
    print("-" * 22)
    for d in [0, 1, 3, 5, 8, 15, 25, 40]:
        print(f"{d:>8} | {initial_river_profile(d):>8.2f}")

    print(f"\n── 底泥恢复 (τ={TAU_BASELINE} yr) ──")
    print(f"{'时间(年)':>8} | {'3 km':>8} | {'8 km':>8} | {'15 km':>8} | {'30 km':>8}")
    print("-" * 50)
    for yr in [0, 5, 10, 15, 20, 30, 50]:
        vals = [f"{river_cd(yr, d):>8.2f}" for d in [3, 8, 15, 30]]
        print(f"{yr:>8} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]}")

    print(f"\n── 农田 Cd (安全利用对比) ──")
    print(f"  土壤 Cd (总量, 恒定):    {FARM_CD_INITIAL:.2f} mg/kg")
    grain_without = FARM_CD_INITIAL * TF_WITHOUT
    grain_with = FARM_CD_INITIAL * TF_WITH
    without_label = "> 限量 (超标)" if grain_without > GB_RICE_CD else "< 限量 (达标)"
    with_label = "> 限量 (超标)" if grain_with > GB_RICE_CD else "< 限量 (达标)"
    print(f"  大米 Cd (无措施):   {grain_without:.2f} mg/kg [{without_label}]")
    print(f"  大米 Cd (安全利用): {grain_with:.2f} mg/kg [{with_label}]")
    print(f"  GB 2762-2022 大米 Cd 限量: {GB_RICE_CD:.1f} mg/kg [S]")
    print("=" * 65)


# ====================================================================
# Figure 1: River sediment recovery at multiple distances
# ====================================================================
def fig1_river_recovery():
    """图1: 废石清理后河流底泥 Cd 恢复曲线"""
    t = np.linspace(0, 50, 300)
    distances = [3, 8, 15, 30]
    colors = ['#DC143C', '#D2691E', '#6B8E23', '#4682B4']
    labels = ['3 km（峰值区）', '8 km', '15 km', '30 km']

    fig, ax = plt.subplots(figsize=(8, 5))

    # — Main recovery curves —
    for d, c, l in zip(distances, colors, labels):
        c_t = river_cd(t, d)
        ax.plot(t, c_t, color=c, lw=2, label=l)

    # — τ sensitivity band on peak curve (d=3 km) —
    c_fast = river_cd(t, distances[0], TAU_FAST)
    c_slow = river_cd(t, distances[0], TAU_SLOW)
    ax.fill_between(t, c_slow, c_fast, alpha=0.12, color=colors[0],
                    label=f'τ 敏感性 ({TAU_FAST}-{TAU_SLOW} yr)')

    # — Reference lines —
    ax.axhline(CD_BG, color='gray', ls='--', lw=1, alpha=0.6,
               label=f'区域背景 ({CD_BG} mg/kg)')
    ax.axhline(SCREENING_VALUE, color='red', ls=':', lw=1.5, alpha=0.7,
               label=f'土壤筛选值 ({SCREENING_VALUE} mg/kg) [GB 15618]')

    # — Annotations —
    ax.annotate('废石清理 (t=0)',
                xy=(0, initial_river_profile(distances[0])),
                xytext=(2, 4.8), fontsize=10, fontweight='bold', color='#333',
                arrowprops=dict(arrowstyle='->', color='#333', lw=1.2))

    ax.set_xlabel('时间 (年)', fontsize=11)
    ax.set_ylabel('底泥 Cd (mg/kg)', fontsize=11)
    ax.set_title('废石清理后河流底泥 Cd 自然恢复', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 50)
    ax.set_ylim(0, 5.5)
    ax.legend(fontsize=8, loc='upper right', framealpha=0.9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '05_river_recovery.png'), dpi=150)
    plt.close(fig)
    print('[Fig 1] 05_river_recovery.png')


# ====================================================================
# Figure 2: Farmland Cd + safe utilization
# ====================================================================
def fig2_farmland_safe_use():
    """图2: 农田 Cd 与安全利用效果"""
    t = np.linspace(0, 50, 200)

    fig, ax1 = plt.subplots(figsize=(8, 5))

    # — Left axis: soil Cd —
    soil_cd = np.full_like(t, FARM_CD_INITIAL)
    ax1.plot(t, soil_cd, color='#8B4513', lw=2.5, label='土壤 Cd（总量）')
    ax1.axhline(CD_BG, color='gray', ls='--', lw=1, alpha=0.5,
                label=f'区域背景 ({CD_BG} mg/kg)')
    ax1.set_xlabel('时间 (年)', fontsize=11)
    ax1.set_ylabel('土壤 Cd (mg/kg)', fontsize=11, color='#8B4513')
    ax1.tick_params(axis='y', labelcolor='#8B4513')
    ax1.set_ylim(0, 0.85)

    # — Right axis: grain Cd —
    ax2 = ax1.twinx()
    grain_without = np.full_like(t, FARM_CD_INITIAL * TF_WITHOUT)
    grain_with = np.full_like(t, FARM_CD_INITIAL * TF_WITH)

    ax2.plot(t, grain_without, color='#DC143C', lw=2, ls='--',
             label='大米 Cd — 无措施')
    ax2.plot(t, grain_with, color='#228B22', lw=2, ls='-.',
             label='大米 Cd — 安全利用')
    ax2.axhline(GB_RICE_CD, color='red', ls=':', lw=1.5, alpha=0.7,
                label=f'GB 限量 ({GB_RICE_CD} mg/kg)')

    ax2.set_ylabel('大米 Cd (mg/kg)', fontsize=11, color='#333')
    ax2.set_ylim(0, 0.40)

    # — Combined legend —
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center',
               fontsize=8, ncol=2, framealpha=0.9)

    ax1.set_title('附：农田土壤 Cd 与安全利用效果', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # — Annotations —
    ax1.annotate('土壤 Cd 总量不降\n（无自然恢复机制）',
                 xy=(35, FARM_CD_INITIAL), fontsize=9, color='#8B4513',
                 ha='center', va='bottom',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF8DC', alpha=0.8))
    ax2.annotate('安全利用阻断\n土壤→籽粒传递',
                 xy=(35, FARM_CD_INITIAL * TF_WITH),
                 fontsize=9, color='#228B22', ha='center', va='bottom',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#F0FFF0', alpha=0.8))

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '05_farmland_safe_use.png'), dpi=150)
    plt.close(fig)
    print('[Fig 2] 05_farmland_safe_use.png')


# ====================================================================
# Figure 3: Sediment profile — three destinations of Cd
# ====================================================================
def fig3_sediment_profile():
    """图3: 底泥镉去向概念图 — 沉积剖面示意

    展示河流横断面中三个去向：
      ① 垂直稀释 — 清洁泥沙覆盖
      ② 沿程搬运 — 洪水冲刷输移
      ③ 深层封存 — 埋入老沉积物
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 14)
    ax.set_ylim(-5, 3)
    ax.set_aspect('equal')

    # ==================== Water column ====================
    water = plt.Rectangle((0, 0), 10, 2.5, facecolor='#B0D4F1',
                          edgecolor='#4A86B8', alpha=0.35, zorder=1)
    ax.add_patch(water)
    ax.text(5, 1.2, '水流（清洁来沙）', fontsize=11, color='#1565C0',
            ha='center', va='center', alpha=0.8, fontweight='bold')

    # Flow arrow
    ax.annotate('', xy=(9, 1.8), xytext=(1, 1.8),
                arrowprops=dict(arrowstyle='->', color='#1565C0', lw=2.5))
    ax.text(5, 2.2, '来沙不含高浓度镉', fontsize=9, color='#1565C0',
            ha='center', va='center', alpha=0.7)

    # ==================== Layer 1: Clean new sediment ====================
    clean = plt.Rectangle((0, -0.6), 10, 0.6, facecolor='#D4A76A',
                          edgecolor='#8B7355', linewidth=1.2, alpha=0.8, zorder=2)
    ax.add_patch(clean)
    ax.text(5, -0.3, '① 清洁泥沙覆盖层（新沉积）', fontsize=10,
            color='#5D4037', ha='center', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF8DC', alpha=0.85))

    # ==================== Layer 2: Contaminated active layer ====================
    contam = plt.Rectangle((0, -1.8), 10, 1.2, facecolor='#CD5C5C',
                           edgecolor='#8B0000', linewidth=1.2, alpha=0.6, zorder=2)
    ax.add_patch(contam)
    ax.text(5, -1.2, '污染活性层（Cd ~4.5 mg/kg）', fontsize=10,
            color='#8B0000', ha='center', va='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#FFF0F0', alpha=0.85))

    # ==================== Layer 3: Background sediment ====================
    bg = plt.Rectangle((0, -4.5), 10, 2.7, facecolor='#C4A882',
                        edgecolor='#8B7355', linewidth=0.8, alpha=0.4, zorder=2)
    ax.add_patch(bg)
    ax.text(5, -3.2, '深层老沉积物（背景值 Cd ~0.15 mg/kg）', fontsize=10,
            color='#8B7355', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#F5F0E0', alpha=0.8))

    # ==================== Annotations for three destinations ====================

    # ① Vertical dilution: clean sand settling down
    ax.annotate('', xy=(2.0, -0.6), xytext=(2.0, 0),
                arrowprops=dict(arrowstyle='->', color='#2E7D32', lw=2))
    ax.text(2.0, -0.8, '① 垂直稀释', fontsize=9, color='#2E7D32',
            ha='center', va='top', fontweight='bold')
    ax.text(2.0, 0.15, '清洁泥沙逐年覆盖\n污染层被稀释', fontsize=7.5,
            color='#2E7D32', ha='center', va='bottom', alpha=0.7)

    # ② Downstream transport: scour and carry downstream (to the right)
    ax.annotate('', xy=(9.2, -1.0), xytext=(8.5, -1.5),
                arrowprops=dict(arrowstyle='->', color='#E65100', lw=2.5))
    ax.annotate('', xy=(9.5, -1.3), xytext=(9.0, -1.8),
                arrowprops=dict(arrowstyle='->', color='#E65100', lw=2.5))
    ax.text(9.5, -0.7, '② 沿程搬运', fontsize=9, color='#E65100',
            ha='center', va='bottom', fontweight='bold')
    ax.text(9.5, -0.3, '洪水再悬浮\n往下游输移', fontsize=7.5,
            color='#E65100', ha='center', va='bottom', alpha=0.7)

    # ③ Deep burial (downward)
    ax.annotate('', xy=(6.0, -3.5), xytext=(6.0, -1.8),
                arrowprops=dict(arrowstyle='->', color='#6A1B9A', lw=2))
    ax.text(6.0, -3.8, '③ 深层封存', fontsize=9, color='#6A1B9A',
            ha='center', va='top', fontweight='bold')
    ax.text(6.0, -4.1, '持续沉积埋入深层\n镉暂离生物接触层', fontsize=7.5,
            color='#6A1B9A', ha='center', va='top', alpha=0.7)

    # ==================== Labels on right ====================
    legend_text = (
        '底泥镉的三个去向\n'
        '━━━━━━━━━━━━━━\n'
        '① 垂直稀释：清洁泥沙覆盖\n'
        '   替代污染层（主驱动力）\n\n'
        '② 沿程搬运：洪水再悬浮\n'
        '   向下游输移\n\n'
        '③ 深层封存：持续沉积\n'
        '   埋入老沉积层'
    )
    ax.text(10.3, -0.5, legend_text, fontsize=8, color='#333',
            va='top', ha='left',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                      edgecolor='#ccc', alpha=0.9))

    # ==================== Cleanup ====================
    ax.axis('off')
    ax.set_title('底泥镉的三个去向：清洁泥沙覆盖 → 稀释 → 埋藏',
                 fontsize=13, fontweight='bold', pad=10)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '05_sediment_profile.png'), dpi=150)
    plt.close(fig)
    print('[Fig 3] 05_sediment_profile.png')


# ====================================================================
# Main
# ====================================================================
if __name__ == '__main__':
    print_summary()
    fig1_river_recovery()
    fig2_farmland_safe_use()
    fig3_sediment_profile()
    print(f'\nAll figures saved to {OUT_DIR}')
