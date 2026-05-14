"""
River sediment heavy metal (Cd) distribution model
Classic suspended sediment-contaminant coupled model.

Theory:
  1D steady-state suspended sediment transport (Einstein 1950; Chapra 1997)
    dS_i/dx = -(w_si / (h*v)) * S_i

  Solute transport with first-order loss from sedimentation:
    C(x) = C_0 * exp(-alpha * x) + C_bg

Key processes:
  1. Multi-size class sediment transport - independent settling per class (Stokes law)
  2. Particle-water partitioning - Cd partitions to particles (Kd approach, >90% particulate)
  3. Bed sediment mixing - fresh deposit mixes with active layer background sediment

Usage:
  python models/river_sediment_cd.py
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
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
# Model parameters
# ====================================================================

# River hydraulics
RIVER_LEN = 100_000          # river length (m)
FLOW_VEL = 0.8               # mean flow velocity (m/s)
MEAN_DEPTH = 2.0             # mean depth (m)
WIDTH = 50.0                 # mean width (m)

# Source parameters
TSS0 = 500.0                 # mg/L, headwater TSS (mining-impacted)
CD_ROCK = 1.0                # mg/kg, Cd concentration in waste rock

# Background
CD_BG = 0.2                  # mg/kg, regional background Cd in sediment
J_BG = 8e-6                  # kg/(m2.s), background sediment deposition flux

# Grain size classes
# (name, diameter um, source fraction, Cd enrichment factor EF, color)
GRAIN_CLASSES = [
    dict(name="Clay",    d_um=2,   f_src=0.50, EF=12, color="#8B0000"),
    dict(name="FSilt",   d_um=10,  f_src=0.30, EF=8,  color="#D2691E"),
    dict(name="CSilt",   d_um=40,  f_src=0.15, EF=3,  color="#BDB76B"),
    dict(name="VFSand",  d_um=62,  f_src=0.04, EF=1.5,color="#6B8E23"),
    dict(name="FSand",   d_um=125, f_src=0.01, EF=0.5,color="#8B7355"),
]


# ====================================================================
# Physical computation
# ====================================================================

def stokes_w(d, rho_s=2650, rho_w=1000, nu=1e-6):
    """Stokes settling velocity (m/s)

    w = (rho_s/rho_w - 1) * g * d^2 / (18 * nu)
    where nu is kinematic viscosity (mu/rho_w).
    """
    g = 9.81
    return (rho_s / rho_w - 1) * g * d**2 / (18 * nu)


def compute_profile(x_m, classes, tss0, cd_rock, v, h, j_bg, cd_bg):
    """
    Compute longitudinal profiles of suspended sediment and bed Cd.

    Parameters
    ----------
    x_m : ndarray, shape (N,)
        Distance array (m)
    classes : list of dict
        Grain class definitions (fields: d, f_src, EF, color, name)
    tss0 : float
        Headwater TSS (mg/L)
    cd_rock : float
        Waste rock Cd (mg/kg)
    v : float
        Flow velocity (m/s)
    h : float
        Mean depth (m)
    j_bg : float
        Background sediment flux (kg/(m2.s))
    cd_bg : float
        Background Cd (mg/kg)

    Returns
    -------
    dict with keys:
      C_bed  - bed Cd concentration (mg/kg)
      J_sed  - (n_classes, N) sediment deposition flux per class
      J_Cd   - (n_classes, N) Cd deposition flux per class
      C_dep  - Cd concentration in freshly deposited sediment
      S      - (n_classes, N) suspended sediment concentration (kg/m3)
      x_km   - distance in km
    """
    n = len(x_m)

    # 1. Settling velocities and initial conditions
    S0 = tss0 / 1000.0           # mg/L -> kg/m3
    for c in classes:
        d_m = c['d_um'] * 1e-6
        c['w_s'] = stokes_w(d_m)
        c['S0'] = S0 * c['f_src']            # kg/m3
        c['Cd_p'] = cd_rock * c['EF']         # mg/kg
        c['alpha'] = c['w_s'] / (h * v)       # decay coefficient (1/m)

    n_cls = len(classes)
    S = np.zeros((n_cls, n))
    J_sed = np.zeros((n_cls, n))
    J_Cd = np.zeros((n_cls, n))

    # 2. Compute profiles
    for i, c in enumerate(classes):
        S[i, :] = c['S0'] * np.exp(-c['alpha'] * x_m)
        J_sed[i, :] = c['w_s'] * S[i, :]
        J_Cd[i, :] = c['w_s'] * S[i, :] * c['Cd_p']

    # 3. Totals
    J_sed_total = np.sum(J_sed, axis=0)
    J_Cd_total = np.sum(J_Cd, axis=0)

    # 4. Cd concentration in freshly deposited sediment (mg/kg)
    C_dep = np.divide(J_Cd_total, J_sed_total,
                      out=np.full_like(J_sed_total, cd_bg),
                      where=J_sed_total > 0)

    # 5. Bed Cd concentration (active layer mixing model)
    C_bed = (J_Cd_total + cd_bg * j_bg) / (J_sed_total + j_bg)

    return dict(
        C_bed=C_bed, J_sed=J_sed, J_Cd=J_Cd,
        C_dep=C_dep, S=S,
        J_sed_total=J_sed_total, J_Cd_total=J_Cd_total,
        x_km=x_m / 1000.0,
        classes=classes,
    )


# ====================================================================
# Plot 1: Concentration distribution curve
# ====================================================================

def plot_concentration_profile(result, save_path=None):
    """Plot Cd concentration profile + grain class deposition stacking."""
    x_km = result['x_km']
    C_bed = result['C_bed']
    J_sed = result['J_sed']
    classes = result['classes']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7),
                                    gridspec_kw={'height_ratios': [3, 2]})
    fig.subplots_adjust(hspace=0.28)

    # ---- Top: bed Cd concentration ----
    ax1.plot(x_km, C_bed, 'o-', color='#DC143C', linewidth=2.2,
             markersize=4, markerfacecolor='white', markeredgewidth=1.2,
             label='Model (bed Cd)', zorder=5)

    # Zone fills
    ax1.axvspan(0, 15, alpha=0.08, color='red', label='Near-source (0-15 km)')
    ax1.axvspan(15, 50, alpha=0.08, color='orange', label='Transition (15-50 km)')
    ax1.axvspan(50, 100, alpha=0.08, color='green', label='Background (50-100 km)')

    # Background line
    ax1.axhline(CD_BG, color='gray', linestyle='--', linewidth=1.0, alpha=0.7)
    ax1.text(102, CD_BG * 1.1, f'Background {CD_BG} mg/kg',
             fontsize=9, color='gray', va='bottom')

    # Peak annotation
    peak_idx = np.argmax(C_bed)
    ax1.annotate(
        f'Peak {C_bed[peak_idx]:.2f} mg/kg\n@ {x_km[peak_idx]:.0f} km',
        xy=(x_km[peak_idx], C_bed[peak_idx]),
        xytext=(x_km[peak_idx] + 15, C_bed[peak_idx] * 0.5),
        arrowprops=dict(arrowstyle='->', color='#333', lw=1.2),
        fontsize=10, color='#333', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.85),
    )
    # Source annotation
    ax1.annotate(
        f'Source: waste rock\n{CD_ROCK} mg/kg',
        xy=(1, C_bed[0]),
        xytext=(1, C_bed[0] * 0.95),
        fontsize=9, color='#8B0000',
    )

    ax1.set_xlabel('Distance from source (km)', fontsize=11)
    ax1.set_ylabel('Bed Cd concentration (mg/kg)', fontsize=11)
    ax1.set_xlim(-2, 110)
    ax1.set_ylim(bottom=0)
    ax1.set_title('Longitudinal Cd concentration in river sediment',
                  fontsize=14, fontweight='bold', pad=10)
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # ---- Bottom: deposition flux stacking ----
    colors = [c['color'] for c in classes]
    labels = [c['name'] for c in classes]
    ax2.stackplot(x_km, J_sed * 1000, colors=colors, alpha=0.85,
                  labels=labels)

    # Total Cd flux overlay
    ax2_twin = ax2.twinx()
    ax2_twin.plot(x_km, result['J_Cd_total'] * 1e6, '--', color='#333',
                  linewidth=1.5, label='Cd deposition flux')
    ax2_twin.set_ylabel('Cd flux (ug/(m2.s))', fontsize=10, color='#333')

    ax2.set_xlabel('Distance from source (km)', fontsize=11)
    ax2.set_ylabel('Sediment flux (g/(m2.s))', fontsize=11)
    ax2.set_xlim(-2, 110)
    ax2.set_title('Grain class sediment deposition + Cd flux (dashed)',
                  fontsize=12, pad=8)
    ax2.grid(True, alpha=0.3)

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right',
               fontsize=8, framealpha=0.9)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'[OK] Concentration profile -> {save_path}')
    plt.show()


# ====================================================================
# Plot 2: River cross-section schematic
# ====================================================================

def plot_cross_section(save_path=None):
    """Draw river cross-section with Cd transport pathways."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # ---- Channel geometry ----
    bank_left = -30
    bank_right = 30
    water_surface = 3

    # Trapezoidal channel
    channel = Polygon([
        (bank_left, -1.5),
        (bank_left, water_surface + 1),
        (bank_right, water_surface + 1),
        (bank_right, -1.8),
    ], facecolor='#F5E6C8', edgecolor='#8B7355', linewidth=1.5,
       alpha=0.4, zorder=1)
    ax.add_patch(channel)

    # Water body
    water = Polygon([
        (-27, 0), (27, 0), (27, water_surface), (-27, water_surface),
    ], facecolor='#B0D4F1', edgecolor='#4A86B8', linewidth=1.5,
       alpha=0.6, zorder=2)
    ax.add_patch(water)

    # ---- Bed sediment layers ----
    # Deep background layer
    sed_bg = Polygon([
        (-28, -1.5), (28, -1.8), (28, -4), (-28, -4),
    ], facecolor='#CDAA7D', edgecolor='#8B7355', linewidth=0.5,
       alpha=0.5, zorder=3)
    ax.add_patch(sed_bg)
    ax.text(0, -3.0, 'Background sediment', fontsize=8, color='#8B7355',
            ha='center', va='center', alpha=0.8)

    # Mid layer (contaminated)
    sed_mid = Polygon([
        (-26, -0.5), (26, -0.8), (26, -1.5), (-28, -1.5),
    ], facecolor='#D2A54A', edgecolor='#A0762C', linewidth=0.5,
       alpha=0.6, zorder=3)
    ax.add_patch(sed_mid)
    ax.text(0, -1.0, 'Contaminated sediment (Cd ~2-5 mg/kg)', fontsize=8,
            color='#8B4513', ha='center', va='center')

    # Top active layer
    sed_top = Polygon([
        (-25, 0.3), (25, 0.0), (25, -0.5), (-26, -0.5),
    ], facecolor='#CD5C5C', edgecolor='#8B0000', linewidth=0.8,
       alpha=0.5, zorder=3)
    ax.add_patch(sed_top)
    ax.text(0, -0.15, 'Active layer (fine particle enrichment)',
            fontsize=7, color='#8B0000', ha='center', va='center')

    # ---- Arrows and labels ----
    # Dissolved Cd transport (upper water column)
    ax.annotate('', xy=(10, 1.8), xytext=(-10, 1.8),
                arrowprops=dict(arrowstyle='->', color='#1565C0', lw=1.8))
    ax.text(0, 2.0, 'Dissolved Cd2+ transport', fontsize=9, color='#1565C0',
            ha='center', va='bottom', fontweight='bold')

    # Suspended particle transport (lower water column)
    ax.annotate('', xy=(12, 0.6), xytext=(-12, 0.6),
                arrowprops=dict(arrowstyle='->', color='#8B0000', lw=2.2))
    ax.text(0, 0.8, 'Suspended particle Cd transport (main pathway)',
            fontsize=9, color='#8B0000', ha='center', va='bottom',
            fontweight='bold')

    # Settling arrows
    for x_pos in [-15, 0, 15]:
        ax.annotate('', xy=(x_pos, -0.3), xytext=(x_pos, 0.3),
                    arrowprops=dict(arrowstyle='->', color='#666', lw=1.2))
    ax.text(-15, 0.0, 'v', fontsize=14, color='#666', ha='center',
            va='center')
    ax.text(0, 0.0, 'v', fontsize=14, color='#666', ha='center',
            va='center')
    ax.text(15, 0.0, 'v', fontsize=14, color='#666', ha='center',
            va='center')
    ax.text(0, -0.65, 'Particle settling', fontsize=8, color='#666',
            ha='center')

    # Bedload transport (bottom)
    ax.annotate('', xy=(20, -2.5), xytext=(-20, -2.5),
                arrowprops=dict(arrowstyle='->', color='#8B7355', lw=1.0))
    ax.text(0, -2.7, 'Bedload transport (slow)', fontsize=7, color='#8B7355',
            ha='center', va='top')

    # ---- Right-side legend ----
    legend_y = 5.8

    # Grain size sorting
    ax.text(32, legend_y, 'Grain size sorting', fontsize=10,
            fontweight='bold', color='#333', va='top')

    grain_info = [
        ('Fine sand (125 um)', '#8B7355', 'rapid settling, near-source'),
        ('V. fine sand (62 um)', '#6B8E23', ''),
        ('Coarse silt (40 um)', '#BDB76B', 'moderate settling, transition'),
        ('Fine silt (10 um)', '#D2691E', ''),
        ('Clay (2 um)', '#8B0000', 'long-range transport, distal'),
    ]
    for i, (name, color, note) in enumerate(grain_info):
        y_pos = legend_y - 0.6 * (i + 1)
        ax.plot([32, 33.5], [y_pos, y_pos], color=color, linewidth=4,
                alpha=0.8)
        ax.text(34, y_pos, name, fontsize=8, color='#333', va='center')
        if note:
            ax.text(48, y_pos, note, fontsize=7, color='gray', va='center')

    # Cd pathway legend
    path_y = legend_y - 3.8
    ax.text(32, path_y, 'Cd transport pathways', fontsize=10,
            fontweight='bold', color='#333', va='top')
    paths = [
        ('Dissolved Cd2+ ->', '#1565C0', '<5% of total Cd'),
        ('Suspended particle Cd ->', '#8B0000', '>90% main pathway'),
        ('Bedload ->', '#8B7355', '<5%, slow'),
    ]
    for i, (label, color, note) in enumerate(paths):
        y_pos = path_y - 0.6 * (i + 1)
        ax.plot([32, 33.5], [y_pos, y_pos], color=color, linewidth=3)
        ax.text(34, y_pos, f'{label}  {note}', fontsize=8, color='#333',
                va='center')

    # ---- Axis and layout ----
    ax.set_xlim(-35, 60)
    ax.set_ylim(-5, 7.5)
    # ax.set_aspect('equal')  # removed: data range is 9:1 (x:y), figure is 2:1
    ax.axis('off')
    ax.set_title('River cross-section: Cd transport pathways',
                 fontsize=14, fontweight='bold', pad=12)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'[OK] Cross-section -> {save_path}')
    plt.show()


# ====================================================================
# Time-dependent bed accumulation
# ====================================================================

def compute_time_evolution(result, active_depth=0.05, bulk_density=1600,
                           max_years=50):
    """
    Time-dependent active layer Cd concentration.

    Active layer is a fixed-thickness surface sediment layer (e.g. 5 cm)
    that exchanges with the water column. Cd concentration evolves as:

      dC/dt = (J_Cd_in - C * J_out) / M_layer

    Solution: C(t) = C_ss + (C_0 - C_ss) * exp(-t / tau)
    where tau = M_layer / J_out

    Returns
    -------
    dict with t_years (T,), C_active (N, T), tau_days (N,), C_ss (N,)
    """
    J_sed = result['J_sed_total']      # kg/(m2.s)
    J_Cd = result['J_Cd_total']        # mg/(m2.s)
    C_ss = result['C_bed']             # mg/kg, steady state

    M_layer = bulk_density * active_depth  # kg/m2
    J_out = J_sed + J_BG                   # kg/(m2.s)

    # Time array in seconds, log-spaced for early resolution
    sec_per_year = 365.25 * 24 * 3600
    t = np.logspace(-2, np.log10(max_years), 500) * sec_per_year
    t_years = t / sec_per_year

    N = len(J_sed)
    T = len(t)
    C_active = np.zeros((N, T))
    tau_days = np.zeros(N)

    for i in range(N):
        tau = M_layer / max(J_out[i], 1e-12)   # seconds
        tau_days[i] = tau / (24 * 3600)
        C_active[i, :] = C_ss[i] + (CD_BG - C_ss[i]) * np.exp(-t / tau)

    return dict(
        t_years=t_years, C_active=C_active,
        tau_days=tau_days, C_ss=C_ss,
        x_km=result['x_km'],
        J_sed_total=J_sed, J_Cd_total=J_Cd,
    )


# ====================================================================
# Plot 3: Time evolution of bed Cd
# ====================================================================

def plot_time_evolution(steady_result, time_result, save_path=None):
    """Plot approach to steady state + spatial profiles at different times."""
    x_km = time_result['x_km']
    t_years = time_result['t_years']
    C_active = time_result['C_active']
    tau_days = time_result['tau_days']
    C_ss = time_result['C_ss']

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # ── Left panel: approach to steady state at selected distances ──
    ax = axes[0]
    dists = [0, 3, 8, 20, 50, 100]
    colors = ['#8B0000', '#D2691E', '#BDB76B', '#6B8E23', '#4682B4', '#708090']
    markers = ['o', 's', '^', 'D', 'v', '<']

    for d, c, m in zip(dists, colors, markers):
        idx = np.searchsorted(x_km, d)
        tau_str = f'{tau_days[idx]:.0f}' if tau_days[idx] < 1000 else f'{tau_days[idx]/365:.1f}y'
        ax.semilogx(t_years, C_active[idx, :], color=c, linewidth=2,
                     marker=m, markevery=80, markersize=6,
                     label=f'{d} km (tau={tau_str}d)')
        # Steady state line
        ax.axhline(C_ss[idx], color=c, linestyle=':', alpha=0.4, linewidth=1)

    ax.axvline(1, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.text(1.05, ax.get_ylim()[1]*0.95, '1 year', fontsize=8, color='gray')

    ax.set_xlabel('Time (years, log scale)', fontsize=11)
    ax.set_ylabel('Active layer Cd (mg/kg)', fontsize=11)
    ax.set_title('Approach to steady state at selected distances',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, framealpha=0.9, ncol=2)
    ax.grid(True, alpha=0.3, which='both')

    # ── Right panel: spatial profiles at different times ──
    ax = axes[1]
    times = [0.08, 0.25, 0.5, 1, 10]  # years
    time_colors = ['#FFA07A', '#F08080', '#CD5C5C', '#DC143C', '#8B0000']
    time_labels = ['1 month', '3 months', '6 months', '1 year', '10+ years (SS)']

    idx_ss = -1  # steady state
    ax.plot(x_km, C_ss, '-', color='#333', linewidth=2.5,
            label='Steady state', zorder=5)

    for ti, tc, tl in zip(times, time_colors, time_labels):
        idx_t = np.searchsorted(t_years, ti)
        if idx_t < len(t_years):
            ax.plot(x_km, C_active[:, idx_t], '--', color=tc, linewidth=1.5,
                    label=tl, alpha=0.8)

    ax.set_xlabel('Distance from source (km)', fontsize=11)
    ax.set_ylabel('Active layer Cd (mg/kg)', fontsize=11)
    ax.set_title('Spatial profile evolving over time',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # ── Annotate time constants along river ──
    ax_tau = axes[0].twinx()
    tau_plot = np.clip(tau_days, 1, 365)
    ax_tau.plot(x_km, tau_plot, '--', color='gray', alpha=0.4, linewidth=1.5)
    ax_tau.set_ylabel('Response time (days)', fontsize=9, color='gray')
    ax_tau.set_yscale('log')
    ax_tau.set_ylim(1, 365)

    fig.suptitle('Time-dependent bed Cd accumulation',
                 fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'[OK] Time evolution -> {save_path}')
    plt.show()


# ====================================================================
# Plot 4: Cumulative Cd inventory over 10/20/50 years
# ====================================================================

def plot_cumulative_cd(steady_result, time_result, sampling_depth=0.50,
                        save_path=None):
    """
    Cumulative Cd mass in top `sampling_depth` m of sediment.

    After the active layer reaches steady state, Cd is buried into
    deeper sediment. This plot shows total Cd per unit area accumulated
    in the top `sampling_depth` of sediment over decadal timescales.
    """
    x_km = steady_result['x_km']
    J_sed = steady_result['J_sed_total']
    J_Cd = steady_result['J_Cd_total']
    C_ss = steady_result['C_bed']

    rho_bulk = 1600  # kg/m3
    M_depth = rho_bulk * sampling_depth  # kg/m2
    J_out = J_sed + J_BG

    # Time to fill the top `sampling_depth` with new sediment
    t_fill_years = M_depth / (J_out * 365.25 * 24 * 3600)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # ── Left: Cd mass per unit area (g/m2) at 10/20/50 years ──
    ax = axes[0]
    decades = [10, 20, 50]
    dec_colors = ['#FF8C00', '#DC143C', '#8B0000']

    for yr, c in zip(decades, dec_colors):
        # Total Cd deposited over `yr` years: J_Cd * time
        sec = yr * 365.25 * 24 * 3600

        # Cd that stays in top `sampling_depth`:
        # If t_fill > yr: all deposited Cd stays within the sampled depth
        # If t_fill < yr: once filled, Cd burial rate = J_out * C_ss
        Cd_in_top = np.where(
            t_fill_years > yr,
            J_Cd * sec,  # all stays
            C_ss * M_depth + J_Cd * sec * 0  # saturated at C_ss * M_depth
        )
        # Better: use the exact mass balance
        Cd_total_deposited = J_Cd * sec  # total Cd that entered bed
        sed_total_deposited = J_out * sec  # total sediment that entered bed

        # Cd in top M_depth of sediment:
        # If sed_deposited <= M_depth: all Cd is in top layer
        # If sed_deposited > M_depth: excess Cd is below, top is at C_ss
        Cd_top = np.where(
            sed_total_deposited <= M_depth,
            Cd_total_deposited,
            C_ss * M_depth  # top layer saturated
        )
        Cd_top_g_m2 = Cd_top / 1000  # mg/m2 -> g/m2

        ax.plot(x_km, Cd_top_g_m2, '-', color=c, linewidth=2,
                label=f'{yr} years')

    ax.set_xlabel('Distance from source (km)', fontsize=11)
    ax.set_ylabel('Cd inventory in top 50 cm (g/m2)', fontsize=11)
    ax.set_title('Cumulative Cd mass over time', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # ── Right: Sediment column cross-section showing depth of contamination ──
    ax = axes[1]
    decades_yr = [10, 20, 50]

    for yr in decades_yr:
        sec = yr * 365.25 * 24 * 3600
        sed_depth_cm = J_out * sec / rho_bulk * 100  # cm of new sediment

        ax.plot(x_km, sed_depth_cm, linewidth=2,
                label=f'{yr} years ({np.max(sed_depth_cm):.0f} cm max)')

    ax.axhline(5, color='gray', linestyle=':', alpha=0.5)
    ax.text(105, 5, 'Active layer (5 cm)', fontsize=8, color='gray', va='center')

    ax.set_xlabel('Distance from source (km)', fontsize=11)
    ax.set_ylabel('Sediment accumulated (cm)', fontsize=11)
    ax.set_title('Depth of new sediment deposited',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-2, 110)
    ax.invert_yaxis()

    fig.suptitle(f'Long-term Cd accumulation (top {sampling_depth*100:.0f} cm)',
                 fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'[OK] Cumulative Cd -> {save_path}')
    plt.show()


# ====================================================================
# Scenario comparison: sandy vs clayey riverbed
# ====================================================================

def plot_scenario_comparison(save_path=None):
    """
    Compare steady-state Cd distribution under different riverbed regimes.

    Sandy river:  high background sediment flux, low background Cd
    Clayey river: low background sediment flux, high background Cd
    """
    x = np.linspace(0, RIVER_LEN, 1000)

    scenarios = [
        dict(name='Baseline (default)',
             j_bg=8e-6, cd_bg=0.2, ls='-',  color='#333', lw=2.0),
        dict(name='Sandy riverbed',
             j_bg=3e-5, cd_bg=0.1, ls='--', color='#D2691E', lw=2.0),
        dict(name='Clayey riverbed',
             j_bg=1e-6, cd_bg=0.4, ls=':',  color='#8B0000', lw=2.5),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    for sc in scenarios:
        local_classes = [dict(c) for c in GRAIN_CLASSES]
        res = compute_profile(x, local_classes, TSS0, CD_ROCK,
                              FLOW_VEL, MEAN_DEPTH,
                              sc['j_bg'], sc['cd_bg'])

        x_km = res['x_km']
        C_bed = res['C_bed']

        ax1.plot(x_km, C_bed, linestyle=sc['ls'], color=sc['color'],
                 linewidth=sc['lw'], label=sc['name'])

        J_sed_g = res['J_sed_total'] * 1000
        ax2.plot(x_km, J_sed_g, linestyle=sc['ls'], color=sc['color'],
                 linewidth=sc['lw'], label=sc['name'])

        peak_idx = np.argmax(C_bed)
        print(f'  {sc["name"]:20s}: peak C_bed={C_bed[peak_idx]:.2f}'
              f' @ {x_km[peak_idx]:.0f} km'
              f'  (J_bg={sc["j_bg"]:.1e}, Cd_bg={sc["cd_bg"]:.1f})')

    ax1.axhline(0.2, color='gray', linestyle=':', alpha=0.4)
    ax1.text(102, 0.2, 'Bg=0.2', fontsize=7, color='gray', va='center')
    ax1.set_xlabel('Distance from source (km)', fontsize=11)
    ax1.set_ylabel('Bed Cd concentration (mg/kg)', fontsize=11)
    ax1.set_title('Steady-state Cd profile by river type',
                  fontsize=12, fontweight='bold')
    ax1.set_xlim(-2, 105)
    ax1.legend(fontsize=9, framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    ax2.set_xlabel('Distance from source (km)', fontsize=11)
    ax2.set_ylabel('Sediment flux (g/(m2.s))', fontsize=11)
    ax2.set_title('Sediment deposition by river type',
                  fontsize=12, fontweight='bold')
    ax2.set_xlim(-2, 105)
    ax2.legend(fontsize=9, framealpha=0.9)
    ax2.grid(True, alpha=0.3)

    ax1.text(0.5, 0.02,
             'Sandy: high bg sediment dilutes Cd signal\n'
             'Clayey: low bg sediment, less dilution, higher peak',
             transform=ax1.transAxes, fontsize=9, color='#555',
             va='bottom', ha='center',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF8DC',
                       alpha=0.8))

    fig.suptitle('Riverbed type controls Cd distribution',
                 fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f'[OK] Scenario comparison -> {save_path}')
    plt.show()


# ====================================================================
# Main
# ====================================================================

if __name__ == '__main__':
    # ---- Spatial grid ----
    x = np.linspace(0, RIVER_LEN, 1000)

    # ---- Run model ----
    result = compute_profile(
        x, GRAIN_CLASSES, TSS0, CD_ROCK,
        FLOW_VEL, MEAN_DEPTH, J_BG, CD_BG,
    )

    # ---- Print summary ----
    print('=' * 60)
    print('River Sediment Cd Model -- Summary')
    print('=' * 60)
    print(f'River length:  {RIVER_LEN/1000:.0f} km')
    print(f'Velocity:      {FLOW_VEL:.1f} m/s')
    print(f'Depth:         {MEAN_DEPTH:.1f} m')
    print(f'Source TSS:    {TSS0:.0f} mg/L')
    print(f'Waste rock Cd: {CD_ROCK:.1f} mg/kg')
    print(f'Background Cd: {CD_BG:.1f} mg/kg')
    print(f'Bg sed flux:   {J_BG:.1e} kg/(m2.s)')
    print('-' * 60)

    idx_samples = np.searchsorted(x / 1000, [0, 5, 10, 20, 50, 80, 100])
    print(f'{"Dist(km)":>10} {"C_bed(mg/kg)":>14} {"C_dep(mg/kg)":>14} {"J_sed(g/m2s)":>14}')
    print('-' * 60)
    for i in idx_samples:
        print(f'{result["x_km"][i]:>10.1f} {result["C_bed"][i]:>14.3f} '
              f'{result["C_dep"][i]:>14.3f} '
              f'{result["J_sed_total"][i] * 1000:>14.4f}')

    # ---- Grain class contributions ----
    print('\nGrain class initial contributions:')
    for i, c in enumerate(GRAIN_CLASSES):
        w_s = stokes_w(c['d_um'] * 1e-6)
        frac_J = c['f_src'] * w_s / sum(
            cc['f_src'] * stokes_w(cc['d_um'] * 1e-6) for cc in GRAIN_CLASSES
        )
        print(f'  {c["name"]:6s}: d={c["d_um"]:3d} um  '
              f'w_s={w_s:.2e} m/s  EF={c["EF"]:3.1f}  '
              f'Cd_p={CD_ROCK * c["EF"]:.1f} mg/kg  '
              f'sed_flux_contrib={frac_J*100:.1f}%')

    print(f'\nModel mechanism:')
    print(f'  Near-source dominated by coarse particles (low Cd)')
    print(f'  Mid-reach enriched by fine particles (high Cd)')
    print(f'  Distal reaches diluted by background sedimentation')
    print(f'')
    print(f'  This produces a characteristic peak-shift:')
    print(f'  maximum Cd concentration occurs downstream of the source,')
    print(f'  NOT at the source itself (fining-driven enrichment).')

    # ---- Create output directory ----
    img_dir = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
    os.makedirs(img_dir, exist_ok=True)

    # ---- Generate plots ----
    plot_concentration_profile(
        result,
        save_path=os.path.join(img_dir, '01_cd_distribution.png'),
    )
    plot_cross_section(
        save_path=os.path.join(img_dir, '01_cross_section.png'),
    )

    # ---- Time-dependent evolution ----
    print('\n' + '=' * 60)
    print('Time-dependent analysis')
    print('=' * 60)

    time_result = compute_time_evolution(result, max_years=50)

    # Print time constants
    print(f'{"Dist(km)":>10} {"tau(days)":>12} {"C_ss(mg/kg)":>14}')
    print('-' * 40)
    for d in [0, 3, 5, 10, 20, 50, 100]:
        idx = np.searchsorted(time_result['x_km'], d)
        tau = time_result['tau_days'][idx]
        tau_str = f'{tau:.0f} d' if tau < 365 else f'{tau/365:.1f} yr'
        print(f'{d:>10.0f} {tau_str:>12} {time_result["C_ss"][idx]:>14.3f}')

    plot_time_evolution(
        result, time_result,
        save_path=os.path.join(img_dir, '01_time_evolution.png'),
    )
    plot_cumulative_cd(
        result, time_result,
        save_path=os.path.join(img_dir, '01_cumulative_cd.png'),
    )

    # ---- Scenario comparison ----
    print('\n' + '=' * 60)
    print('Scenario comparison: sandy vs clayey riverbed')
    print('=' * 60)
    plot_scenario_comparison(
        save_path=os.path.join(img_dir, '01_scenario_comparison.png'),
    )
