"""
Atmospheric Cd deposition from a waste incineration plant
Gaussian plume dispersion + dry/wet deposition → soil accumulation

Scenario: 南方某城市 3000 t/d MSW incinerator, 80m stack, subtropical monsoon climate
Target: Cd accumulation in surrounding agricultural soil

NOTE: This is a SCREENING-LEVEL model. Parameters are based on typical ranges
from literature, not site-specific measurements. Designed for mechanism
understanding and semi-quantitative assessment, not formal EIA.

Theory:
  1. Gaussian plume dispersion (Briggs 1973, urban parameters)
     C(x,y,0) = Q/(2πuσyσz) * exp(-y²/2σy²) * 2*exp(-H²/2σz²)

  2. Dry deposition: F_dry = Vd * C_ground (PM2.5-bound Cd, Vd ~ 0.1-0.5 cm/s)

  3. Wet deposition:
     Scavenging coefficient approach for annual average:
     F_wet = Λ * C_column * (rain_fraction * seconds_per_year)

  4. Soil accumulation:
     ΔC_soil = F_total * t / (ρ_bulk * h_mix)
     GB 15618-2018: screening 0.3 mg/kg (pH≤5.5), 0.4 mg/kg (pH 5.5-6.5)

Standards referenced:
  - GB 18485-2014: Cd emission limit 0.1 mg/Nm³ (real)
  - GB 15618-2018: soil Cd risk screening/control values (real)

Parameter source key:
  [S] = standard/regulation · [L] = literature typical range · [E] = estimated
  [C] = calculated · [A] = assumed for screening model
  See each parameter comment for source type and basis.

Usage:
  python models/atmo_cd_deposition.py
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
SEC_PER_YEAR = 365.25 * 24 * 3600  # seconds in a year
UG_PER_G = 1e6                     # μg/g for unit conversion

# ====================================================================
# Source parameters (南方某城市 3000 t/d MSW incinerator)
# ====================================================================
STACK_H = 80       # m, physical stack height [A: typical for large incinerators]
PLUME_RISE = 30    # m, buoyant rise estimate, D stability [E: Briggs formula with
                    #    150°C exhaust, 2 m/s wind → ~50-150m range, conservative low end]
H_EFF = STACK_H + PLUME_RISE  # 110 m effective height [C]
FLUE_GAS_V = 150_000  # Nm³/h, typical for 3000 t/d plant [L: Wang et al. 2019,
                       #    Environ. Pollut. 252: 461-475]

# Emission scenario: modern APCD (SD+BF+CI)
# Cd after APCD: 0.002-0.05 mg/Nm³ in literature; choosing 0.03 as "well-operated" level
# GB 18485-2014 limit: 0.1 mg/Nm³ → 0.03 = 30% of limit [S]
CD_CONC_FLUE = 0.03  # mg/Nm³ [E: within L range, well below S limit]
Q_G_PER_H = CD_CONC_FLUE * FLUE_GAS_V / 1e3  # mg/Nm³ * Nm³/h → g/h [C]
Q = Q_G_PER_H / 3600   # g/s [C]

# ====================================================================
# Meteorological parameters (华南沿海亚热带季风气候)
# ====================================================================
U_AVG = 2.0        # m/s, annual mean wind speed [L: typical 1.5-2.5 m/s,
                    #    coastal S China cities, China Met. Yearbook]
RAIN_FRACTION = 0.08  # fraction of time with rain (~700 h/yr) [E: ~150 rain-days/yr,
                       #    avg ~4.5h/rain-day → ~675h/yr ≈ 8%]
RAIN_ANNUAL = 1800    # mm/yr, annual precipitation [L: typical for S China coastal cities,
                       #    used for reference context only; deposition calc uses RAIN_FRACTION]

# Stability distribution (annual average, 南方亚热带)
# Reference: estimates based on latitude + cloud cover typical of S China
# D (neutral) dominates at ~45%; A-B (unstable) in summer daytime ~23%;
# E-F (stable) winter nights ~20%; remainder C
STAB_FRACTIONS = {
    'A': 0.08,   # very unstable, summer daytime [E]
    'B': 0.15,   # moderately unstable [E]
    'C': 0.12,   # slightly unstable [E]
    'D': 0.45,   # neutral, most common, overcast/windy [E]
    'E': 0.12,   # slightly stable [E]
    'F': 0.08,   # stable, winter nights [E]
}

# ====================================================================
# Soil parameters (华南红壤)
# ====================================================================
SOIL_BG_CD = 0.15   # mg/kg, regional background Cd in topsoil
                     # [L: 0.08-0.25 mg/kg for S China red soil, CNEMC 1990]
SOIL_RHO = 1.3      # g/cm³, typical bulk density for cultivated red soil
                     # [L: 1.2-1.5 g/cm³, soil physics textbook values]
SOIL_H_MIX = 0.20   # m, plow layer (tillage depth) [A: typical 15-20 cm]
SOIL_MASS = SOIL_RHO * 1000 * SOIL_H_MIX  # kg/m² = 260 [C]
# 1.3 g/cm³ × 1000 = 1300 kg/m³ × 0.2 m = 260 kg/m²

# ====================================================================
# Deposition parameters
# ====================================================================
# Dry deposition velocity for PM2.5-bound Cd
# Literature range: 0.1-1.0 cm/s depending on surface and meteorology
# Cd is mostly submicron (< 1 μm) → lower end of range
VD_CD = 0.003      # m/s (0.3 cm/s) [L: Seinfeld & Pandis 2016, Zhang et al. 2001]

# Scavenging coefficient for wet deposition
# Λ = removal rate (s⁻¹) during rain — literature range 1e-5 to 1e-4
# Moderate rain ~3 mm/hr → Λ ≈ 3e-5 s⁻¹ for PM2.5
LAMBDA_SCAV = 3e-5  # s⁻¹ [L: Sportisse 2007, Brandt et al. 2002]


# ====================================================================
# Briggs (1973) urban dispersion coefficients
# ====================================================================
def sigma_y_urban(x, stab):
    """Briggs urban σy (m) as function of downwind distance x (m)."""
    if stab == 'A':
        return 0.32 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'B':
        return 0.32 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'C':
        return 0.22 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'D':
        return 0.16 * x / np.sqrt(1 + 0.0004 * x)
    else:  # E, F
        return 0.11 * x / np.sqrt(1 + 0.0004 * x)


def sigma_z_urban(x, stab):
    """Briggs urban σz (m) as function of downwind distance x (m)."""
    if stab == 'A':
        return 0.24 * x * np.sqrt(1 + 0.0001 * x)
    elif stab == 'B':
        return 0.24 * x * np.sqrt(1 + 0.0001 * x)
    elif stab == 'C':
        return 0.20 * x
    elif stab == 'D':
        return 0.14 * x / np.sqrt(1 + 0.0003 * x)
    elif stab == 'E':
        return 0.08 * x / (1 + 0.0015 * x) ** 0.5
    else:  # F
        return 0.08 * x / (1 + 0.0015 * x) ** 0.5


# ====================================================================
# Physical computation
# ====================================================================

def ground_concentration(x, y, Q, u, H, stab):
    """Ground-level concentration C(x,y,0) in g/m³.

    Full Gaussian plume with ground reflection.
    """
    sy = sigma_y_urban(x, stab)
    sz = sigma_z_urban(x, stab)

    # Avoid division by zero
    sy = np.maximum(sy, 1.0)
    sz = np.maximum(sz, 1.0)

    term1 = Q / (2 * np.pi * u * sy * sz)
    term2 = np.exp(-y**2 / (2 * sy**2))
    term3 = 2 * np.exp(-H**2 / (2 * sz**2))  # ground reflection (z=0)

    return term1 * term2 * term3


def column_integrated(x, y, Q, u, stab):
    """Vertically integrated concentration C_column (g/m²).

    ∫₀^∞ C(x,y,z) dz = Q / (√(2π) * u * σy) * exp(-y²/2σy²)
    Independent of σz and stack height H.
    """
    sy = sigma_y_urban(x, stab)
    sy = np.maximum(sy, 1.0)
    return Q / (np.sqrt(2 * np.pi) * u * sy) * np.exp(-y**2 / (2 * sy**2))


def dry_flux(C_ground, Vd, seconds):
    """Dry deposition flux (g/m² over given seconds)."""
    return C_ground * Vd * seconds


def wet_flux(C_column, Lambda, sec_with_rain):
    """Wet deposition flux (g/m² over rainy seconds).

    Uses scavenging coefficient approach.
    """
    return C_column * Lambda * sec_with_rain


def soil_increment(F_total_g_m2, years):
    """Soil Cd increment (mg/kg) from cumulative deposition."""
    μg_per_m2 = F_total_g_m2 * UG_PER_G  # convert g/m² → μg/m²
    return μg_per_m2 * years / SOIL_MASS / 1e3  # μg/m²·yr × yr ÷ kg/m² ÷ 1000 = mg/kg


# ====================================================================
# Annual average (weighted by stability class)
# ====================================================================

def annual_avg_deposition(x, y, Q, u, H):
    """Annual average total deposition (g/m²/yr) weighted by stability.

    Returns (F_total, F_dry, F_wet, C_ground_avg)
    """
    sec_total = SEC_PER_YEAR
    sec_rain = SEC_PER_YEAR * RAIN_FRACTION

    F_dry_annual = 0.0
    F_wet_annual = 0.0
    Cg_annual = 0.0

    for stab, frac in STAB_FRACTIONS.items():
        Cg = ground_concentration(x, y, Q, u, H, stab)
        Ccol = column_integrated(x, y, Q, u, stab)

        Fd = dry_flux(Cg, VD_CD, sec_total)
        Fw = wet_flux(Ccol, LAMBDA_SCAV, sec_rain)

        F_dry_annual += Fd * frac
        F_wet_annual += Fw * frac
        Cg_annual += Cg * frac

    return F_dry_annual + F_wet_annual, F_dry_annual, F_wet_annual, Cg_annual


# ====================================================================
# Scenarios
# ====================================================================

SCENARIOS = {
    # Baseline: modern APCD meeting GB 18485-2014 — SD+BF+CI
    # Cd emission ~4.5 g/h (within typical L range of 1-10 g/h)
    'standard': {
        'label': '现行标准 (SD+BF)',
        'Q_factor': 1.0,
        'color': '#2E86AB',
    },
    # WFGD (wet flue gas desulfurization) adds ~80% additional removal
    # for particulate-bound metals as a co-benefit of SO₂ removal
    # [L: 50-90% co-removal reported in literature]
    'high_standard': {
        'label': '高标准 (SD+BF+WFGD)',
        'Q_factor': 0.2,    # ~80% extra removal → 0.9 g/h [E: optimistic]
        'color': '#36B37E',
    },
}


# ====================================================================
# Output directory
# ====================================================================
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(OUT_DIR, exist_ok=True)


# ====================================================================
# Figure 1: Vertical plume cross-section  (烟羽扩散截面)
# ====================================================================
def fig_plume_cross_section():
    """Vertical slice along plume centerline. Concentration contours."""
    print("[Fig 1] 烟羽扩散截面...")

    x_vals = np.linspace(100, 5000, 200)
    z_vals = np.linspace(0, 200, 100)
    X, Z = np.meshgrid(x_vals, z_vals)

    stab = 'D'  # neutral, most common
    sy = sigma_y_urban(X, stab)
    sz = sigma_z_urban(X, stab)

    C_3d = (Q / (2 * np.pi * U_AVG * sy * sz)
            * (np.exp(-(Z - H_EFF)**2 / (2 * sz**2))
               + np.exp(-(Z + H_EFF)**2 / (2 * sz**2))))

    C_3d = np.maximum(C_3d, 1e-15)

    # Ground concentration profile
    C_ground_x = ground_concentration(x_vals, 0, Q, U_AVG, H_EFF, stab)

    fig, (ax_contour, ax_profile) = plt.subplots(
        2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [3, 1]},
        sharex=True)

    # Contour
    levels = np.logspace(np.log10(C_3d.max() / 100), np.log10(C_3d.max()), 10)
    cf = ax_contour.contourf(X / 1000, Z, C_3d, levels=levels, cmap='YlOrRd',
                             extend='both')
    ax_contour.plot([0, 5], [STACK_H, STACK_H], 'k-', linewidth=2)
    ax_contour.annotate(f'烟囱 {STACK_H}m', xy=(0, STACK_H),
                        xytext=(0.3, STACK_H + 20),
                        arrowprops=dict(arrowstyle='->'), fontsize=9)
    ax_contour.axhline(H_EFF, color='gray', linestyle='--', linewidth=1)
    ax_contour.text(4.8, H_EFF + 5, f'有效源高 {H_EFF}m', fontsize=8, color='gray')
    ax_contour.set_ylabel('高度 (m)')
    ax_contour.set_ylim(0, 200)

    # Profile
    ax_profile.plot(x_vals / 1000, C_ground_x * 1e9, 'b-', linewidth=1.5)
    ax_profile.fill_between(x_vals / 1000, C_ground_x * 1e9, alpha=0.3)
    ax_profile.set_xlabel('下风向距离 (km)')
    ax_profile.set_ylabel('C地面 (ng/m³)')
    ax_profile.set_xlim(0, 5)

    # Colorbar
    cbar = plt.colorbar(cf, ax=ax_contour, orientation='horizontal',
                        pad=0.02, shrink=0.8, label='浓度 (g/m³, log scale)')

    fig.suptitle('烟羽扩散截面 (D类稳定度)', fontsize=13, y=1.01)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, '02_plume_cross_section.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


# ====================================================================
# Figure 2: Deposition spatial distribution (沉降通量空间分布)
# ====================================================================
def fig_deposition_contour():
    """Plan view of annual Cd deposition with dominant wind direction."""
    print("[Fig 2] 沉降通量空间分布...")

    # Grid: downwind 0-10 km, crosswind ±3 km
    x_vals = np.linspace(100, 10000, 200)
    y_vals = np.linspace(-3000, 3000, 200)
    X, Y = np.meshgrid(x_vals, y_vals)

    # Vectorized computation per stability class
    F_total_ann = np.zeros_like(X)
    for stab, frac in STAB_FRACTIONS.items():
        sy = sigma_y_urban(X, stab)
        sy = np.maximum(sy, 1.0)
        sz = sigma_z_urban(X, stab)
        sz = np.maximum(sz, 1.0)

        # Ground concentration
        Cg = (Q / (2 * np.pi * U_AVG * sy * sz)
              * np.exp(-Y**2 / (2 * sy**2))
              * 2 * np.exp(-H_EFF**2 / (2 * sz**2)))

        # Column integrated
        Ccol = (Q / (np.sqrt(2 * np.pi) * U_AVG * sy)
                * np.exp(-Y**2 / (2 * sy**2)))

        # Annual fluxes
        sec_rain = SEC_PER_YEAR * RAIN_FRACTION
        Fd = Cg * VD_CD * SEC_PER_YEAR
        Fw = Ccol * LAMBDA_SCAV * sec_rain
        F_total_ann += (Fd + Fw) * frac

    F_total_ann *= 1e4  # g/m²/yr → g/ha/yr (1 ha = 10,000 m²)

    fig, ax = plt.subplots(figsize=(10, 7))

    levels = np.logspace(np.log10(max(F_total_ann.min(), 1)),
                         np.log10(F_total_ann.max()), 12)
    cf = ax.contourf(X / 1000, Y / 1000, F_total_ann, levels=levels,
                     cmap='RdYlBu_r', extend='both')

    # Source marker
    ax.plot(0, 0, 'v', color='k', markersize=12, zorder=5)
    ax.annotate('烟囱', xy=(0, 0), xytext=(0.15, 0.3), fontsize=10,
                arrowprops=dict(arrowstyle='->'))

    # Wind direction arrow
    ax.annotate('', xy=(2.5, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(1.2, 0.15, '主导风向 →', fontsize=9, color='gray')

    # Distance rings
    for r in [2, 5]:
        circle = plt.Circle((0, 0), r, fill=False, color='gray',
                            linestyle=':', linewidth=0.8, alpha=0.5)
        ax.add_patch(circle)
        ax.text(r, 0.1, f'{r}km', fontsize=8, color='gray')

    ax.set_xlabel('下风向距离 (km)')
    ax.set_ylabel('侧风向距离 (km)')
    ax.set_xlim(0, 10)
    ax.set_ylim(-3, 3)
    ax.set_aspect('equal')

    cbar = plt.colorbar(cf, ax=ax, shrink=0.8, label='Cd沉降通量 (g/ha/yr)')
    fig.suptitle('全年总Cd沉降通量空间分布', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, '02_deposition_contour.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


# ====================================================================
# Figure 3: Soil Cd accumulation over time (土壤Cd时间演化)
# ====================================================================
def fig_soil_accumulation():
    """Soil Cd concentration vs time at several downwind distances."""
    print("[Fig 3] 土壤Cd累积曲线...")

    distances = [1_000, 3_000, 5_000]  # m downwind
    years = np.arange(0, 51, 1)

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ['#E5534B', '#2E86AB', '#36B37E']
    labels = ['1 km', '3 km', '5 km']

    for dist, color, label in zip(distances, colors, labels):
        F_ann, Fd, Fw, Cg = annual_avg_deposition(dist, 0, Q, U_AVG, H_EFF)
        C_soil = SOIL_BG_CD + soil_increment(F_ann, years)
        after_30 = C_soil[years == 30][0]
        after_50 = C_soil[years == 50][0]
        ax.plot(years, C_soil, color=color, linewidth=2, label=label)
        # Mark endpoint
        ax.plot(50, after_50, 'o', color=color, markersize=5)
        ax.text(50.5, after_50, f'{after_50:.3f}', fontsize=8, color=color, va='center')
        print(f"  {label}: 30yr={after_30:.3f} mg/kg, 50yr={after_50:.3f} mg/kg")

    # GB 15618-2018 screening value (pH≤5.5, most relevant for acidic S China soil)
    ax.axhline(0.3, color='orange', linestyle='--', linewidth=1.2, alpha=0.8)
    ax.text(51.5, 0.3, '筛选值 0.3 (pH≤5.5)', fontsize=9, color='orange', va='center')

    ax.axhline(SOIL_BG_CD, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.text(51.5, SOIL_BG_CD, f'背景 {SOIL_BG_CD}', fontsize=8, color='gray', va='center')

    ax.set_xlabel('运行时间 (年)')
    ax.set_ylabel('土壤Cd (mg/kg)')
    ax.set_xlim(0, 56)
    ax.set_ylim(0.10, 0.42)
    ax.legend(title='下风向距离', fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle('不同距离处土壤Cd累积曲线', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, '02_soil_accumulation.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


def print_accumulation_table(distances):
    """Print soil Cd accumulation table."""
    print("\n[Soil Cd accumulation]")
    header = f"{'Dist':>8} {'5yr':>8} {'10yr':>8} {'20yr':>8} {'30yr':>8}"
    print(header)
    print("-" * 40)
    for dist in distances:
        F_ann, _, _, _ = annual_avg_deposition(dist, 0, Q, U_AVG, H_EFF)
        row = [f'{dist//1000:.0f} km']
        for yr in [5, 10, 20, 30]:
            C = SOIL_BG_CD + soil_increment(F_ann, yr)
            row.append(f'{C:.3f}')
        print(f"{row[0]:>8} {' '.join(f'{v:>8}' for v in row[1:])}")


# ====================================================================
# Figure 4: Scenario comparison (情景对比)
# ====================================================================
def fig_scenario_comparison(dist_peak):
    """Compare soil Cd across scenarios at peak deposition location."""
    print("[Fig 4] 情景对比...")

    years = np.array([10, 20, 30])
    n_scenarios = len(SCENARIOS)
    n_years = len(years)

    fig, ax = plt.subplots(figsize=(9, 6))

    width = 0.25
    x_pos = np.arange(n_years)

    for i, (key, sc) in enumerate(SCENARIOS.items()):
        Q_sc = Q * sc['Q_factor']
        F_ann, _, _, _ = annual_avg_deposition(dist_peak, 0, Q_sc, U_AVG, H_EFF)
        values = [SOIL_BG_CD + soil_increment(F_ann, yr) for yr in years]

        offset = (i - (n_scenarios - 1) / 2) * width
        bars = ax.bar(x_pos + offset, values, width, label=sc['label'],
                      color=sc['color'], alpha=0.85, edgecolor='white', linewidth=0.5)

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.008,
                    f'{val:.3f}', ha='center', fontsize=9, fontweight='bold')

    # GB reference line
    ax.axhline(0.3, color='orange', linestyle='--', linewidth=1, alpha=0.7,
               label='筛选值 0.3 (pH≤5.5)')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'{y}年' for y in years])
    ax.set_xlabel('运行时间')
    ax.set_ylabel('土壤Cd (mg/kg)')
    ax.set_ylim(0.10, 0.38)
    ax.legend(fontsize=9, loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')

    fig.suptitle(f'不同排放标准情景对比 (下风向{dist_peak//1000:.0f}km)', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, '02_scenario_comparison.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")


def print_scenario_table(dist_peak):
    """Print scenario comparison table."""
    print(f"\n[Scenario comparison @ {dist_peak/1000:.1f} km]")
    header = f"{'Scenario':>20} {'Emit(g/h)':>12} {'10yr(mg/kg)':>14} {'30yr(mg/kg)':>14} {'>0.3?':>10}"
    print(header)
    print("-" * 70)
    for key, sc in SCENARIOS.items():
        Q_sc = Q * sc['Q_factor']
        Q_gh = Q_sc * 3600
        F_ann, _, _, _ = annual_avg_deposition(dist_peak, 0, Q_sc, U_AVG, H_EFF)
        c10 = SOIL_BG_CD + soil_increment(F_ann, 10)
        c30 = SOIL_BG_CD + soil_increment(F_ann, 30)
        exceed = 'YES' if c30 > 0.3 else 'no'
        print(f"{sc['label']:>20} {Q_gh:>8.2f} {c10:>14.3f} {c30:>14.3f} {exceed:>10}")


# ====================================================================
# Figure 5: Stack height comparison (烟囱高度对比)
# ====================================================================
HEIGHT_SCENARIOS = [
    {'label': '矮烟囱 60m', 'H_stack': 60,  'rise': 20, 'color': '#E5534B'},
    {'label': '基准 80m',   'H_stack': 80,  'rise': 30, 'color': '#2E86AB'},
    {'label': '高烟囱 120m', 'H_stack': 120, 'rise': 40, 'color': '#36B37E'},
]


def fig_stack_height_comparison():
    """Compare deposition flux profiles for different stack heights."""
    print("[Fig 5] 烟囱高度对比...")

    # Start at 2x max stack height to avoid plume-not-yet-landed artifact
    x_vals = np.linspace(250, 10000, 150)

    fig, (ax_flux, ax_soil) = plt.subplots(1, 2, figsize=(12, 5))

    for sc in HEIGHT_SCENARIOS:
        H_eff = sc['H_stack'] + sc['rise']
        F_profile = np.array([annual_avg_deposition(x, 0, Q, U_AVG, H_eff)[0]
                              for x in x_vals])

        # Left: deposition flux vs distance
        ax_flux.plot(x_vals / 1000, F_profile * 1e4, color=sc['color'],
                     linewidth=2, label=sc['label'])
        idx_max = np.argmax(F_profile)
        ax_flux.plot(x_vals[idx_max] / 1000, F_profile[idx_max] * 1e4, 'o',
                     color=sc['color'], markersize=6)
        ax_flux.text(x_vals[idx_max] / 1000 + 0.2, F_profile[idx_max] * 1e4,
                     f'{x_vals[idx_max]:.0f}m', fontsize=8, color=sc['color'])

        # Right: soil Cd after 30yr
        C_30 = SOIL_BG_CD + soil_increment(F_profile, 30)
        ax_soil.plot(x_vals / 1000, C_30, color=sc['color'],
                     linewidth=2, label=sc['label'])

    # Reference line on right
    ax_soil.axhline(0.3, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    ax_soil.text(10.2, 0.3, '筛选值 0.3', fontsize=8, color='orange', va='center')

    ax_flux.set_xlabel('下风向距离 (km)')
    ax_flux.set_ylabel('Cd沉降通量 (g/ha/yr)')
    ax_flux.set_xlim(0, 10)
    ax_flux.legend(fontsize=8)
    ax_flux.grid(True, alpha=0.3)

    ax_soil.set_xlabel('下风向距离 (km)')
    ax_soil.set_ylabel('30年土壤Cd (mg/kg)')
    ax_soil.set_xlim(0, 10)
    ax_soil.legend(fontsize=8)
    ax_soil.grid(True, alpha=0.3)

    fig.suptitle('不同烟囱高度对Cd沉降和土壤累积的影响', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, '02_stack_height.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  → {path}")

    # Print comparison table
    print("\n[Stack height comparison]")
    header = f"{'Height':>10} {'PeakPos':>10} {'PeakFlux':>12} {'30yr@1km':>10} {'30yr@Peak':>10}"
    print(header)
    print("-" * 52)
    for sc in HEIGHT_SCENARIOS:
        H_eff = sc['H_stack'] + sc['rise']
        F_profile = np.array([annual_avg_deposition(x, 0, Q, U_AVG, H_eff)[0]
                              for x in x_vals])
        idx_max = np.argmax(F_profile)
        peak_x_val = x_vals[idx_max]
        peak_F = F_profile[idx_max]
        F_at_1k = annual_avg_deposition(1000, 0, Q, U_AVG, H_eff)[0]
        c_1k = SOIL_BG_CD + soil_increment(F_at_1k, 30)
        c_peak = SOIL_BG_CD + soil_increment(peak_F, 30)
        label = f"{sc['H_stack']}m"
        print(f"{label:>10} {peak_x_val:>7.0f}m {peak_F*1e4:>10.2f} g/ha/yr"
              f" {c_1k:>8.3f} {c_peak:>8.3f} mg/kg")


# ====================================================================
# Main
# ====================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("Atmo Cd Deposition Model - 南方某城市焚烧厂")
    print("Screening-level model. See parameter comments for source types.")
    print("=" * 60)
    print(f"\nEmission:")
    print(f"  Cd in flue gas: {CD_CONC_FLUE:.2f} mg/Nm3")
    print(f"  Flue gas volume: {FLUE_GAS_V:,} Nm3/h")
    print(f"  Emission rate: {Q * 3600:.2f} g/h = {Q * 3600 * 1e3:.0f} ug/h")
    print(f"  Effective stack height: {H_EFF} m ({STACK_H} + {PLUME_RISE})")
    print(f"\nMeteorology (南方某城市):")
    print(f"  Wind speed: {U_AVG} m/s")
    print(f"  Rainfall: {RAIN_ANNUAL} mm/yr")
    print(f"  Rain fraction: {RAIN_FRACTION*100:.0f}%")
    print(f"\nSoil:")
    print(f"  Background Cd: {SOIL_BG_CD} mg/kg")
    print(f"  Bulk density: {SOIL_RHO} g/cm3")
    print(f"  Mixing depth: {SOIL_H_MIX} m -> {SOIL_MASS:.0f} kg/m2")

    # Find peak deposition location
    x_test = np.arange(200, 10000, 50)
    F_test = np.array([annual_avg_deposition(x, 0, Q, U_AVG, H_EFF)[0]
                       for x in x_test])
    peak_idx = np.argmax(F_test)
    peak_x = x_test[peak_idx]
    peak_F = F_test[peak_idx]
    print(f"\nPeak deposition:")
    print(f"  Location: {peak_x:.0f} m downwind")
    print(f"  Flux: {peak_F * 1e4:.2f} g/ha/yr")

    # Print peak point details
    F_ann, Fd, Fw, Cg = annual_avg_deposition(peak_x, 0, Q, U_AVG, H_EFF)
    print(f"  Annual avg C_ground: {Cg * 1e9:.2f} ng/m3")
    print(f"  Dry deposition: {Fd * 1e4:.2f} g/ha/yr ({Fd/F_ann*100:.0f}%)")
    print(f"  Wet deposition: {Fw * 1e4:.2f} g/ha/yr ({Fw/F_ann*100:.0f}%)")

    print(f"\nPeak soil Cd (background + increment):")
    for yr in [10, 20, 30, 50]:
        C = SOIL_BG_CD + soil_increment(F_ann, yr)
        status = "EXCEED screening" if C > 0.3 else ("EXCEED control" if C > 1.5 else "OK")
        print(f"  {yr:>2d}yr: {C:.3f} mg/kg  {status}")

    print(f"\nSoil Cd by distance:")
    print_accumulation_table([1000, 3000, 5000, 10000])

    print(f"\nScenario comparison (peak {peak_x:.0f}m):")
    print_scenario_table(peak_x)

    # Generate figures
    print("\n" + "=" * 60)
    print("Generating figures...")
    print("=" * 60)
    fig_plume_cross_section()
    fig_deposition_contour()
    fig_soil_accumulation()
    fig_scenario_comparison(peak_x)
    fig_stack_height_comparison()

    print("\nDone!")
