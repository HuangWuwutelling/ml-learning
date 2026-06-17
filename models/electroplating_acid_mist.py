"""
Electroplating factory acid mist — process emission to atmospheric deposition
Gaussian plume dispersion + dry/wet deposition → soil acidification risk

Scenario: 南方某镀铬厂, 2m² 镀槽, 15m 排气筒, 亚热带季风气候
Target: 酸雾（铬酸雾/硫酸雾/氯化氢）扩散、沉降及土壤酸化风险评估

NOTE: This is a SCREENING-LEVEL model. Parameters based on GB/HJ standards
and literature typical ranges, not site-specific measurements.

Theory (6-step mass balance chain):
  1. Emission generation: D = G_s * A   (HJ 984-2018 产污系数法)
  2. Canopy collection: η_coll = 90%
  3. Wet scrubbing: η_scrub (≥90-95% per pollutant, HJ 984-2018 附录F)
  4. Stack emission: Q_stack = D * η_coll * (1 - η_scrub)
  5. Gaussian plume: C(x,y,0) = Q/(2πuσyσz) * exp(-y²/2σy²) * 2*exp(-H²/2σz²)
  6. Dry/wet deposition + H⁺ equivalent → soil acidification ratio

Standards referenced:
  - GB 21900-2008: 电镀污染物排放标准 (emission limits, base air volume)
  - HJ 984-2018: 污染源源强核算技术指南 电镀 (emission factors, treatment efficiency)

Parameter source key:
  [S] = standard/regulation · [L] = literature typical range · [E] = estimated
  [C] = calculated
  See each parameter comment for source type and basis.

Usage:
  python models/electroplating_acid_mist.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
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
SEC_PER_YEAR = 365.25 * 24 * 3600  # seconds in a year

# ====================================================================
# Step 1-3: Emission source calculation (产污 → 集气 → 洗涤)
# ====================================================================

# ---- Factory scenario ----
TANK_AREA = 2.0        # m², 镀槽液面面积 [A: 典型镀铬槽]
PLATING_HOURS = 16      # h/day, 日运行时间 [A: 两班制]
WORK_DAYS = 300         # days/yr, 年工作日 [A]

# ---- Step 1: Emission factors (产污系数 from HJ 984-2018 附录B 表B.1) ----
# 铬酸雾: 0.38 g/m²·h, 添加铬雾抑制剂的镀铬槽 [S]
# 硫酸雾: 25.2 g/m²·h, 硫酸浓度 > 100g/L 的浸蚀/抛光 [S]
# 氯化氢: 220 g/m²·h, 中等盐酸(16-20%), 不加热 [S, 取中值]
EMISSION_FACTORS = {
    'chromic_acid': {'factor': 0.38,   'unit': 'g/m2.h', 'name': 'ChromicAcid', 'Mw': 52.0},
    'sulfuric_acid': {'factor': 25.2,  'unit': 'g/m2.h', 'name': 'SulfuricAcid', 'Mw': 98.08},
    'hcl':           {'factor': 220,   'unit': 'g/m2.h', 'name': 'HCl',         'Mw': 36.46},
}

# ---- Step 2: Collection efficiency ----
COLL_EFF = 0.90  # 槽边抽风集气效率 [E: 90% by design spec]

# ---- Step 3: Scrubber efficiency (洗涤塔去除效率 from HJ 984-2018 附录F 表F.1) ----
# 铬酸雾喷淋塔回收率 ≥95% [S]
# 硫酸雾碱液喷淋中和去除率 ≥90% [S]
# 氯化氢碱液喷淋去除率 ≥95% [S]
SCRUB_EFF = {
    'chromic_acid': 0.95,
    'sulfuric_acid': 0.90,
    'hcl': 0.95,
}

# ---- Stack parameters ----
STACK_H = 15          # m, 排气筒物理高度 [S: GB 21900-2008 §4.2.5, ≥15m]
PLUME_RISE = 5        # m, 烟气抬升 [E: Briggs公式, 低速排气取保守值]
H_EFF = STACK_H + PLUME_RISE  # 20m, 有效源高 [C]

# GB 21900-2008 表6: 镀铬基准排气量 74.4 m³/m² [S]
BASE_EXHAUST_VOLUME = 74.4  # m³/m² (per unit plating area)
EXHAUST_VOLUME = BASE_EXHAUST_VOLUME * TANK_AREA  # 148.8 m³/h [C]


def calc_emission_rates():
    """Calculate stack emission rates (g/s) for each pollutant.

    6-step chain: Steps 1-3
    Returns dict of {key: {'Q_g_s': g/s, 'Q_g_h': g/h, 'conc_mg_m3': mg/m³}}
    """
    results = {}
    print(f"{'Pollutant':>15} {'Generate':>10} {'Collected':>10} {'Emitted':>10} {'Conc':>10} {'Limit':>10} {'Status'}")
    print("-" * 80)

    for key, info in EMISSION_FACTORS.items():
        # Step 1: 产污
        D_gh = info['factor'] * TANK_AREA  # g/h

        # Step 2: 集气
        D_collected_gh = D_gh * COLL_EFF  # g/h

        # Step 3: 洗涤
        eff = SCRUB_EFF[key]
        Q_gh = D_collected_gh * (1 - eff)  # g/h
        Q_gs = Q_gh / 3600  # g/s

        # Emission concentration check
        conc_mg_m3 = Q_gh / EXHAUST_VOLUME * 1000  # g/h ÷ m³/h × 1000 = mg/m³

        # GB 21900-2008 表5 新建企业限值
        limits = {
            'chromic_acid': 0.05,
            'sulfuric_acid': 30,
            'hcl': 30,
        }
        limit = limits[key]
        status = 'Exceed!' if conc_mg_m3 > limit else 'Pass'

        results[key] = {
            'Q_g_s': Q_gs,
            'Q_g_h': Q_gh,
            'conc_mg_m3': conc_mg_m3,
            'limit': limit,
            'status': status,
            'name': info['name'],
        }

        print(f"{info['name']:>15} {D_gh:>8.4f} g/h {D_collected_gh:>8.4f} g/h {Q_gh:>8.4f} g/h "
              f"{conc_mg_m3:>8.4f} {limit:>8.2f} mg/m3 {status:>6}")

    return results


# ====================================================================
# Step 4: Gaussian plume dispersion (Briggs 1973, urban parameters)
# ====================================================================

# ---- Meteorological parameters ----
U_AVG = 3.0          # m/s, 年均风速 [E: typical coastal S China]
RAIN_FRACTION = 0.08  # 降雨时间比例 [L: ~700 h/yr ≈ 8%]

# ---- Stability distribution (南方亚热带, annual avg) ----
STAB_FRACTIONS = {
    'A': 0.08,
    'B': 0.15,
    'C': 0.12,
    'D': 0.45,
    'E': 0.12,
    'F': 0.08,
}


def sigma_y_urban(x, stab):
    """Briggs urban σy (m) as function of downwind distance x (m)."""
    if stab in ('A', 'B'):
        return 0.32 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'C':
        return 0.22 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'D':
        return 0.16 * x / np.sqrt(1 + 0.0004 * x)
    else:  # E, F
        return 0.11 * x / np.sqrt(1 + 0.0004 * x)


def sigma_z_urban(x, stab):
    """Briggs urban σz (m) as function of downwind distance x (m)."""
    if stab in ('A', 'B'):
        return 0.24 * x * np.sqrt(1 + 0.0001 * x)
    elif stab == 'C':
        return 0.20 * x
    elif stab == 'D':
        return 0.14 * x / np.sqrt(1 + 0.0003 * x)
    else:  # E, F
        return 0.08 * x / (1 + 0.0015 * x) ** 0.5


def ground_concentration(x, y, Q, u, H, stab):
    """Ground-level concentration C(x,y,0) in g/m³.

    Full Gaussian plume with ground reflection.
    """
    sy = sigma_y_urban(x, stab)
    sz = sigma_z_urban(x, stab)
    sy = np.maximum(sy, 1.0)
    sz = np.maximum(sz, 1.0)

    term1 = Q / (2 * np.pi * u * sy * sz)
    term2 = np.exp(-y**2 / (2 * sy**2))
    term3 = 2 * np.exp(-H**2 / (2 * sz**2))
    return term1 * term2 * term3


def column_integrated(x, y, Q, u, stab):
    """Vertically integrated concentration C_column (g/m²)."""
    sy = sigma_y_urban(x, stab)
    sy = np.maximum(sy, 1.0)
    return Q / (np.sqrt(2 * np.pi) * u * sy) * np.exp(-y**2 / (2 * sy**2))


# ====================================================================
# Step 5: Deposition (干湿沉降)
# ====================================================================

# ---- Dry deposition velocities ----
VD_CHROMIC = 0.003    # m/s (0.3 cm/s), 铬酸雾气溶胶 [L]
VD_SULFURIC = 0.010   # m/s (1.0 cm/s), 硫酸雾气溶胶 (larger droplets) [L]
VD_HCL = 0.005        # m/s (0.5 cm/s), HCl gas [L]

VD_VALUES = {
    'chromic_acid': VD_CHROMIC,
    'sulfuric_acid': VD_SULFURIC,
    'hcl': VD_HCL,
}

# Scavenging coefficient for wet deposition
LAMBDA_SCAV = 3e-5    # s⁻¹ [L: Sportisse 2007, moderate rain]


def calc_deposition(pollutant_key, Q_gs, x, y, u, H):
    """Annual average total deposition (g/m²/yr) for a single pollutant.

    Returns (F_total, F_dry, F_wet, Cg_annual_avg)
    """
    vd = VD_VALUES[pollutant_key]
    sec_total = SEC_PER_YEAR
    sec_rain = SEC_PER_YEAR * RAIN_FRACTION

    F_dry = 0.0
    F_wet = 0.0
    Cg_avg = 0.0

    for stab, frac in STAB_FRACTIONS.items():
        Cg = ground_concentration(x, y, Q_gs, u, H, stab)
        Ccol = column_integrated(x, y, Q_gs, u, stab)

        Fd = Cg * vd * sec_total
        Fw = Ccol * LAMBDA_SCAV * sec_rain

        F_dry += Fd * frac
        F_wet += Fw * frac
        Cg_avg += Cg * frac

    return F_dry + F_wet, F_dry, F_wet, Cg_avg


# ====================================================================
# Step 6: Soil acidification (H⁺ equivalent)
# ====================================================================

# H⁺ equivalent per gram of each pollutant (mol H⁺/g)
# H₂SO₄ → 2H⁺: 2 mol / 98.08 g/mol = 0.0204 mol H⁺/g
# HCl → 1H⁺: 1 mol / 36.46 g/mol = 0.0274 mol H⁺/g
# H₂CrO₄ (chromic acid) → 2H⁺: 2 mol / 118.0 g/mol = 0.0169 mol H⁺/g
HPLUS_PER_GRAM = {
    'chromic_acid': 0.0169,   # mol H⁺/g as H₂CrO₄ [C]
    'sulfuric_acid': 0.0204,  # mol H⁺/g [C]
    'hcl': 0.0274,            # mol H⁺/g [C]
}

# Soil acid buffering capacity (mol H⁺/ha·yr)
# [L: 中国土壤酸沉降临界负荷, 见 Hao et al. 2001, Environ. Pollut.]
SOIL_BUFFER = {
    'red_soil':     {'name': 'RedSoil_SC',   'capacity': 750,   'color': '#E5534B'},
    'yellow_brown': {'name': 'YellowBrown_CC', 'capacity': 1500,  'color': '#2E86AB'},
    'cinnamon':     {'name': 'Cinnamon_NC',   'capacity': 3500,  'color': '#36B37E'},
}


def hplus_deposition(F_total_g_m2, pollutant_key):
    """Convert total deposition mass to H⁺ equivalent (mol/ha·yr)."""
    mol_h_per_g = HPLUS_PER_GRAM[pollutant_key]
    # g/m² → g/ha: * 10,000
    # g/ha → mol H⁺/ha: * mol_h_per_g
    return F_total_g_m2 * 10000 * mol_h_per_g


def acidification_risk(hplus_total, buffer_capacity):
    """Calculate acidification risk ratio R = H⁺ deposition / buffer capacity."""
    return hplus_total / buffer_capacity


def risk_category(R):
    """Categorize acidification risk."""
    if R < 0.5:
        return 'Safe', '#36B37E'
    elif R < 1.0:
        return 'Caution', '#FFA726'
    else:
        return 'High Risk', '#E5534B'


# ====================================================================
# Output directory
# ====================================================================
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(OUT_DIR, exist_ok=True)


# ====================================================================
# Figure 1: Process flow diagram (工艺流程图 - text-based)
# ====================================================================
def fig_process_flow():
    """Schematic diagram of the 6-step mass balance chain."""
    print("[Fig 1] Process flow diagram...")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')

    steps = [
        ('镀槽产污', '0.38~220\ng/m²·h\n[HJ 984-2018]', '#FF6B6B'),
        ('槽边集气\nη=90%', '收集效率\n90%', '#FFA94D'),
        ('碱液洗涤塔\nη≥90~95%', '去除效率\n≥90~95%\n[HJ 984-2018]', '#4ECDC4'),
        ('烟囱排放\nH=15m', '排气量\n148.8 m³/h\n[GB 21900]', '#45B7D1'),
        ('高斯烟羽扩散', 'σy, σz\nBriggs参数', '#6C5CE7'),
        ('干湿沉降\n->土壤酸化', '风险比 R\nH+沉积/\n缓冲容量', '#A66CFF'),
    ]

    x_positions = np.linspace(0.05, 0.95, len(steps))
    y_box = 0.55
    y_label = 0.18

    for i, (title, detail, color) in enumerate(steps):
        # Box
        rect = FancyBboxPatch((x_positions[i] - 0.07, y_box - 0.12),
                                  0.14, 0.24, boxstyle="round,pad=0.02",
                                  facecolor=color, alpha=0.3,
                                  edgecolor=color, linewidth=2, zorder=3)
        ax.add_patch(rect)
        ax.text(x_positions[i], y_box + 0.04, title, ha='center', va='center',
                fontsize=9, fontweight='bold', color=color)
        ax.text(x_positions[i], y_box - 0.10, detail, ha='center', va='center',
                fontsize=7, color='#444444')

        # Arrow
        if i < len(steps) - 1:
            ax.annotate('', xy=(x_positions[i+1] - 0.07, y_box),
                        xytext=(x_positions[i] + 0.07, y_box),
                        arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

    # Step numbers
    for i in range(len(steps)):
        ax.text(x_positions[i], y_box - 0.22, f'步骤 {i+1}', ha='center',
                fontsize=8, color='gray')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 0.85)
    ax.set_title('电镀厂酸雾质量平衡模型 — 六步链条', fontsize=13, fontweight='bold', pad=10)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_acid_mist_flow.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


# ====================================================================
# Figure 2: Ground concentration vs downwind distance (地面浓度曲线)
# ====================================================================
def fig_ground_conc_profile(emission_data):
    """Ground concentration profiles for each pollutant vs distance."""
    print("[Fig 2] Ground concentration profile...")

    x_vals = np.linspace(100, 5000, 100)
    stab = 'D'

    fig, ax = plt.subplots(figsize=(10, 5.5))

    colors = {'chromic_acid': '#E5534B', 'sulfuric_acid': '#2E86AB', 'hcl': '#36B37E'}
    labels = {'chromic_acid': '铬酸雾 (Cr6+)', 'sulfuric_acid': '硫酸雾 (H2SO4)', 'hcl': '氯化氢 (HCl)'}

    for key in emission_data:
        Q_val = emission_data[key]['Q_g_s']
        Cg = np.array([ground_concentration(x, 0, Q_val, U_AVG, H_EFF, stab)
                       for x in x_vals])
        ax.plot(x_vals / 1000, Cg * 1e6,  # convert g/m³ → μg/m³
                color=colors[key], linewidth=2, label=labels[key])

        # Mark peak location
        idx_max = np.argmax(Cg)
        ax.plot(x_vals[idx_max] / 1000, Cg[idx_max] * 1e6, 'o',
                color=colors[key], markersize=6)
        ax.text(x_vals[idx_max] / 1000 + 0.15, Cg[idx_max] * 1e6,
                f'{x_vals[idx_max]:.0f}m\n{Cg[idx_max]*1e6:.4f} μg/m³',
                fontsize=7.5, color=colors[key], va='center')

    # WHO Cr(VI) reference: unit risk 0.012 per μg/m³
    # Concentration for 1×10⁻⁶ risk = 1e-6 / 0.012 = 8.33e-5 μg/m³
    who_ref = 1e-6 / 0.012  # μg/m³
    ax.axhline(who_ref, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.text(5000/1000 * 1.02, who_ref,
            f'WHO Cr(VI) 参考\n{who_ref:.1e} ug/m3\n(1E-6 风险)',
            fontsize=7, color='gray', va='bottom')

    ax.set_xlabel('下风向距离 (km)')
    ax.set_ylabel('地面浓度 (μg/m³)')
    ax.set_xlim(0, 5.5)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle('烟羽中心线地面浓度随距离变化 (D类稳定度)', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_acid_mist_conc_profile.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


# ====================================================================
# Figure 3: Heatmap of chromic acid mist ground concentration (铬酸雾热力图)
# ====================================================================
def fig_conc_heatmap(emission_data):
    """Ground concentration heatmap for chromic acid mist."""
    print("[Fig 3] Chromic acid concentration heatmap...")

    x_vals = np.linspace(100, 5000, 150)
    y_vals = np.linspace(-500, 500, 100)
    X, Y = np.meshgrid(x_vals, y_vals)

    Q_ca = emission_data['chromic_acid']['Q_g_s']

    # Weighted average across stability classes
    C_total = np.zeros_like(X)
    for stab, frac in STAB_FRACTIONS.items():
        sy = sigma_y_urban(X, stab)
        sy = np.maximum(sy, 1.0)
        sz = sigma_z_urban(X, stab)
        sz = np.maximum(sz, 1.0)

        C_stab = (Q_ca / (2 * np.pi * U_AVG * sy * sz)
                  * np.exp(-Y**2 / (2 * sy**2))
                  * 2 * np.exp(-H_EFF**2 / (2 * sz**2)))
        C_total += C_stab * frac

    C_total = np.maximum(C_total, 1e-15)

    fig, ax = plt.subplots(figsize=(10, 6))
    # Convert to μg/m³ for plotting
    C_ug = C_total * 1e6
    levels = np.logspace(np.log10(C_ug.max() / 1000),
                         np.log10(C_ug.max()), 15)

    cf = ax.contourf(X / 1000, Y / 1000, C_ug,
                     levels=levels, cmap='YlOrRd', extend='both')

    ax.plot(0, 0, 'v', color='k', markersize=12, zorder=5)
    ax.annotate('烟囱 (15m)', xy=(0, 0), xytext=(0.2, 0.15),
                arrowprops=dict(arrowstyle='->'), fontsize=9)

    ax.annotate('', xy=(2, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(0.8, 0.05, '主导风向 →', fontsize=9, color='gray')

    # Distance markers
    for r in [1, 3]:
        circle = plt.Circle((0, 0), r, fill=False, color='gray',
                            linestyle=':', linewidth=0.8, alpha=0.5)
        ax.add_patch(circle)
        ax.text(r, 0.05, f'{r}km', fontsize=8, color='gray')

    ax.set_xlabel('下风向距离 (km)')
    ax.set_ylabel('侧风向距离 (km)')
    ax.set_xlim(0, 5)
    ax.set_ylim(-0.5, 0.5)
    ax.set_aspect('equal')

    cbar = plt.colorbar(cf, ax=ax, shrink=0.8, label='铬酸雾地面浓度 (μg/m³)')
    fig.suptitle('铬酸雾地面浓度空间分布 (年均)', fontsize=13)

    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_acid_mist_heatmap.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


# ====================================================================
# Figure 4: Deposition flux profiles (各污染物沉降通量对比)
# ====================================================================
def fig_deposition_profile(emission_data):
    """Deposition flux profiles (total, dry, wet) for each pollutant."""
    print("[Fig 4] Deposition flux comparison...")

    x_vals = np.linspace(100, 5000, 100)

    fig, (ax_dep, ax_hplus) = plt.subplots(1, 2, figsize=(12, 5))

    colors = {'chromic_acid': '#E5534B', 'sulfuric_acid': '#2E86AB', 'hcl': '#36B37E'}

    # Left: total deposition flux
    for key in emission_data:
        Q_val = emission_data[key]['Q_g_s']
        F_total = np.array([calc_deposition(key, Q_val, x, 0, U_AVG, H_EFF)[0]
                           for x in x_vals])
        ax_dep.plot(x_vals / 1000, F_total * 1e4,  # g/m²·yr → g/ha·yr
                    color=colors[key], linewidth=2,
                    label=emission_data[key]['name'])

    ax_dep.set_xlabel('下风向距离 (km)')
    ax_dep.set_ylabel('总沉降通量 (g/ha·yr)')
    ax_dep.set_xlim(0, 5)
    ax_dep.legend(fontsize=9)
    ax_dep.grid(True, alpha=0.3)

    # Right: H⁺ equivalent deposition
    for key in emission_data:
        Q_val = emission_data[key]['Q_g_s']
        F_total = np.array([calc_deposition(key, Q_val, x, 0, U_AVG, H_EFF)[0]
                           for x in x_vals])
        hplus = hplus_deposition(F_total, key)
        ax_hplus.plot(x_vals / 1000, hplus, color=colors[key], linewidth=2,
                      label=emission_data[key]['name'])

    # Buffer capacity reference lines
    for soil_key, soil_info in SOIL_BUFFER.items():
        ax_hplus.axhline(soil_info['capacity'], color=soil_info['color'],
                         linestyle='--', linewidth=1, alpha=0.5)
        ax_hplus.text(5.2, soil_info['capacity'] * 1.05,
                      soil_info['name'], fontsize=7.5, color=soil_info['color'])

    ax_hplus.set_xlabel('下风向距离 (km)')
    ax_hplus.set_ylabel('H+ 沉降当量 (mol/ha.yr)')
    ax_hplus.set_xlim(0, 5)
    ax_hplus.legend(fontsize=9)
    ax_hplus.grid(True, alpha=0.3)

    fig.suptitle('各污染物沉降通量与 H+ 当量', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_acid_mist_deposition.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


# ====================================================================
# Figure 5: Soil acidification risk (土壤酸化风险)
# ====================================================================
def fig_acidification_risk(emission_data):
    """Soil acidification risk vs distance for different soil types."""
    print("[Fig 5] Soil acidification risk...")

    x_vals = np.linspace(100, 5000, 100)

    # Total H⁺ deposition from all pollutants combined
    hplus_total = np.zeros_like(x_vals)
    for key in emission_data:
        Q_val = emission_data[key]['Q_g_s']
        F_total = np.array([calc_deposition(key, Q_val, x, 0, U_AVG, H_EFF)[0]
                           for x in x_vals])
        hplus_total += hplus_deposition(F_total, key)

    fig, ax = plt.subplots(figsize=(10, 6))

    for soil_key, soil_info in SOIL_BUFFER.items():
        R = acidification_risk(hplus_total, soil_info['capacity'])
        R = np.maximum(R, 0)  # clip negative
        ax.plot(x_vals / 1000, R, color=soil_info['color'], linewidth=2,
                label=soil_info['name'])

    # All R values are well below 0.5 (max ~0.04), so zoom to data range
    # and note the threshold by annotation
    ax.annotate('潜在风险阈值 R=0.5（远高于本图范围）',
                xy=(4.5, 0.065), fontsize=8, color='#FFA726', alpha=0.5,
                ha='right', fontweight='bold')

    ax.set_xlabel('下风向距离 (km)')
    ax.set_ylabel('酸化风险比 R = H+沉积 / 缓冲容量')
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 0.08)
    ax.legend(fontsize=9, title='土壤类型')
    ax.grid(True, alpha=0.3)

    fig.suptitle('不同土壤类型的酸化风险评估', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_acid_mist_risk.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")

    # Print risk table
    print("\n[Acidification risk at key distances]")
    print(f"{'Distance':>10} {'Soil Type':>15} {'H+ dep':>12} {'Buffer':>10} {'R':>8} {'Category':>12}")
    print("-" * 70)
    for dist in [500, 1000, 2000, 3000]:
        hplus_at_dist = 0
        for key in emission_data:
            Q_val = emission_data[key]['Q_g_s']
            F = calc_deposition(key, Q_val, dist, 0, U_AVG, H_EFF)[0]
            hplus_at_dist += hplus_deposition(F, key)

        for soil_key, soil_info in SOIL_BUFFER.items():
            R = acidification_risk(hplus_at_dist, soil_info['capacity'])
            R = max(R, 0)
            cat, _ = risk_category(R)
            print(f"{dist:>7.0f}m {soil_info['name']:>15} {hplus_at_dist:>10.1f} "
                  f"{soil_info['capacity']:>8} {R:>7.2f} {cat:>12}")


# ====================================================================
# Main
# ====================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("Electroplating Acid Mist Model")
    print("Screening-level model. See parameter comments for source types.")
    print("=" * 70)

    # Steps 1-3: Calculate emission rates
    print(f"\n[Steps 1-3] Source calculation (Tank area: {TANK_AREA} m2)")
    print(f"  Exhaust volume: {EXHAUST_VOLUME:.1f} m3/h (GB 21900 Tab6: {BASE_EXHAUST_VOLUME} m3/m2)")
    print(f"  Collection efficiency: {COLL_EFF*100:.0f}%")
    print(f"  Stack height: {STACK_H}m + plume rise {PLUME_RISE}m = {H_EFF}m effective\n")

    emission_data = calc_emission_rates()

    # Step 4-5: Dispersion & deposition summary
    print(f"\n[Steps 4-5] Dispersion & deposition")
    print(f"  Wind speed: {U_AVG} m/s")
    print(f"  Rain fraction: {RAIN_FRACTION*100:.0f}%")

    # Find peak deposition location for key pollutant
    x_test = np.arange(200, 5000, 50)
    Q_ca = emission_data['chromic_acid']['Q_g_s']
    F_test = np.array([calc_deposition('chromic_acid', Q_ca, x, 0, U_AVG, H_EFF)[0]
                       for x in x_test])
    peak_idx = np.argmax(F_test)
    peak_x = x_test[peak_idx]
    print(f"\n  Peak deposition (chromic acid): {peak_x:.0f}m downwind")

    # Print deposition breakdown at peak
    F_ann, Fd, Fw, Cg = calc_deposition('chromic_acid', Q_ca, peak_x, 0, U_AVG, H_EFF)
    print(f"  Annual avg C_ground: {Cg*1e6:.6f} ug/m3")
    print(f"  Total deposition: {F_ann*1e4:.4f} g/ha/yr")
    print(f"    Dry: {Fd*1e4:.4f} g/ha/yr ({Fd/F_ann*100:.0f}%)")
    print(f"    Wet: {Fw*1e4:.4f} g/ha/yr ({Fw/F_ann*100:.0f}%)")

    # Step 6: Acidification risk summary at peak
    print(f"\n[Step 6] Soil acidification risk (@{peak_x:.0f}m)")
    hplus_peak = 0
    for key in emission_data:
        Q_val = emission_data[key]['Q_g_s']
        F, _, _, _ = calc_deposition(key, Q_val, peak_x, 0, U_AVG, H_EFF)
        hplus = hplus_deposition(F, key)
        hplus_peak += hplus
        print(f"  {emission_data[key]['name']}: {F*1e4:.4f} g/ha/yr -> {hplus:.1f} mol H+/ha.yr")

    for soil_key, soil_info in SOIL_BUFFER.items():
        R = acidification_risk(hplus_peak, soil_info['capacity'])
        cat, _ = risk_category(R)
        print(f"  {soil_info['name']}: R={R:.2f} -> {cat}")

    # Generate figures
    print("\n" + "=" * 70)
    print("Generating figures...")
    print("=" * 70)
    fig_process_flow()
    fig_ground_conc_profile(emission_data)
    fig_conc_heatmap(emission_data)
    fig_deposition_profile(emission_data)
    fig_acidification_risk(emission_data)

    print("\nDone!")
