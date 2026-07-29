"""
TCE / PCE 地下水羽流 1D 对流-弥散模型

1D Advection-Dispersion Equation (ADE):
    ∂C/∂t = D · ∂²C/∂x² - v · ∂C/∂x

Ogata-Banks 解析解（半无限域，x=0 处连续注入浓度 C₀，初始 C=0）:
    C(x, t) / C₀ = ½ · erfc( (x - v·t) / (2·√(D·t)) )

参数注释：
    [S] = standard/regulation · [L] = literature typical range
    [E] = estimated · [C] = calculated · [A] = assumed

物理参数参考（地下水 TCE/PCE 常见污染场景）:
    - 渗透流速 v:  0.01-1 m/day (砂质含水层典型 0.1 m/day) [L]
    - 弥散系数 D:  0.01-1 m²/day (纵向弥散度 1-10 m × v, 这里取 0.1) [L]
    - 注入浓度 C₀: 取决于泄漏源, 数千-数万 μg/L (Woburn Well G TCE ~267 ppb = 267 μg/L) [L]

监管限值:
    - 美国 EPA MCL (1987): TCE 5 μg/L, PCE 5 μg/L [S]
    - 中国 GB/T 14848-2017 III 类: TCE 70 μg/L, PCE 40 μg/L [S]

Usage:
    python models/groundwater_tce_pce.py
"""

import os
import numpy as np
from scipy.special import erfc
import matplotlib.pyplot as plt

# 全局字体（GBK console 友好，遵循 CLAUDE.md）
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120


class GroundwaterTCEPce:
    """TCE/PCE 地下水 1D 羽流 — Ogata-Banks 解析解.

    Parameters:
        v   : 地下水流速 (m/day)，[L] 砂质含水层典型 0.1 m/day
        D   : 弥散系数 (m²/day)，[L] 纵向弥散度 1-10 m × v, 典型 0.1 m²/day
        C0  : 注入源浓度 (μg/L)，泄漏处浓度，取决于源强
    """

    # 监管限值 (μg/L)
    EPA_MCL_TCE = 5.0         # 美国 EPA MCL, 1987
    EPA_MCL_PCE = 5.0
    CN_III_TCE = 70.0         # 中国 GB/T 14848-2017 III 类
    CN_III_PCE = 40.0

    def __init__(self, v=0.1, D=0.1, C0=1000.0):
        self.v = v
        self.D = D
        self.C0 = C0

    # ── 核心：Ogata-Banks 解析解 ─────────────────────────────────
    def concentration(self, x, t):
        """t 时刻 x 距离处的浓度 (μg/L).

        C(x, t) / C₀ = ½ · erfc( (x - v·t) / (2·√(D·t)) )

        Args:
            x : 距注入源的距离 (m), 标量或数组
            t : 自注入起的时间 (day)
        Returns:
            浓度 (μg/L)
        """
        x = np.asarray(x, dtype=float)
        t = np.asarray(t, dtype=float)
        # 避免 t=0 除零
        t_safe = np.where(t == 0, 1e-12, t)
        sigma = 2 * np.sqrt(self.D * t_safe)
        return self.C0 * 0.5 * erfc((x - self.v * t) / sigma)

    # ── 羽流前锋距离 ───────────────────────────────────────────
    def front_distance(self, t):
        """对流前锋距离 (m): v·t，即浓度达到 C₀/2 的位置."""
        return self.v * t

    # ── 达 MCL 距离 ───────────────────────────────────────────
    def distance_to_MCL(self, t, MCL=None):
        """t 时刻, 浓度等于 MCL 5 μg/L 的距离 (m) — 即羽流污染羽边缘.

        用数值搜索: 在 x ∈ [0, v·t + 5σ] 区间找 C(x,t)=MCL 的位置.
        """
        if MCL is None:
            MCL = self.EPA_MCL_TCE
        x_max = self.v * t + 10 * np.sqrt(self.D * max(t, 1))
        xs = np.linspace(0, x_max, 5000)
        Cs = self.concentration(xs, t)
        # 找最后一个 C >= MCL 的位置（下降沿）
        idx = np.where(Cs >= MCL)[0]
        if len(idx) == 0:
            return 0.0
        return xs[idx[-1]]

    # ── 多时间羽流曲线 ─────────────────────────────────────────
    def plume_curves(self, times, x_max=300):
        """返回多个时间的浓度-距离曲线.

        Args:
            times : list of t (day)
            x_max : 距离范围上限 (m)
        Returns:
            xs (m), dict {t: C(x)} (μg/L)
        """
        xs = np.linspace(0, x_max, 500)
        curves = {}
        for t in times:
            curves[t] = self.concentration(xs, t)
        return xs, curves


# ====================================================================
# Self-test & demo figure (run as standalone)
# ====================================================================

def main():
    # 默认参数：典型砂质含水层，干洗店泄漏 C₀=1000 μg/L
    model = GroundwaterTCEPce(v=0.1, D=0.1, C0=1000.0)

    times = [30, 180, 365, 730, 1825]   # 1 月, 6 月, 1 年, 2 年, 5 年
    xs, curves = model.plume_curves(times, x_max=300)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    for t, c in zip(times, colors):
        label = f'{t} 天 ({t//30 if t < 365 else t//365} {"月" if t < 365 else "年"})'
        ax.plot(xs, curves[t], color=c, lw=2, label=label)

    # 监管线
    ax.axhline(model.EPA_MCL_TCE, color='red', ls='--', lw=1.5,
               label=f'美国 EPA MCL = {model.EPA_MCL_TCE} μg/L')
    ax.axhline(model.CN_III_TCE, color='darkorange', ls=':', lw=1.5,
               label=f'中国 GB/T 14848 III 类 = {model.CN_III_TCE} μg/L')

    # 关键数字标注：5 年时污染羽到哪
    front_5y = model.front_distance(1825)
    mcl_5y = model.distance_to_MCL(1825, MCL=model.EPA_MCL_TCE)
    ax.annotate(f'5 年时 v·t = {front_5y:.0f} m\n(对流前锋)',
                xy=(front_5y, model.C0/2), xytext=(front_5y-80, model.C0*0.55),
                fontsize=10, color='#9467bd',
                arrowprops=dict(arrowstyle='->', color='#9467bd'))
    ax.annotate(f'5 年时 EPA MCL 边界 ≈ {mcl_5y:.0f} m',
                xy=(mcl_5y, model.EPA_MCL_TCE), xytext=(mcl_5y+20, model.EPA_MCL_TCE*3),
                fontsize=10, color='red',
                arrowprops=dict(arrowstyle='->', color='red'))

    ax.set_xlabel('距注入源的距离 (m)', fontsize=12)
    ax.set_ylabel('TCE/PCE 浓度 (μg/L)', fontsize=12)
    ax.set_title('1D 地下水羽流：连续泄漏 5 年后浓度-距离分布\n'
                 f'参数 v={model.v} m/day, D={model.D} m²/day, C0={model.C0} μg/L',
                 fontsize=13)
    ax.set_yscale('log')
    ax.set_ylim(1, model.C0 * 2)
    ax.set_xlim(0, 300)
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(loc='upper right', fontsize=10)

    # 输出
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'articles', 'env')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'fig_env_18_plume.png')
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    print(f'已保存: {out_path}')
    print()
    print('=== 关键数字 ===')
    for t in times:
        mcl = model.distance_to_MCL(t, model.EPA_MCL_TCE)
        cn = model.distance_to_MCL(t, model.CN_III_TCE)
        print(f'  t={t:4d} 天: 对流前锋={model.front_distance(t):5.1f} m | '
              f'EPA MCL 边界={mcl:5.1f} m | GB/T III 类边界={cn:5.1f} m')


if __name__ == '__main__':
    main()
