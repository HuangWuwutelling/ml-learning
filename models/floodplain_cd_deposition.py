"""
Floodplain Cd deposition from river sediment during flood events
Gaussian-type lateral deposition model with size-selective settling

Scenario: same river as river_sediment_cd.py, 南方某河流
Target: Cd accumulation in floodplain farmland from flood events

Key processes:
  1. Floodwater spreads across floodplain, velocity decays with distance
  2. Suspended sediment settles by size fraction (coarse first, fine later)
  3. Cd adsorbed to fine particles → concentration increases with distance
  4. Multi-event accumulation over decades

Three flood scenarios:
  - Frequent  (2-5 yr): small inundation, low SSC
  - Design   (10-20 yr): moderate inundation, moderate SSC
  - Extreme  (50+ yr):  large inundation, high SSC

Theory:
  v(x) = v0 * exp(-x / L_v)                # velocity decay
  sed_dep(x) = S_max * exp(-x / L_s)        # sediment deposition (kg/m²)
  cd_sed(x) = C_bg + (C_max - C_bg) * (1 - exp(-x / L_c))  # Cd in deposited sed

Usage:
  python models/floodplain_cd_deposition.py

Parameter source key:
  [S] = standard/regulation · [L] = literature typical range · [E] = estimated
  [C] = calculated · [A] = assumed for screening model
  See each parameter comment for source type and basis.
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
SOIL_BG_CD = 0.15       # mg/kg, regional background for S China red soil [L: CNEMC 1990]
SOIL_RHO = 1.3          # g/cm³, typical bulk density for cultivated soil [L: 1.2-1.5, soil physics]
SOIL_H_MIX = 0.20       # m, plow layer depth [A: typical 15-20 cm for farmland]
SOIL_MASS = SOIL_RHO * 1000 * SOIL_H_MIX  # kg/m² = 260 [C]
SCREENING_VALUE = 0.3    # mg/kg, GB 15618-2018 pH≤5.5 [S]

# ====================================================================
# Output directory
# ====================================================================
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(OUT_DIR, exist_ok=True)


# ====================================================================
# Flood scenario definitions
# ====================================================================
FLOOD_SCENARIOS = {
    'frequent': dict(
        label='经常洪水 (2-5年一遇)',
        inundation=300,      # m, max inundation width [E: typical bankfull width × 3-5]
        S_max=3.0,           # kg/m², max sediment deposition near channel (~2.3 mm) [E]
        L_s=80,              # m, sediment decay length [E: rapid decay for small flood]
        C_max=5.0,           # mg/kg, max Cd in finest sediment [L: river_sediment_cd.py peak ~4.8]
        L_c=120,             # m, Cd content length scale [E]
        n_50yr=15,           # expected occurrences in 50 years [E: ~1 per 3-4 years]
        color='#2E86AB',     # blue
        hatch='',
    ),
    'design': dict(
        label='设计洪水 (10-20年一遇)',
        inundation=600,      # m [E: typical 1% floodplain width for small-medium river]
        S_max=8.0,           # kg/m² (~6.2 mm) [E]
        L_s=150,             # m [E]
        C_max=6.5,           # mg/kg [L: higher than bed sediment due to fine resuspension]
        L_c=200,             # m [E]
        n_50yr=4,            # expected occurrences in 50 years [E: ~1 per 12-15 years]
        color='#A23B72',     # purple
        hatch='///',
    ),
    'extreme': dict(
        label='稀遇洪水 (50年+)',
        inundation=1000,     # m [E: extreme floodplain extent]
        S_max=15.0,          # kg/m² (~11.5 mm) [E]
        L_s=250,             # m [E: slower decay = sediment carried further]
        C_max=8.0,           # mg/kg [L: fine sediment Cd approaching max enrichment]
        L_c=300,             # m [E]
        n_50yr=1,            # expected occurrences in 50 years [E: ~50 year return period]
        color='#F18F01',     # orange
        hatch='...',
    ),
}


# ====================================================================
# Core computation functions
# ====================================================================
def sed_deposition(x, scenario):
    """Sediment deposition at distance x from channel (kg/m² per event)."""
    p = FLOOD_SCENARIOS[scenario]
    if x > p['inundation']:
        return 0.0
    return p['S_max'] * np.exp(-x / p['L_s'])


def cd_in_sediment(x, scenario):
    """Cd concentration in deposited sediment (mg/kg).
    Beyond inundation zone, returns background (no new deposit)."""
    p = FLOOD_SCENARIOS[scenario]
    if x > p['inundation']:
        return SOIL_BG_CD
    return SOIL_BG_CD + (p['C_max'] - SOIL_BG_CD) * (1 - np.exp(-x / p['L_c']))


def cd_deposition(x, scenario):
    """Cd deposited per event (g/ha)."""
    sed = sed_deposition(x, scenario)
    cd_sed = cd_in_sediment(x, scenario)
    cd_mg_m2 = sed * cd_sed  # mg/m²
    return cd_mg_m2 * 10     # mg/m² → g/ha


def soil_increment(x, scenario, n_events):
    """Soil Cd increase after n flood events (mg/kg)."""
    cd_per_event_mg_m2 = cd_deposition(x, scenario) / 10  # g/ha → mg/m²
    cd_total_mg_m2 = cd_per_event_mg_m2 * n_events
    return cd_total_mg_m2 / SOIL_MASS


# ====================================================================
# Figure 1: Cd deposition profile for each scenario (single event)
# ====================================================================
def fig1_deposition_profile():
    """截图1: 不同洪水情景下单次 Cd 沉积通量横向分布."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.linspace(0, 1100, 500)

    for name, p in FLOOD_SCENARIOS.items():
        cd = np.array([cd_deposition(xi, name) for xi in x])
        ax.plot(x, cd, label=p['label'], color=p['color'], lw=2)

    ax.axvline(0, color='gray', ls=':', lw=1, label='河岸')
    ax.set_xlabel('距河距离 (m)')
    ax.set_ylabel('Cd 沉积通量 (g/ha/event)')
    ax.set_title('不同洪水情景下单次 Cd 沉积通量横向分布')
    ax.legend()
    ax.set_xlim(0, 1050)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '03_flood_cd_profile.png'), dpi=150)
    plt.close(fig)
    print('[Fig 1] Saved: 03_flood_cd_profile.png')


# ====================================================================
# Figure 2: Cd concentration in deposited sediment (along floodplain)
# ====================================================================
def fig2_sediment_cd():
    """截图2: 沉积物 Cd 含量沿距河距离的变化."""
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.linspace(0, 1100, 500)

    for name, p in FLOOD_SCENARIOS.items():
        cd_sed = np.array([cd_in_sediment(xi, name) for xi in x])
        ax.plot(x, cd_sed, label=p['label'], color=p['color'], lw=2)

    ax.axhline(SOIL_BG_CD, color='gray', ls='--', lw=1, alpha=0.5, label=f'背景值 ({SOIL_BG_CD} mg/kg)')
    ax.axvline(0, color='gray', ls=':', lw=1)
    ax.set_xlabel('距河距离 (m)')
    ax.set_ylabel('沉积物 Cd 含量 (mg/kg)')
    ax.set_title('沉积物 Cd 含量沿距河距离变化')
    ax.legend()
    ax.set_xlim(0, 1050)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '03_sediment_cd_profile.png'), dpi=150)
    plt.close(fig)
    print('[Fig 2] Saved: 03_sediment_cd_profile.png')


# ====================================================================
# Figure 3: 50-year cumulative soil Cd
# ====================================================================
def fig3_accumulation_50yr():
    """截图3: 50 年累积土壤 Cd 横向分布."""
    fig, ax = plt.subplots(figsize=(8, 5))

    # Compute combined accumulation
    x = np.linspace(0, 1100, 500)
    cd_total = np.zeros_like(x)
    cd_by_scenario = {}

    for name, p in FLOOD_SCENARIOS.items():
        cd_contrib = np.array([soil_increment(xi, name, p['n_50yr']) for xi in x])
        cd_by_scenario[name] = cd_contrib
        cd_total += cd_contrib

    # Stacked area
    ax.stackplot(x, [cd_by_scenario[s] for s in FLOOD_SCENARIOS],
                 labels=[p['label'] for p in FLOOD_SCENARIOS.values()],
                 colors=[p['color'] for p in FLOOD_SCENARIOS.values()],
                 alpha=0.7)

    # Total line
    ax.plot(x, cd_total + SOIL_BG_CD, color='black', lw=1.5, label='土壤 Cd 总量')

    # Reference lines
    ax.axhline(SOIL_BG_CD, color='gray', ls='--', lw=1, alpha=0.5,
               label=f'区域背景 ({SOIL_BG_CD} mg/kg)')
    ax.axhline(SCREENING_VALUE, color='red', ls='--', lw=2,
               label=f'筛选值 ({SCREENING_VALUE} mg/kg)')

    ax.axvline(0, color='gray', ls=':', lw=1)
    ax.set_xlabel('距河距离 (m)')
    ax.set_ylabel('土壤 Cd (mg/kg)')
    ax.set_title('50 年洪水累积后土壤 Cd 横向分布')
    ax.legend(loc='upper right', fontsize=9)
    ax.set_xlim(0, 1050)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '03_accumulation_50yr.png'), dpi=150)
    plt.close(fig)
    print('[Fig 3] Saved: 03_accumulation_50yr.png')


# ====================================================================
# Figure 4: Comparison with atmospheric deposition pathway
# ====================================================================
def fig4_pathway_comparison():
    """截图4: 洪水 vs 大气 Cd 输入路径对比."""
    fig, ax = plt.subplots(figsize=(7, 5))

    # Atmospheric deposition (from article 02: 9.64 g/ha/yr peak)
    # 50-year cumulative at peak point (450m from incinerator)
    atm_yearly = 9.64  # g/ha/yr
    atm_50yr = atm_yearly * 50  # g/ha
    atm_soil = atm_50yr / 10 / SOIL_MASS + SOIL_BG_CD  # mg/kg
    # = 9.64 * 50 / 10 / 260 + 0.15 = 482 / 260 + 0.15 = 1.85 + 0.15 = 0.335

    # Flood Cd at the most impacted distance (peak of combined scenarios)
    x = np.linspace(0, 1100, 500)
    cd_total_by_x = np.zeros_like(x)
    for name, p in FLOOD_SCENARIOS.items():
        for i, xi in enumerate(x):
            cd_total_by_x[i] += soil_increment(xi, name, p['n_50yr'])
    peak_idx = np.argmax(cd_total_by_x)
    peak_x = x[peak_idx]
    flood_peak_soil = cd_total_by_x[peak_idx] + SOIL_BG_CD

    # Bar chart
    categories = ['大气沉降\n(50年, 峰值点)', '洪水漫滩\n(50年, 峰值点)']
    values = [atm_soil, flood_peak_soil]
    colors = ['#5DADE2', '#A23B72']

    bars = ax.bar(categories, values, color=colors, width=0.5, edgecolor='black', lw=0.5)
    ax.axhline(SCREENING_VALUE, color='red', ls='--', lw=2, label=f'筛选值 ({SCREENING_VALUE} mg/kg)')
    ax.axhline(SOIL_BG_CD, color='gray', ls='--', lw=1, alpha=0.5, label=f'背景值 ({SOIL_BG_CD} mg/kg)')

    # Value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f'{val:.3f} mg/kg', ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('土壤 Cd (mg/kg)')
    ax.set_title('50 年后两种 Cd 输入路径贡献对比')
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(values) * 1.25)
    ax.grid(True, alpha=0.3, axis='y')

    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, '03_pathway_comparison.png'), dpi=150)
    plt.close(fig)
    print('[Fig 4] Saved: 03_pathway_comparison.png')
    print(f'\n  Atmospheric peak soil Cd (50yr): {atm_soil:.3f} mg/kg')
    print(f'  Flood peak soil Cd (50yr):       {flood_peak_soil:.3f} mg/kg at {peak_x:.0f} m')



# ====================================================================
# Print results table
# ====================================================================
def print_results():
    """Print key results to console."""
    print("=" * 70)
    print("洪水底泥镉农田输入模型 — 结果汇总")
    print("=" * 70)

    print("\n--- 单次事件 Cd 沉积通量 (g/ha/event) ---")
    print(f"{'距河距离':>8} | {'经常洪水':>10} | {'设计洪水':>10} | {'稀遇洪水':>10}")
    print("-" * 50)
    for d in [0, 50, 100, 150, 200, 300, 500]:
        vals = []
        for name in FLOOD_SCENARIOS:
            if d <= FLOOD_SCENARIOS[name]['inundation']:
                vals.append(f"{cd_deposition(d, name):>8.1f}")
            else:
                vals.append(f"{'—':>8}")
        print(f"{d:>8} | {vals[0]:>10} | {vals[1]:>10} | {vals[2]:>10}")

    print("\n--- 50 年累积 — 土壤 Cd 增量 (mg/kg) ---")
    print(f"{'距河距离':>8} | {'经常洪水':>10} | {'设计洪水':>10} | {'稀遇洪水':>10} | {'总量':>8} | {'+背景':>8}")
    print("-" * 65)
    for d in [0, 50, 100, 150, 200, 300, 500]:
        total_inc = 0
        parts = []
        for name, p in FLOOD_SCENARIOS.items():
            if d <= p['inundation']:
                inc = soil_increment(d, name, p['n_50yr'])
                parts.append(inc)
                total_inc += inc
            else:
                parts.append(0)
        cd_with_bg = total_inc + SOIL_BG_CD
        flag = ' *' if cd_with_bg > SCREENING_VALUE else ''
        print(f"{d:>8} | {parts[0]:>8.3f}  | {parts[1]:>8.3f}  | {parts[2]:>8.3f}  | {total_inc:>6.3f} | {cd_with_bg:>6.3f}{flag}")

    print("\n--- 大气沉降路径对比 (50年峰值点) ---")
    atm_yearly = 9.64  # g/ha/yr (from atmo_cd_deposition.py peak)
    atm_50yr_soil = atm_yearly * 50 / 10 / SOIL_MASS  # mg/kg increment
    print(f"  大气沉降 Cd 土壤增量: {atm_50yr_soil:.3f} mg/kg")
    x = np.linspace(0, 1100, 500)
    cd_total_by_x = np.zeros_like(x)
    for name, p in FLOOD_SCENARIOS.items():
        for i, xi in enumerate(x):
            cd_total_by_x[i] += soil_increment(xi, name, p['n_50yr'])
    peak_idx = np.argmax(cd_total_by_x)
    print(f"  洪水 Cd 土壤增量 (峰值): {cd_total_by_x[peak_idx]:.3f} mg/kg @ {x[peak_idx]:.0f} m")
    print("=" * 70)


# ====================================================================
# Main
# ====================================================================
if __name__ == '__main__':
    print_results()
    fig1_deposition_profile()
    fig2_sediment_cd()
    fig3_accumulation_50yr()
    fig4_pathway_comparison()
    print('\nAll figures saved to', OUT_DIR)
