"""
Spatially varying riverbed scenario.
  0-20 km:  sandy (high background sediment flux, low metal bg)
  20-50 km: sand-clay 1:1 mix
  50-100 km: clayey (low background sediment flux, high metal bg)

Reuses settling physics from river_sediment_cd.py.
"""

import numpy as np
import matplotlib.pyplot as plt
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from river_sediment_cd import GRAIN_CLASSES, stokes_w, RIVER_LEN, FLOW_VEL, MEAN_DEPTH, TSS0

# ====================================================================
# Metal parameters
# ====================================================================
METALS = [
    dict(name='Cd', source=1.0,  bg=0.2,   ef=[12,  8, 3, 1.5, 0.5], color='#DC143C'),
    dict(name='Pb', source=200,  bg=25,    ef=[18, 12, 5,   2, 0.5], color='#1565C0'),
    dict(name='As', source=50,   bg=8,     ef=[8,   6, 3, 1.5, 0.5], color='#2E7D32'),
]

# Riverbed type background parameters
BED_SANDY = dict(j_bg=3e-5, c_bg_factor=0.5)   # high sed flux, low metal bg
BED_CLAY = dict(j_bg=1e-6, c_bg_factor=2.0)    # low sed flux, high metal bg
BED_MIX = dict(j_bg=(3e-5 + 1e-6) / 2., c_bg_factor=(0.5 + 2.0) / 2.)

# ====================================================================
# Spatial profile (same physical transport, locally varying bg)
# ====================================================================
def spatial_profile(x_m, classes, tss0, metal_source, metal_bg_ref, v, h):
    n = len(x_m)

    # Settling velocities and initial conditions
    S0 = tss0 / 1000.0
    for c in classes:
        d_m = c['d_um'] * 1e-6
        c['w_s'] = stokes_w(d_m)
        c['S0'] = S0 * c['f_src']
        c['C_p'] = metal_source * c['EF']
        c['alpha'] = c['w_s'] / (h * v)

    # Transport (independent of local bed)
    n_cls = len(classes)
    S = np.zeros((n_cls, n))
    J_sed = np.zeros((n_cls, n))
    J_C = np.zeros((n_cls, n))
    for i, c in enumerate(classes):
        S[i, :] = c['S0'] * np.exp(-c['alpha'] * x_m)
        J_sed[i, :] = c['w_s'] * S[i, :]
        J_C[i, :] = c['w_s'] * S[i, :] * c['C_p']

    J_sed_total = np.sum(J_sed, axis=0)
    J_C_total = np.sum(J_C, axis=0)

    # Spatially varying background (piecewise)
    x_km = x_m / 1000.0
    j_bg = np.select(
        [x_km < 20, x_km < 50, x_km >= 50],
        [BED_SANDY['j_bg'], BED_MIX['j_bg'], BED_CLAY['j_bg']],
    )
    c_bg_factor = np.select(
        [x_km < 20, x_km < 50, x_km >= 50],
        [BED_SANDY['c_bg_factor'], BED_MIX['c_bg_factor'], BED_CLAY['c_bg_factor']],
    )
    c_bg = metal_bg_ref * c_bg_factor

    C_bed = (J_C_total + c_bg * j_bg) / (J_sed_total + j_bg)

    return dict(C_bed=C_bed, x_km=x_km, j_bg=j_bg, c_bg=c_bg,
                J_sed_total=J_sed_total, J_C_total=J_C_total)


# ====================================================================
# Also keep constant-scenario references for comparison
# ====================================================================
from river_sediment_cd import compute_profile as compute_constant

def constant_result(classes, source, c_bg, j_bg):
    x = np.linspace(0, RIVER_LEN, 1000)
    return compute_constant(x, classes, TSS0, source, FLOW_VEL, MEAN_DEPTH, j_bg, c_bg)

# ====================================================================
# Run
# ====================================================================
x = np.linspace(0, RIVER_LEN, 2000)  # finer grid for smoother transitions
results_spatial = {}
results_sandy = {}
results_clay = {}

for m in METALS:
    classes = [dict(c, EF=ef) for c, ef in zip(GRAIN_CLASSES, m['ef'])]
    results_spatial[m['name']] = spatial_profile(
        x, classes, TSS0, m['source'], m['bg'], FLOW_VEL, MEAN_DEPTH)

for m in METALS:
    classes = [dict(c, EF=ef) for c, ef in zip(GRAIN_CLASSES, m['ef'])]
    results_sandy[m['name']] = constant_result(classes, m['source'],
                                                m['bg'] * BED_SANDY['c_bg_factor'],
                                                BED_SANDY['j_bg'])
    results_clay[m['name']] = constant_result(classes, m['source'],
                                               m['bg'] * BED_CLAY['c_bg_factor'],
                                               BED_CLAY['j_bg'])

# ====================================================================
# Print summary
# ====================================================================
print('=' * 75)
print('Spatial riverbed scenario: 0-20 km sandy | 20-50 km mix | 50-100 km clayey')
print('=' * 75)

for m in METALS:
    r = results_spatial[m['name']]
    pi = np.argmax(r['C_bed'])
    pk_val = r['C_bed'][pi]
    pk_km = r['x_km'][pi]

    i20 = np.searchsorted(r['x_km'], 20)
    i50 = np.searchsorted(r['x_km'], 50)
    v20 = r['C_bed'][i20]
    v50 = r['C_bed'][i50]
    v100 = r['C_bed'][-1]

    # Local peaks in each segment
    seg1 = r['C_bed'][:i20]
    seg2 = r['C_bed'][i20:i50]
    seg3 = r['C_bed'][i50:]
    p1 = np.max(seg1) if len(seg1) else 0
    p2 = np.max(seg2) if len(seg2) else 0
    p3 = np.max(seg3) if len(seg3) else 0
    p1_km = r['x_km'][np.argmax(seg1)] if len(seg1) else 0

    print(f'\n{"─" * 75}')
    print(f'  {m["name"]} (source={m["source"]} mg/kg)')
    print(f'  {"─" * 75}')
    print(f'  Global peak:      {pk_val:>8.2f} mg/kg @ {pk_km:>3.0f} km')
    print(f'  Sandy seg peak:   {p1:>8.2f} mg/kg @ {p1_km:>3.0f} km')
    print(f'  At transition 20: {v20:>8.2f} mg/kg')
    print(f'  Mix seg (20-50):  local max {p2:>8.2f} mg/kg')
    print(f'  At 50 km:         {v50:>8.2f} mg/kg')
    print(f'  Clay seg (50-100): local max {p3:>8.2f} mg/kg')
    print(f'  @ 100 km:         {v100:>8.2f} mg/kg')

    # Compare with constant scenarios
    rs = results_sandy[m['name']]
    rc = results_clay[m['name']]
    print(f'  vs constant sandy: peak {np.max(rs["C_bed"]):.2f} @ {rs["x_km"][np.argmax(rs["C_bed"])]:.0f} km')
    print(f'  vs constant clay:  peak {np.max(rc["C_bed"]):.2f} @ {rc["x_km"][np.argmax(rc["C_bed"])]:.0f} km')

# ====================================================================
# Plot: 2 panels (Cd top, Pb+As bottom)
# ====================================================================
fig, (ax_cd, ax_pb) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
fig.subplots_adjust(hspace=0.1)

SEGMENTS = [
    (0, 20, '#D2691E', 'Sandy\n0-20 km'),
    (20, 50, '#BDB76B', 'Mix\n20-50 km'),
    (50, 100, '#8B0000', 'Clayey\n50-100 km'),
]

for ax in [ax_cd, ax_pb]:
    for x0, x1, color, label in SEGMENTS:
        ax.axvspan(x0, x1, alpha=0.08, color=color)
        if ax == ax_cd:
            ax.text((x0 + x1) / 2, ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 0.95,
                    label, fontsize=8, ha='center', va='top',
                    color='#666', fontweight='bold')
    ax.set_xlim(-2, 110)

for m in METALS:
    r = results_spatial[m['name']]
    pi = np.argmax(r['C_bed'])
    ax = ax_cd if m['name'] == 'Cd' else ax_pb

    # Main curve
    ax.plot(r['x_km'], r['C_bed'], color=m['color'], linewidth=2.5, zorder=5,
            label=f'{m["name"]} (spatial)')
    ax.plot(r['x_km'][::30], r['C_bed'][::30], m.get('marker', 'o'), color=m['color'],
            markersize=4, markerfacecolor='white', zorder=6)

    # Annotate peaks
    if m['name'] == 'Cd':
        ax.annotate(f'Peak {r["C_bed"][pi]:.2f}\n@ {r["x_km"][pi]:.0f} km',
                    xy=(r['x_km'][pi], r['C_bed'][pi]),
                    xytext=(r['x_km'][pi] + 12, r['C_bed'][pi] * 0.75),
                    arrowprops=dict(arrowstyle='->', color=m['color'], lw=1.2),
                    fontsize=9, color=m['color'], fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                              edgecolor=m['color'], alpha=0.85))

    # Reference constant scenarios (dashed)
    rs = results_sandy[m['name']]
    rc = results_clay[m['name']]

    if m['name'] == 'Cd':
        ax.plot(rs['x_km'], rs['C_bed'], '--', color=m['color'], linewidth=0.8, alpha=0.35,
                label='constant sandy')
        ax.plot(rc['x_km'], rc['C_bed'], ':', color=m['color'], linewidth=0.8, alpha=0.35,
                label='constant clayey')
    else:
        ax.plot(rs['x_km'], rs['C_bed'], '--', color=m['color'], linewidth=0.8, alpha=0.35)
        ax.plot(rc['x_km'], rc['C_bed'], ':', color=m['color'], linewidth=0.8, alpha=0.35)

    # Segment boundary lines
    for xx in [20, 50]:
        ax.axvline(xx, color='gray', linestyle='--', linewidth=0.6, alpha=0.4)

    if m['name'] == 'Cd':
        ax.annotate('20 km boundary', xy=(20, ax.get_ylim()[1] * 0.9),
                    fontsize=7, color='gray', ha='center', alpha=0.6)
        ax.annotate('50 km boundary', xy=(50, ax.get_ylim()[1] * 0.9),
                    fontsize=7, color='gray', ha='center', alpha=0.6)

    ax.set_ylabel(f'{m["name"]} concentration (mg/kg)', fontsize=11)
    ax.grid(True, alpha=0.3)

    legend = ax.legend(loc='upper right', fontsize=8, framealpha=0.9,
                       ncol=2 if m['name'] == 'Cd' else 1)

ax_cd.set_title('Spatially varying riverbed: multi-metal comparison',
                fontsize=14, fontweight='bold', pad=10)
ax_pb.set_xlabel('Distance from source (km)', fontsize=11)

# ── Bottom annotation: j_bg and c_bg info ──
ax_pb.text(0.02, 0.02,
    'Background params:  sandy (J=3e-5, c_bg=0.5x ref)  |  mix (J=1.55e-5, c_bg=1.25x ref)  |  '
    'clayey (J=1e-6, c_bg=2x ref)',
    transform=ax_pb.transAxes, fontsize=7, color='#555', va='bottom',
    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

plt.tight_layout()

# ── Save ──
img_dir = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(img_dir, exist_ok=True)
save_path = os.path.join(img_dir, 'spatial_riverbed_comparison.png')
fig.savefig(save_path, dpi=150, bbox_inches='tight')
print(f'\n[OK] -> {save_path}')
plt.show()
