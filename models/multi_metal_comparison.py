"""
Multi-metal river sediment comparison: Cd, Pb, As.

Reuses the physical model from river_sediment_cd.py.
Run: python models/multi_metal_comparison.py
"""

import numpy as np
import matplotlib.pyplot as plt
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
import river_sediment_cd as base

# ====================================================================
# Metal-specific parameters
# ====================================================================
# EF order: [Clay, FSilt, CSilt, VFSand, FSand] — matches GRAIN_CLASSES
# EF values are conceptual estimates (adsorption affinity to fine particles):
#   Cd: baseline from original model (Kd ~10^4-10^5)
#   Pb: stronger particle affinity (Kd ~10^5-10^6) → higher EF in fines
#   As: oxyanion (H2AsO4-/HAsO4 2-), moderate enrichment, Fe/Mn oxide association
METALS = [
    dict(name='Cd', source=1.0,  bg=0.2,   ef=[12,   8,  3, 1.5, 0.5],
         color='#DC143C', marker='o', ls='-',  panels='separate'),
    dict(name='Pb', source=200,  bg=25,    ef=[18,  12,  5,   2, 0.5],
         color='#1565C0', marker='s', ls='--', panels='shared'),
    dict(name='As', source=50,   bg=8,     ef=[8,    6,  3, 1.5, 0.5],
         color='#2E7D32', marker='^', ls=':',  panels='shared'),
]

X = np.linspace(0, base.RIVER_LEN, 1000)

# ====================================================================
# Run model for all metals
# ====================================================================
results = {}
for m in METALS:
    classes = []
    for c, ef in zip(base.GRAIN_CLASSES, m['ef']):
        cls = dict(c)
        cls['EF'] = ef
        classes.append(cls)

    res = base.compute_profile(
        X, classes, base.TSS0, m['source'],
        base.FLOW_VEL, base.MEAN_DEPTH, base.J_BG, m['bg'],
    )
    results[m['name']] = res

# ====================================================================
# Console summary
# ====================================================================
print('=' * 72)
print('Multi-metal comparison: steady-state bed concentration')
print('=' * 72)
header = f"{'Metal':>5} {'Source':>8} {'Bg':>8} {'Peak':>10} {'@km':>5} {'100km':>8} {'Peak/src':>9} {'Peak/bg':>9}"
print(header)
print('-' * 72)
peak_data = {}
for m in METALS:
    r = results[m['name']]
    peak_i = np.argmax(r['C_bed'])
    peak_data[m['name']] = dict(val=r['C_bed'][peak_i], km=r['x_km'][peak_i])
    print(f"{m['name']:>5} {m['source']:>8.0f} {m['bg']:>8.1f} "
          f"{r['C_bed'][peak_i]:>10.2f} {r['x_km'][peak_i]:>5.0f} "
          f"{r['C_bed'][-1]:>8.2f} "
          f"{r['C_bed'][peak_i] / m['source'] * 100:>8.1f}% "
          f"{r['C_bed'][peak_i] / m['bg']:>8.1f}x")
print()

# Print key differences
cd = peak_data['Cd']
pb = peak_data['Pb']
as_ = peak_data['As']
print('Key differences:')
print(f'  Pb peak = {pb["val"]:.1f} mg/kg @ {pb["km"]:.0f} km '
      f'(source {METALS[1]["source"]} mg/kg)')
print(f'  As peak = {as_["val"]:.1f} mg/kg @ {as_["km"]:.0f} km '
      f'(source {METALS[2]["source"]} mg/kg)')
print(f'  Cd peak = {cd["val"]:.2f} mg/kg @ {cd["km"]:.0f} km '
      f'(source {METALS[0]["source"]} mg/kg)')
print(f'  Pb peak position: {pb["km"]:.0f} km vs Cd {cd["km"]:.0f} km '
      f'(difference: {pb["km"] - cd["km"]:.0f} km)')
print(f'  As peak position: {as_["km"]:.0f} km vs Cd {as_["km"]:.0f} km '
      f'(difference: {as_["km"] - cd["km"]:.0f} km)')
print()

# ====================================================================
# Plot
# ====================================================================
fig, (ax_cd, ax_pbas) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
fig.subplots_adjust(hspace=0.08)

for m in METALS:
    r = results[m['name']]
    x_km = r['x_km']
    C = r['C_bed']
    peak_i = np.argmax(C)
    ax = ax_cd if m['name'] == 'Cd' else ax_pbas

    # Main line
    ax.plot(x_km, C, color=m['color'], linestyle=m['ls'], linewidth=2.2,
            label=f"{m['name']} (source {m['source']} mg/kg)")
    # Markers every 20 km
    ax.plot(x_km[::20], C[::20], m['marker'], color=m['color'],
            markersize=4, alpha=0.5, markerfacecolor='white')

    # Peak annotation
    ax.annotate(
        f"Peak {C[peak_i]:.1f} mg/kg\n@ {x_km[peak_i]:.0f} km",
        xy=(x_km[peak_i], C[peak_i]),
        xytext=(x_km[peak_i] + 12, C[peak_i] * 0.65),
        arrowprops=dict(arrowstyle='->', color=m['color'], lw=1.2),
        fontsize=10, color=m['color'], fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                  edgecolor=m['color'], alpha=0.85),
    )

    # Source reference line
    ax.axhline(m['source'], color=m['color'], linestyle=':', alpha=0.25, linewidth=1)
    ax.text(103, m['source'], f'source {m["source"]:.0f}', fontsize=7,
            color=m['color'], alpha=0.5, va='center')

# ── Top panel: Cd ──
ax_cd.set_ylabel('Cd concentration (mg/kg)', fontsize=11)
ax_cd.set_title('Steady-state bed concentration: Cd, Pb, As comparison',
                fontsize=14, fontweight='bold', pad=10)
ax_cd.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax_cd.grid(True, alpha=0.3)
ax_cd.set_xlim(-2, 110)

# ── Bottom panel: Pb + As ──
ax_pbas.set_xlabel('Distance from source (km)', fontsize=11)
ax_pbas.set_ylabel('Pb / As concentration (mg/kg)', fontsize=11)
ax_pbas.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax_pbas.grid(True, alpha=0.3)
ax_pbas.set_xlim(-2, 110)

# ── Save ──
img_dir = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
os.makedirs(img_dir, exist_ok=True)
save_path = os.path.join(img_dir, 'multi_metal_comparison.png')
fig.savefig(save_path, dpi=150, bbox_inches='tight')
print(f'[OK] Comparison plot -> {save_path}')

plt.show()
