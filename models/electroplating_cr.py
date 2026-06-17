"""
Electroplating Cr(VI) — atmospheric deposition, soil accumulation & health risk
Gaussian plume dispersion + dry/wet deposition → soil Cr(VI) accumulation → cancer risk

Scenario: 南方某镀铬厂, same factory as acid mist article (07)
Target: Cr(VI) dispersion, soil accumulation and health risk assessment

NOTE: This is a SCREENING-LEVEL model. Parameters based on GB/HJ standards
and literature typical ranges, not site-specific measurements.

Theory (6-step chain):
  1-3. Same emission chain as acid mist model (HJ 984-2018)
  4.   Gaussian plume dispersion for chromic acid mist
  5.   Dry/wet deposition of Cr(VI) to ground
  6.   Soil Cr accumulation + inhalation/ingestion cancer risk

Standards referenced:
  - GB 21900-2008: 电镀污染物排放标准
  - HJ 984-2018: 污染源源强核算技术指南 电镀
  - GB 15618-2018: 土壤环境质量标准 (Cr VI screening value: 3.0 mg/kg)
  - US EPA IRIS: Cr(VI) inhalation unit risk

Parameter source key:
  [S] = standard/regulation · [L] = literature typical range · [E] = estimated
  [C] = calculated

Usage:
  python models/electroplating_cr.py
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
SEC_PER_YEAR = 365.25 * 24 * 3600

# ====================================================================
# Steps 1-3: Emission (same factory, same method as acid mist model)
# ====================================================================

TANK_AREA = 2.0         # m2, plating tank [A]
WORK_DAYS = 300          # days/yr [A]
PLATING_HOURS = 16       # h/day [A]
EXPOSURE_YEARS = 30      # yr, typical residential exposure [A]

# Step 1: Chromic acid mist emission factor
# HJ 984-2018 附录B 表B.1: 0.38 g/m2.h for CrO3 mist (with suppressant) [S]
CHROMIC_FACTOR = 0.38    # g/m2.h
D_GH = CHROMIC_FACTOR * TANK_AREA  # 0.76 g/h total chromic acid mist

# Step 2: Collection efficiency
COLL_EFF = 0.90

# Step 3: Scrubber (≥95% for chromic acid, HJ 984-2018 附录F) [S]
SCRUB_EFF = 0.95

# Stack emission rate (g/s)
Q_GH = D_GH * COLL_EFF * (1 - SCRUB_EFF)  # 0.0342 g/h = 9.5e-6 g/s
Q_GS = Q_GH / 3600

# Emission concentration check
EXHAUST_VOL = 74.4 * TANK_AREA  # 148.8 m3/h (GB 21900 Tab6)
CONC_MG_M3 = Q_GH / EXHAUST_VOL * 1000  # 0.23 mg/m3
LIMIT_MG_M3 = 0.05  # GB 21900 表5 [S]
EXCEED_FACTOR = CONC_MG_M3 / LIMIT_MG_M3

# Stack parameters
STACK_H = 15
PLUME_RISE = 5
H_EFF = STACK_H + PLUME_RISE  # 20m

# Cr(VI) fraction in chromic acid mist
# Chromic acid mist from Cr plating bath: nearly all Cr is Cr(VI) [L]
CR6_FRACTION = 0.95  # 95% of emitted Cr is Cr(VI) [E]
Q_CR6_GS = Q_GS * CR6_FRACTION

# Cr mass fraction in chromic acid (CrO3 → Cr: 52/100 = 0.52)
CR_MASS_FRAC = 52.0 / 100.0  # Cr atomic mass / CrO3 molecular mass [C]
Q_CR_METAL_GS = Q_CR6_GS * CR_MASS_FRAC  # mass of elemental Cr(VI) emitted

# ====================================================================
# Step 4: Gaussian plume (Briggs urban parameters)
# ====================================================================

U_AVG = 3.0
RAIN_FRACTION = 0.08

STAB_FRACTIONS = {
    'A': 0.08, 'B': 0.15, 'C': 0.12,
    'D': 0.45, 'E': 0.12, 'F': 0.08,
}


def sigma_y_urban(x, stab):
    if stab in ('A', 'B'):
        return 0.32 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'C':
        return 0.22 * x / np.sqrt(1 + 0.0004 * x)
    elif stab == 'D':
        return 0.16 * x / np.sqrt(1 + 0.0004 * x)
    else:
        return 0.11 * x / np.sqrt(1 + 0.0004 * x)


def sigma_z_urban(x, stab):
    if stab in ('A', 'B'):
        return 0.24 * x * np.sqrt(1 + 0.0001 * x)
    elif stab == 'C':
        return 0.20 * x
    elif stab == 'D':
        return 0.14 * x / np.sqrt(1 + 0.0003 * x)
    else:
        return 0.08 * x / (1 + 0.0015 * x) ** 0.5


def ground_concentration(x, y, Q, u, H, stab):
    sy = sigma_y_urban(x, stab)
    sz = sigma_z_urban(x, stab)
    sy = np.maximum(sy, 1.0)
    sz = np.maximum(sz, 1.0)
    return (Q / (2 * np.pi * u * sy * sz)
            * np.exp(-y**2 / (2 * sy**2))
            * 2 * np.exp(-H**2 / (2 * sz**2)))


def column_integrated(x, y, Q, u, stab):
    sy = sigma_y_urban(x, stab)
    sy = np.maximum(sy, 1.0)
    return Q / (np.sqrt(2 * np.pi) * u * sy) * np.exp(-y**2 / (2 * sy**2))


# ====================================================================
# Step 5: Deposition
# ====================================================================

VD_CR = 0.003      # m/s, Cr(VI) aerosol dry deposition velocity [L]
LAMBDA_SCAV = 3e-5  # s-1, scavenging coefficient [L]


def annual_deposition(x, y, Q):
    """Annual total Cr(VI) deposition (g/m2/yr)."""
    sec_rain = SEC_PER_YEAR * RAIN_FRACTION
    F_total = 0.0
    Cg_avg = 0.0

    for stab, frac in STAB_FRACTIONS.items():
        Cg = ground_concentration(x, y, Q, U_AVG, H_EFF, stab)
        Ccol = column_integrated(x, y, Q, U_AVG, stab)

        Fd = Cg * VD_CR * SEC_PER_YEAR
        Fw = Ccol * LAMBDA_SCAV * sec_rain

        F_total += (Fd + Fw) * frac
        Cg_avg += Cg * frac

    return F_total, Cg_avg


# ====================================================================
# Step 6a: Soil accumulation
# ====================================================================

SOIL_BG_CR = 50       # mg/kg, background total Cr in S China soil [L]
SOIL_BG_CR6 = 0       # mg/kg, background Cr(VI) is typically ~0 [L]
SOIL_RHO = 1.3         # g/cm3 [L]
SOIL_H_MIX = 0.20      # m, plow layer [A]
SOIL_MASS = SOIL_RHO * 1000 * SOIL_H_MIX  # kg/m2 = 260 [C]

# GB 15618-2018 表1: Cr(VI) screening value
# Note: here we compare total Cr deposition - a simplified approach
# More rigorous: speciation-dependent, but screening model uses total Cr
GB_CR6_SCREEN = 3.0   # mg/kg, Cr(VI) screening [S]

# Cr(VI) reduction rate in soil (first-order)
# Cr(VI) → Cr(III) in soil: half-life varies widely (days to decades)
# depending on organic matter, pH, redox conditions, Fe/S availability.
# 2 yr is a screening-level estimate for typical aerobic soils. [L]
CR6_HALF_LIFE_YR = 2.0  # years [L]
CR6_DECAY = np.log(2) / CR6_HALF_LIFE_YR  # yr-1


def soil_cr_accumulation(F_annual, years):
    """Soil Cr(VI) over time considering deposition + first-order reduction.

    dC/dt = (F_total * f_cr6 / SOIL_MASS) - CR6_DECAY * C
    Analytical solution for constant F:
    C(t) = C0 * exp(-k*t) + (F*f/SOIL_MASS/k) * (1 - exp(-k*t))
    """
    k = CR6_DECAY
    F = F_annual * CR_MASS_FRAC  # g/m2/yr Cr metal (F_annual is already Cr(VI)-only)
    C0 = SOIL_BG_CR6

    if k > 0:
        steady = F / (SOIL_MASS * k) * 1000  # g/m2/yr / (kg/m2 * 1/yr) * 1000 = mg/kg
        C_t = C0 * np.exp(-k * years) + steady * (1 - np.exp(-k * years))
    else:
        C_t = C0 + F / SOIL_MASS * years * 1000

    return C_t * 1000  # convert to μg/kg for comparison (more readable)


# ====================================================================
# Step 6b: Health risk assessment
# ====================================================================

# ---- Inhalation cancer risk ----
# US EPA IRIS: Cr(VI) inhalation unit risk = 0.012 per μg/m3
# [S: https://iris.epa.gov/ChemicalLanding/&substance_nmbr=144]
# Means: lifetime exposure to 1 μg/m3 → 0.012 excess cancer risk (1.2%)
INHALATION_UNIT_RISK = 0.012  # per μg/m3 [S]

# Exposure parameters (Chinese adult, conservative residential)
# [L: HJ 25.3-2019 建设用地土壤污染风险评估技术导则]
BW = 65              # kg, body weight [E]
IR_INHALE = 15       # m3/day, inhalation rate [E]
EF = 350             # days/yr, exposure frequency [E]
ED = 24              # yr, exposure duration [E]
AT_CANCER = 70 * 365 # days, averaging time for carcinogens [S]

# ---- Ingestion cancer risk (soil ingestion, vegetable consumption) ----
# Daily soil ingestion rate (adult, inadvertent)
IR_SOIL = 0.05       # g/day [L]
# Vegetable ingestion (home-grown, contaminated)
IR_VEG = 0.3         # kg/day fresh weight [E]
# Cr(VI) soil-to-plant transfer factor
# [L: literature range 0.01-0.1 for Cr]
TF_SOIL_PLANT = 0.05  # unitless [L]

# Cr(VI) oral slope factor (US EPA IRIS)
# Note: oral slope factor for Cr(VI) is debated. Using 0.5 (mg/kg-day)-1 [L]
ORAL_SF = 0.5        # (mg/kg-day)-1 [L]


def inhalation_cancer_risk(C_ground_ug_m3):
    """Excess lifetime cancer risk from Cr(VI) inhalation.

    Risk = C * UR * (EF * ED) / (AT * 365/365)
    Simplified: Risk = C_μg_m3 * UnitRisk * (ED/70)
    where ED/70 adjusts for partial lifetime exposure.
    """
    return C_ground_ug_m3 * INHALATION_UNIT_RISK * (ED / 70)


def ingestion_cancer_risk(C_soil_mg_kg):
    """Excess lifetime cancer risk from Cr(VI) ingestion.

    Pathways: soil ingestion + vegetable consumption
    CDI = C_soil * (IR_soil + IR_veg * TF) * EF * ED / (BW * AT)

    Note: returns risk from Cr(VI) only. Total Cr risk is higher.
    """
    # Simplified: Cr(VI) in soil directly ingested + plant uptake
    daily_intake_soil = C_soil_mg_kg * IR_SOIL / 1000  # mg/day (soil: mg/kg * g/day / 1000)
    daily_intake_veg = C_soil_mg_kg * IR_VEG * TF_SOIL_PLANT  # mg/day (veg: kg/day * TF)

    daily_intake = daily_intake_soil + daily_intake_veg  # mg/day
    CDI = daily_intake * EF * ED / (BW * AT_CANCER)  # mg/kg-day
    return CDI * ORAL_SF


# ====================================================================
# Risk interpretation
# ====================================================================
def risk_level(risk):
    if risk < 1e-6:
        return 'Negligible', '#36B37E'
    elif risk < 1e-5:
        return 'Very Low', '#7BC67E'
    elif risk < 1e-4:
        return 'Low', '#FFA726'
    elif risk < 1e-3:
        return 'Moderate', '#FF6B35'
    else:
        return 'High', '#E5534B'


# ====================================================================
# Output
# ====================================================================
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(OUT_DIR, exist_ok=True)


# ====================================================================
# Figure 1: Cr(VI) ground concentration profile
# ====================================================================
def fig_cr_conc_profile():
    """Cr(VI) ground concentration vs downwind distance."""
    print("[Fig 1] Cr(VI) ground concentration...")
    x_vals = np.linspace(100, 5000, 150)
    stab = 'D'

    Cg = np.array([ground_concentration(x, 0, Q_CR6_GS, U_AVG, H_EFF, stab)
                   for x in x_vals])

    fig, (ax_conc, ax_risk) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: concentration
    ax_conc.plot(x_vals / 1000, Cg * 1e6, '#E5534B', linewidth=2, label='Cr(VI)')
    idx_max = np.argmax(Cg)
    ax_conc.plot(x_vals[idx_max] / 1000, Cg[idx_max] * 1e6, 'o', color='#E5534B', markersize=7)
    ax_conc.text(x_vals[idx_max] / 1000 + 0.15, Cg[idx_max] * 1e6,
                 f'Peak: {Cg[idx_max]*1e6:.4f} ug/m3\n@{x_vals[idx_max]:.0f}m',
                 fontsize=8, color='#E5534B')

    # WHO reference: unit risk 0.012 per μg/m³, 1×10⁻⁶ at 8.33e-5 μg/m³
    who_ref = 1e-6 / 0.012  # μg/m³
    ax_conc.axhline(who_ref, color='gray', linestyle=':', linewidth=1, alpha=0.6)
    ax_conc.text(5.2, who_ref * 1.3,
                 f'WHO unit risk\n{who_ref:.1e} ug/m3\n(1E-6 risk)',
                 fontsize=7, color='gray')

    ax_conc.set_xlabel('Downwind distance (km)')
    ax_conc.set_ylabel('Cr(VI) concentration (ug/m3)')
    ax_conc.set_xlim(0, 5.5)
    ax_conc.grid(True, alpha=0.3)
    ax_conc.set_title('Cr(VI) ground concentration (D stability)', fontsize=11)

    # Right: inhalation cancer risk
    risk = np.array([inhalation_cancer_risk(c * 1e6) for c in Cg])
    ax_risk.plot(x_vals / 1000, risk, '#E5534B', linewidth=2)

    # Risk thresholds
    ax_risk.axhline(1e-6, color='green', linestyle='--', linewidth=1, alpha=0.6)
    ax_risk.text(5.2, 1.1e-6, '1E-6 (Negligible)', fontsize=8, color='green')
    ax_risk.axhline(1e-4, color='orange', linestyle='--', linewidth=1, alpha=0.6)
    ax_risk.text(5.2, 1.1e-4, '1E-4 (Moderate)', fontsize=8, color='orange')

    ax_risk.set_xlabel('Downwind distance (km)')
    ax_risk.set_ylabel('Excess lifetime cancer risk')
    ax_risk.set_yscale('log')
    ax_risk.set_ylim(1e-8, 0.1)
    ax_risk.set_xlim(0, 5.5)
    ax_risk.grid(True, alpha=0.3)
    ax_risk.set_title('Inhalation cancer risk (30yr exposure)', fontsize=11)

    fig.suptitle('Cr(VI) ground concentration and cancer risk', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_cr_conc_risk.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {path}")


# ====================================================================
# Figure 2: Cr(VI) deposition flux spatial distribution
# ====================================================================
def fig_cr_deposition_map():
    """Plan view of annual Cr(VI) deposition flux."""
    print("[Fig 2] Cr(VI) deposition spatial map...")

    x_vals = np.linspace(100, 5000, 150)
    y_vals = np.linspace(-500, 500, 100)
    X, Y = np.meshgrid(x_vals, y_vals)

    F_total = np.zeros_like(X)
    sec_rain = SEC_PER_YEAR * RAIN_FRACTION

    for stab, frac in STAB_FRACTIONS.items():
        sy = sigma_y_urban(X, stab)
        sy = np.maximum(sy, 1.0)
        sz = sigma_z_urban(X, stab)
        sz = np.maximum(sz, 1.0)

        Cg = (Q_CR6_GS / (2 * np.pi * U_AVG * sy * sz)
              * np.exp(-Y**2 / (2 * sy**2))
              * 2 * np.exp(-H_EFF**2 / (2 * sz**2)))

        Ccol = (Q_CR6_GS / (np.sqrt(2 * np.pi) * U_AVG * sy)
                * np.exp(-Y**2 / (2 * sy**2)))

        Fd = Cg * VD_CR * SEC_PER_YEAR
        Fw = Ccol * LAMBDA_SCAV * sec_rain
        F_total += (Fd + Fw) * frac

    # Convert to g/ha/yr for Cr metal
    F_cr_metal = F_total * CR6_FRACTION * CR_MASS_FRAC * 1e4
    # Convert to mg/m2/yr for readability
    F_cr_mg_m2 = F_total * CR6_FRACTION * CR_MASS_FRAC * 1000

    fig, ax = plt.subplots(figsize=(10, 6))
    levels = np.logspace(np.log10(max(F_cr_metal.min(), 0.001)),
                         np.log10(max(F_cr_metal.max(), 0.1)), 12)

    cf = ax.contourf(X / 1000, Y / 1000, F_cr_metal,
                     levels=levels, cmap='YlOrRd', extend='both')

    ax.plot(0, 0, 'v', color='k', markersize=12, zorder=5)
    ax.annotate('Stack', xy=(0, 0), xytext=(0.2, 0.15),
                arrowprops=dict(arrowstyle='->'), fontsize=9)

    ax.annotate('', xy=(2, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(0.8, 0.04, 'Wind ->', fontsize=9, color='gray')

    for r in [1, 3]:
        c = plt.Circle((0, 0), r, fill=False, color='gray',
                       linestyle=':', linewidth=0.8, alpha=0.5)
        ax.add_patch(c)
        ax.text(r, 0.04, f'{r}km', fontsize=8, color='gray')

    ax.set_xlabel('Downwind distance (km)')
    ax.set_ylabel('Crosswind distance (km)')
    ax.set_xlim(0, 5)
    ax.set_ylim(-0.5, 0.5)
    ax.set_aspect('equal')

    cbar = plt.colorbar(cf, ax=ax, shrink=0.8,
                        label='Cr(VI) deposition (g/ha/yr)')
    fig.suptitle('Annual Cr(VI) deposition flux', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_cr_deposition_map.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {path}")


# ====================================================================
# Figure 3: Soil Cr accumulation over time
# ====================================================================
def fig_cr_soil_accumulation():
    """Soil Cr(VI) accumulation and decay at key distances."""
    print("[Fig 3] Soil Cr(VI) accumulation...")

    distances = [200, 500, 1000, 2000]
    years = np.arange(0, 51, 0.5)

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ['#E5534B', '#FF6B35', '#FFA726', '#4ECDC4']
    GB_label_added = False

    for dist, color in zip(distances, colors):
        F_ann, Cg = annual_deposition(dist, 0, Q_CR6_GS)
        C_soil = soil_cr_accumulation(F_ann, years)
        label = f'{dist}m (Cg={Cg*1e6:.6f} ug/m3)'
        ax.plot(years, C_soil, color=color, linewidth=2, label=label)

        # Endpoint
        end_val = C_soil[-1]
        ax.plot(50, end_val, 'o', color=color, markersize=5)
        ax.text(50.2, end_val, f'{end_val:.1f}', fontsize=7.5, color=color)

    # Note: GB 15618-2018 Cr(VI) screening is 3.0 mg/kg = 3000 μg/kg,
    # which is ~4 orders of magnitude above the y-axis range — omit from figure,
    # the comparison is conveyed in the article text instead.
    ax.text(0.5, 0.38, 'GB 筛选值 3000 μg/kg\n（远超出本图范围）',
            fontsize=7.5, color='orange', alpha=0.6, fontweight='bold',
            bbox=dict(facecolor='white', edgecolor='orange', alpha=0.3, boxstyle='round'))

    ax.set_xlabel('运行年限')
    ax.set_ylabel('土壤 Cr(VI) (μg/kg)')
    ax.set_xlim(0, 56)
    ax.legend(fontsize=8, title='Distance from stack')
    ax.grid(True, alpha=0.3)

    fig.suptitle('Soil Cr(VI) accumulation with reduction (t_1/2=2yr)', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_cr_soil.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {path}")


# ====================================================================
# Figure 4: Risk comparison (inhalation vs ingestion)
# ====================================================================
def fig_cr_risk_comparison():
    """Compare inhalation and ingestion cancer risk at different distances."""
    print("[Fig 4] Risk comparison inhalation vs ingestion...")

    x_vals = np.linspace(100, 5000, 100)
    stab = 'D'

    fig, ax = plt.subplots(figsize=(10, 6))

    # Inhalation risk
    Cg = np.array([ground_concentration(x, 0, Q_CR6_GS, U_AVG, H_EFF, stab)
                   for x in x_vals])
    risk_inh = np.array([inhalation_cancer_risk(c * 1e6) for c in Cg])
    ax.plot(x_vals / 1000, risk_inh, '#E5534B', linewidth=2.5,
            label='Inhalation (direct)')

    # Ingestion risk (via soil accumulation)
    risk_ing = np.array([])
    for x in x_vals:
        F_ann, _ = annual_deposition(x, 0, Q_CR6_GS)
        C_soil_30yr = soil_cr_accumulation(F_ann, np.array([30]))[0]
        risk_30yr = ingestion_cancer_risk(C_soil_30yr / 1000)  # convert ug/kg to mg/kg
        risk_ing = np.append(risk_ing, risk_30yr)

    ax.plot(x_vals / 1000, risk_ing, '#2E86AB', linewidth=2.5,
            label='Ingestion (30yr soil + veg)')

    # Combined
    risk_total = risk_inh + risk_ing
    ax.plot(x_vals / 1000, risk_total, '#6C5CE7', linewidth=2, linestyle='--',
            label='Combined', alpha=0.8)

    # Thresholds
    ax.axhline(1e-6, color='gray', linestyle=':', linewidth=1, alpha=0.7)
    ax.text(5.2, 1.3e-6, '1E-6 Negligible', fontsize=8, color='gray')
    ax.axhline(1e-5, color='orange', linestyle='--', linewidth=1, alpha=0.7)
    ax.text(5.2, 1.3e-5, '1E-5 Low', fontsize=8, color='orange')
    ax.axhline(1e-4, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.text(5.2, 1.3e-4, '1E-4 Moderate', fontsize=8, color='red')

    ax.set_xlabel('Downwind distance (km)')
    ax.set_ylabel('Excess lifetime cancer risk')
    ax.set_yscale('log')
    ax.set_ylim(1e-9, 0.1)
    ax.set_xlim(0, 5.5)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle('Cr(VI) cancer risk: inhalation vs ingestion pathways', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_cr_risk.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {path}")


# ====================================================================
# Figure 5: Cr(VI) mass balance summary (pie/bar)
# ====================================================================
def fig_cr_mass_balance():
    """Cr mass flow through the system."""
    print("[Fig 5] Cr mass balance summary...")

    categories = [
        'Generated in bath',
        'Collected by hood',
        'Removed by scrubber',
        'Stack emission',
        'Fugitive (uncollected)',
    ]

    D_total = D_GH  # 0.76 g/h total chromic acid
    collected = D_total * COLL_EFF  # 0.684
    emitted = collected * (1 - SCRUB_EFF)  # 0.0342
    removed = collected - emitted  # 0.6498
    fugitive = D_total * (1 - COLL_EFF)  # 0.076

    # As Cr metal (g/h)
    values = [
        D_total * CR_MASS_FRAC,
        collected * CR_MASS_FRAC,
        removed * CR_MASS_FRAC,
        emitted * CR_MASS_FRAC,
        fugitive * CR_MASS_FRAC,
    ]

    colors = ['#B0BEC5', '#78909C', '#36B37E', '#E5534B', '#FFA726']

    fig, (ax_pie, ax_bar) = plt.subplots(1, 2, figsize=(12, 5))

    # Pie: emitted vs removed
    sizes = [emitted * CR_MASS_FRAC, removed * CR_MASS_FRAC, fugitive * CR_MASS_FRAC]
    labels_pie = [f'Stack emission\n{sizes[0]:.4f} g/h',
                  f'Scrubber removed\n{sizes[1]:.4f} g/h',
                  f'Fugitive\n{sizes[2]:.4f} g/h']
    colors_pie = ['#E5534B', '#36B37E', '#FFA726']
    ax_pie.pie(sizes, labels=labels_pie, colors=colors_pie, autopct='%1.1f%%',
               startangle=90, textprops={'fontsize': 9})
    ax_pie.set_title('Cr mass flow distribution', fontsize=12)

    # Bar: stepwise mass reduction
    bar_labels = ['Generation', 'After collection', 'After scrubber', 'Stack emission']
    bar_values = [
        D_total * CR_MASS_FRAC,
        collected * CR_MASS_FRAC,
        collected * CR_MASS_FRAC - removed * CR_MASS_FRAC + 1e-10,
        emitted * CR_MASS_FRAC,
    ]
    bar_values[2] = bar_values[3]  # after scrubber = stack emission
    bar_colors = ['#78909C', '#FFA726', '#36B37E', '#E5534B']

    bars = ax_bar.bar(bar_labels, bar_values, color=bar_colors, alpha=0.85, width=0.6)
    for bar, val in zip(bars, bar_values):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
                    f'{val:.4f}', ha='center', fontsize=9, fontweight='bold')

    ax_bar.set_ylabel('Cr metal mass flow (g/h)')
    ax_bar.set_ylim(0, 0.45)
    ax_bar.tick_params(axis='x', rotation=15)
    ax_bar.grid(True, alpha=0.3, axis='y')

    fig.suptitle('Cr(VI) mass flow through emission control system', fontsize=13)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, 'fig_cr_mass_balance.png')
    plt.savefig(path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {path}")

    return {
        'D_total': D_total,
        'collected': collected,
        'removed': removed,
        'emitted': emitted,
        'fugitive': fugitive,
    }


# ====================================================================
# Main
# ====================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("Electroplating Cr(VI) Model")
    print("Screening-level model. See parameter comments for source types.")
    print("=" * 70)

    print(f"\n[Steps 1-3] Emission calculation")
    print(f"  Tank area: {TANK_AREA} m2")
    print(f"  Cr generation rate: {D_GH:.4f} g/h")
    print(f"  Collection eff: {COLL_EFF*100:.0f}%")
    print(f"  Scrubber eff: {SCRUB_EFF*100:.0f}%")
    print(f"  Stack emission: {Q_GH:.6f} g/h = {Q_GS:.8f} g/s")
    print(f"  Exhaust conc: {CONC_MG_M3:.4f} mg/m3 (limit {LIMIT_MG_M3}, {EXCEED_FACTOR:.1f}x exceed)")
    print(f"  Cr(VI) emission rate: {Q_CR6_GS:.8f} g/s")
    print(f"  Cr metal emission rate: {Q_CR_METAL_GS:.8f} g/s")

    print(f"\n[Dispersion & deposition]")
    x_test = np.arange(200, 5000, 50)
    F_test = np.array([annual_deposition(x, 0, Q_CR6_GS)[0] for x in x_test])
    idx_max = np.argmax(F_test)
    peak_x = x_test[idx_max]

    F_peak, Cg_peak = annual_deposition(peak_x, 0, Q_CR6_GS)
    print(f"  Peak deposition: {peak_x:.0f}m downwind")
    print(f"  C_ground at peak: {Cg_peak*1e6:.6f} ug/m3")

    risk_peak = inhalation_cancer_risk(Cg_peak * 1e6)
    lvl, _ = risk_level(risk_peak)
    print(f"  Inhalation cancer risk: {risk_peak:.2e} -> {lvl}")

    print(f"\n[Soil accumulation & health risk]")
    print(f"{'Distance':>10} {'Soil Cr(VI)':>15} {'Inh Risk':>12} {'Ing Risk':>12} {'Total Risk':>12} {'Level':>12}")
    print("-" * 75)

    for dist in [200, 500, 1000, 2000, 3000]:
        F_ann, Cg = annual_deposition(dist, 0, Q_CR6_GS)
        C_soil = soil_cr_accumulation(F_ann, np.array([30]))[0]
        risk_inh = inhalation_cancer_risk(Cg * 1e6)
        risk_ing = ingestion_cancer_risk(max(C_soil / 1000, 1e-10))
        risk_tot = risk_inh + risk_ing
        lvl, _ = risk_level(risk_tot)
        print(f"{dist:>7.0f}m {C_soil:>11.1f} ug/kg {risk_inh:>10.2e} {risk_ing:>10.2e} {risk_tot:>10.2e} {lvl:>12}")

    print(f"\nGenerating figures...")
    mb = fig_cr_mass_balance()
    fig_cr_conc_profile()
    fig_cr_deposition_map()
    fig_cr_soil_accumulation()
    fig_cr_risk_comparison()

    print(f"\nDone!")
