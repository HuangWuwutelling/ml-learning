"""布洛芬 1 阶消除 PK 模型 — 配套文章 21_一片布洛芬被吞之后.md.

本文代码对应文章五个章节的几何学骨架 (2026-08-15 重构: 删了多次给药蓄积整节):

    一    半衰期定义                  — 浓度砍一半要多久
    二    dC/dt = -k·C 的代数        — 为什么衰减规则是 1/2, 不是别的数
    三    4 个时间点的浓度             — 布洛芬验证 (1/2)^n ≈ exp(-k·t)
    四    F / Vd / CL / t½ 分工       — 谁决定起点, 谁决定节奏 + 不同人群 t½
    五    收束                       — 一条链 (t½ ← CL × Vd)

几何规则就一条: 走过 n 个半衰期, 浓度乘 (1/2)^n. 无论 t½ 是 1.5 h (儿童)、
2.0 h (成人)、2.5 h (老年)、3.4 h (肝损), 这条规则都成立, 变的只是 n 的值.

注: 多次给药蓄积函数 (accumulation_ratio / steady_state_cmax /
multiple_dose_curve) 不再被当前文章引用, 保留为通用 PK 工具.

    C(t) = Cmax * exp(-k * (t - Tmax))   # t ≥ Tmax, t 从服药时刻起算
    C(t) = Cmax * (1/2)^n,  n = (t - Tmax) / t½   [几何规则]

    Cmax     = F * Dose / Vd
    k        = ln(2) / t½
    AUC      = F * Dose / CL
    Cmax_ss  = Cmax / (1 - exp(-k * tau))           # 稳态峰值 (R 公式)
    R        = 1 / (1 - (1/2)^n),   n = tau / t½    # 蓄积比

References (every parameter verified by web lookup):
- Wikipedia ibuprofen (F 80-100%, protein binding 98%, t1/2 2-4 h, urine 95%):
  https://en.wikipedia.org/wiki/Ibuprofen
- DrugBank DB01050 (CYP2C9 ~70%, CYP2C8 ~30%, hepatic metabolism):
  https://go.drugbank.com/drugs/DB01050
- PubMed 2868248 (1986 adult PK, CL 3.5-4.5 L/h, Vd 10-12 L, t1/2 ~2 h):
  https://pubmed.ncbi.nlm.nih.gov/2868248/
- PubMed 29668820 (2018 population PK, typical CL 4.0 L/h, Vd ~12 L):
  https://pubmed.ncbi.nlm.nih.gov/29668820/
- PubMed 7213018 (1981 Clin Pharmacokinet review, CL 3.5-4.5 L/h, Vd 10-12 L, ~99% PB):
  https://pubmed.ncbi.nlm.nih.gov/7213018/
- Drugs.com adult dose (200-400 mg q4-6h, max 1200 mg/day OTC, 3200 mg/day Rx):
  https://www.drugs.com/dosage/ibuprofen.html
- St. Louis Children's pediatric dose (5-10 mg/kg q6-8h, max 40 mg/kg/day):
  https://www.stlouischildrens.org/health-resources/dose-calculator/ibuprofen-pediatric-dosing-chart
- Ibuprofen Pharmacology and Therapeutics, PMC8290344 (CYP2C9 ~70%):
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8290344/

Usage:
    >>> m = IbuprofenPK(dose_g=0.4)        # 默认 70 kg 成人, t1/2=2 h
    >>> m.peak_conc_mg_per_L                # 文章 4.1
    32.4
    >>> m.n_half_lives_since_peak(24)       # 文章一, 11.25
    11.25
    >>> m.remaining_fraction(24)            # (1/2)^11.25, 文章一
    0.000411
    >>> m.concentration_at(6)               # 文章 4.2
    6.81
    >>> m.concentration_at(24)              # 文章 4.2
    0.013
    >>> m.accumulation_ratio(6)             # 文章 6.2, 1.143
    1.143
    >>> m.steady_state_cmax(6)              # 文章 6.2, 37.0 mg/L
    37.0
    >>> m.verify_article_anchors()          # 打印文章第一节四个锚点
"""
from __future__ import annotations

import numpy as np


# ── PK 参数 (literature-verified) ─────────────────────────────────
# 这些数字只在 __init__ 时读一次, 之后用 self.x. 修改不在 API 范围.

# 半衰期 (h). 成人典型 2 h, 范围 1.8-2.5 h; Wikipedia 给出 2-4 h 范围.
# 儿童 / 老年 / 肝损场景有各自覆盖.
DEFAULT_HALF_LIFE_H = 2.0

# 口服生物利用度 F. 范围 80-100%; 取 0.85 为典型值 (吸收有首过损失;
# 赖氨酸盐接近 1.0). F 决定 Cmax, 不决定节奏 — 见文章五 5.1.
DEFAULT_BIOAVAILABILITY = 0.85

# 表观分布容积 Vd (L/kg). PubMed 2868248/29668820 给出 70 kg 成人 10-12 L
# 总体, 对应 ~0.15 L/kg. 决定 Cmax 的稀释程度, 不决定节奏 — 见文章五 5.2.
DEFAULT_VD_PER_KG = 0.15

# 总清除率 CL (L/h). 典型 4.0 L/h (范围 3.5-4.5), 健康成人. 与 Vd 共同
# 决定 t½ — 见文章五 5.3: t½ = 0.693 · Vd / CL.
DEFAULT_CL_L_PER_H = 4.0

# 血浆蛋白结合率. 98-99%; 未结合部分 ~1%.
PROTEIN_BINDING = 0.99

# 起效时间 (min). Wikipedia: 解热作用 30 min.
ONSET_MIN = 30

# 临床有效持续时间 (h). OTC 用药 q6-q8h.
DURATION_OF_EFFECT_H = 6.0

# 成人 OTC 用药 (Drugs.com, FDA 标签).
ADULT_OTC_SINGLE_DOSE_G = (0.2, 0.4)         # 单次 200-400 mg
ADULT_OTC_MAX_DAILY_G = 1.2                   # 1200 mg/day
ADULT_OTC_INTERVAL_H = (4.0, 6.0)            # q4-q6h

# 儿童用药 (Drugs.com, St. Louis Children's, 美林说明书).
PEDS_DOSE_MG_PER_KG = (5.0, 10.0)            # 5-10 mg/kg per dose
PEDS_MAX_DAILY_MG_PER_KG = 40.0              # 40 mg/kg/day
PEDS_INTERVAL_H = (6.0, 8.0)                 # q6-q8h

# 急性毒性参考浓度 (仅用于图示). 综述给的下沿是 >100 mg/L, 临床
# 报道跨度 100-700+ mg/L. 单点阈值意义有限, 文章六 6.5 / 图 1 用 100
# 作为参考线下沿. 不作为临床阈值.
TOXICITY_REF_MG_PER_L = 100.0


class IbuprofenPK:
    """布洛芬 1 阶消除 PK 模型 — 对应文章三、四、五、六的几何实现.

    实现一条几何规则: 每过一个半衰期, 浓度乘 1/2. 多个不同 t½ 的场景
    共用这条规则, 变的只是 n 的值.

    默认参数取典型成人 70 kg 体重; 儿童/老年/肝损通过 age_group 调整.
    多次给药场景请用 ``multiple_dose_curve``.

    属性映射:
      F, Vd           — 文章五 5.1, 5.2 (决定起点)
      t½, k           — 文章三 3.1, 五 5.4 (决定节奏)
      Cmax            — 文章四 4.1
      C(t), (1/2)^n   — 文章四 4.2 (两条路径同一件事)
      R, Cmax_ss      — 文章六 6.2
      多次给药叠加     — 文章六 6.3
    """

    def __init__(
        self,
        dose_g: float = 0.4,
        body_weight_kg: float = 70.0,
        half_life_h: float = DEFAULT_HALF_LIFE_H,
        bioavailability: float = DEFAULT_BIOAVAILABILITY,
        vd_per_kg: float = DEFAULT_VD_PER_KG,
        cl_L_per_h: float = DEFAULT_CL_L_PER_H,
        tmax_h: float = 1.5,
        age_group: str = "adult",
    ):
        if dose_g <= 0:
            raise ValueError("dose_g must be > 0")
        if body_weight_kg <= 0:
            raise ValueError("body_weight_kg must be > 0")
        if age_group not in ("adult", "child", "elderly", "hepatic"):
            raise ValueError(f"age_group must be one of adult/child/elderly/hepatic")

        self.dose_g = float(dose_g)
        self.body_weight_kg = float(body_weight_kg)
        self.half_life_h = float(half_life_h)
        self.bioavailability = float(bioavailability)
        self.vd_per_kg = float(vd_per_kg)
        self.cl_L_per_h = float(cl_L_per_h)
        self.tmax_h = float(tmax_h)
        self.age_group = age_group

        # age_group 默认值覆盖: 仅在用户没传具体值时覆盖 (用 DEFAULT 值
        # 作"未指定"信号). 这是为 ergonomics; 实际场景 t½ 也常被显式传.
        if age_group == "child" and vd_per_kg == DEFAULT_VD_PER_KG:
            # 儿童: 体液分数高 → Vd/kg ~0.30 L/kg. 混悬液 F ~0.95.
            # CL/kg ~0.10 L/h/kg, 比成人相对更快.
            self.vd_per_kg = 0.30
            self.bioavailability = 0.95
            self.cl_L_per_h = max(0.10 * body_weight_kg, 1.5)
        elif age_group == "elderly" and vd_per_kg == DEFAULT_VD_PER_KG:
            # 老年: 体脂上升 → Vd 略高; 肝血流降低 → CL 略低.
            self.vd_per_kg = 0.18
            self.cl_L_per_h = 3.2
        elif age_group == "hepatic" and vd_per_kg == DEFAULT_VD_PER_KG:
            # 肝损: Vd 不变, CL 降约一半 (4.0→2.1 L/h; t½ = 0.693·Vd/CL ≈ 3.4 h).
            self.cl_L_per_h = 2.1

        # 派生常数
        self.k_per_h = np.log(2) / self.half_life_h      # 消除速率常数, 文章三 3.1
        self.vd_L = self.vd_per_kg * self.body_weight_kg  # 总 Vd
        # 单剂 AUC (mg·h/L): F * Dose(mg) / CL
        self.auc_single_mg_h_per_L = (
            self.bioavailability * self.dose_g * 1000.0 / self.cl_L_per_h
        )

    # ── 峰值 / 浓度 (文章 四) ────────────────────────────────────
    @property
    def peak_conc_mg_per_L(self) -> float:
        """Cmax (mg/L = μg/mL), 1 阶模型下即 Tmax 处浓度. 对应文章四 4.1.

        Cmax = F * Dose / Vd  (假设瞬时分布; 实际 Tmax=1.5 h).
        """
        return (
            self.bioavailability * self.dose_g * 1000.0 / self.vd_L
        )

    def n_half_lives_since_peak(self, t_h: float) -> float:
        """从 Tmax 起走过几个半衰期. 对应文章二的定义 + 文章四 4.2.

        n = (t − Tmax) / t½

        例: 成人 0.4 g, t_h=24 → n = (24 − 1.5) / 2 = 11.25.
        这是文章第一节的"11.25"几何来源.
        """
        if t_h < self.tmax_h:
            return 0.0
        return (t_h - self.tmax_h) / self.half_life_h

    def remaining_fraction(self, t_h: float) -> float:
        """经过 t_h 小时后, 浓度占峰值的比例. 对应文章一的几何规则.

        ratio(t) = C(t) / Cmax = (1/2)^n,  其中 n = n_half_lives_since_peak(t).

        与 ``concentration_at(t) / peak_conc_mg_per_L`` 数值一致 —
        这是文章四 4.2 "代数式和 (1/2)^n 算出来的数一致" 的代码侧对应.
        """
        return 0.5 ** self.n_half_lives_since_peak(t_h)

    def concentration_at(self, t_h: float) -> float:
        """t 小时后血药浓度 (mg/L, t 从服药时刻起算). 对应文章四 4.2.

        C(t) = Cmax * exp(-k * (t - Tmax)),  t ≥ Tmax.  t < Tmax 时
        按吸收相简化返回 Cmax.

        关注的是文章四 4.2 表里的 4 个时间点:
          t = 1.5 h (Tmax) → 32.4 mg/L
          t = 6 h         → 6.81 mg/L
          t = 12 h        → 0.85 mg/L
          t = 24 h        → 0.013 mg/L

        也可以用 ``remaining_fraction(t) * peak_conc_mg_per_L`` 走
        几何路径 — 两条结果在浮点精度内一致.
        """
        if t_h < self.tmax_h:
            return self.peak_conc_mg_per_L
        elapsed = t_h - self.tmax_h
        return self.peak_conc_mg_per_L * np.exp(-self.k_per_h * elapsed)

    def time_to_below(self, threshold_mg_per_L: float) -> float:
        """返回浓度首次降到 threshold (mg/L) 的时间 (h, 从 t=0 起).

        若 Cmax 已经 < threshold, 返回 0.0 (代表当前即可).
        若消除速率为 0, 返回 inf.
        """
        if self.peak_conc_mg_per_L <= threshold_mg_per_L:
            return 0.0
        if self.k_per_h <= 0:
            return float("inf")
        # From peak: t = Tmax + ln(Cmax/threshold)/k
        t_after_peak = np.log(
            self.peak_conc_mg_per_L / threshold_mg_per_L
        ) / self.k_per_h
        return self.tmax_h + t_after_peak

    def time_to_half(self) -> float:
        """Cmax 降到 50% 的时间 (h). 对应文章二"半衰期定义" 的代码侧.

        半衰期指 Cmax 到 50% 的时间间隔 (从 Tmax 起算).  返回 Tmax + t½.
        """
        return self.tmax_h + self.half_life_h

    # ── 文章节一锚点核验 ──────────────────────────────────────────────
    def verify_article_anchors(self) -> None:
        """打印并断言文章第一节的四个锚点数字, 用于配文代码一致性.

        锚点 (文章一, 表):
          22.5 h   窗口长度 (24 - Tmax)
          2 h      半衰期 (this model)
          11.25    窗口里装了几个半衰期 (n = 22.5 / 2)
          0.0411% 残留比例 ((1/2)^11.25)
        """
        window_h = 24.0 - self.tmax_h
        n = window_h / self.half_life_h
        residual = 0.5 ** n
        print("=== 文章节一锚点核验 ===")
        print(f"  Tmax = {self.tmax_h} h")
        print(f"  窗口长度 = 24 - {self.tmax_h} = {window_h} h        (文章写 22.5)")
        print(f"  t1/2    = {self.half_life_h} h                       (文章写 2)")
        print(f"  n       = {window_h} / {self.half_life_h} = {n}    (文章写 11.25)")
        print(f"  (1/2)^n = {residual:.6f} = {residual*100:.4f}%        (文章写 0.0411%)")
        # 容忍浮点误差
        assert abs(window_h - 22.5) < 0.01, f"窗口长度异常: {window_h}"
        assert abs(n - 11.25) < 0.001, f"n 异常: {n}"
        assert abs(residual - 4.11e-4) < 1e-5, f"残留异常: {residual}"

    # ── 多次给药 (文章 六) ────────────────────────────────────────────
    def steady_state_cmax(self, tau_h: float) -> float:
        """多次给药稳态峰值浓度 (mg/L). 对应文章六 6.2 R 公式.

        Cmax_ss = Cmax / (1 - exp(-k * tau))
                = Cmax / (1 - (1/2)^n),  n = tau / t½

        布洛芬成人 0.4 g q6h:
          n = 6/2 = 3, (1/2)^3 = 12.5%, R = 1.143
          Cmax_ss = 32.4 / 0.875 = 37.0 mg/L  [稳态峰值, 蓄积 14.3%]

        注: 实测 0.4 g q6h 逐剂叠加 (dose 2 = 36.4, dose 3 = 36.9 mg/L),
        与稳态 37.0 mg/L 差 < 2%. 布洛芬 t½ ≪ 给药间隔, R 公式
        是临床可直接用的近似, 不必管瞬时叠加的细节.
        """
        if tau_h <= 0:
            raise ValueError("tau_h must be > 0")
        return self.peak_conc_mg_per_L / (1.0 - np.exp(-self.k_per_h * tau_h))

    def accumulation_ratio(self, tau_h: float) -> float:
        """蓄积比 R = 1 / (1 - (1/2)^n),  n = tau / t½. 对应文章六 6.2.

        R 是稳态峰值相对单剂峰值的倍数, 是文章六核心公式.

        布洛芬成人 t½=2 h 的典型值:
          q4h: n=2,   R = 1.333   (上次残留 25%)
          q6h: n=3,   R = 1.143   (12.5%)   ← 文章六 6.2 / 6.4 主例
          q8h: n=4,   R = 1.067   (6.25%)
          q12h: n=6,  R = 1.016   (1.56%)
          q24h: n=12, R = 1.000   (0.024%)

        对比地高辛 t½=36 h qd: n=0.67, R=2.70   (文章六 6.4)
        """
        return 1.0 / (1.0 - np.exp(-self.k_per_h * tau_h))

    # ── 向量化单剂曲线 ────────────────────────────────────────
    def curve(self, t_max: float = 24.0, n: int = 481) -> tuple[np.ndarray, np.ndarray]:
        """返回 (t_array_h, C_array_mg_per_L) over [0, t_max]. 对应文章图 1 蓝线.

        t 从服药时刻起算, 0 ≤ t < Tmax 时 C = Cmax (吸收相简化),
        t ≥ Tmax 时 C = Cmax * exp(-k * (t - Tmax)). 与 concentration_at()
        时间口径一致.
        """
        t = np.linspace(0.0, float(t_max), int(n))
        c = np.where(
            t < self.tmax_h,
            self.peak_conc_mg_per_L,
            self.peak_conc_mg_per_L * np.exp(-self.k_per_h * (t - self.tmax_h)),
        )
        return t, c

    # ── 多次给药曲线 (文章 六 6.3 瞬时叠加) ─────────────────────────────
    def multiple_dose_curve(
        self,
        doses_g: list[float],
        dose_times_h: list[float],
        t_max: float = 24.0,
        dt: float = 0.05,
    ) -> tuple[np.ndarray, np.ndarray]:
        """多次给药曲线 (叠加 1 阶消除). 对应文章六 6.3.

        doses_g: 各次剂量 (g), 长度 == dose_times_h 长度.
        dose_times_h: 各次给药时间 (h).
        返回 (t_array, C_array) over [0, t_max].

        每次给药: t_dose ≤ t < t_dose + Tmax 时 C = sub_cmax (吸收相),
        t ≥ t_dose + Tmax 时 C = sub_cmax * exp(-k * (t - t_dose - Tmax)).
        与 concentration_at() / curve() 时间口径一致.

        重要: 该方法输出瞬时叠加曲线 (timeline 上每个时刻的实际浓度).
        对布洛芬 q6h 这种 t½ ≪ 给药间隔, 头几次给药的瞬时峰值就
        收敛到稳态峰值附近 (差 < 2%) — 见 ``steady_state_cmax`` 注释.
        真正会瞬时 vs 稳态差距大的是 t½ 接近给药间隔的药 (地高辛).
        """
        if len(doses_g) != len(dose_times_h):
            raise ValueError("doses_g and dose_times_h must have equal length")
        t = np.arange(0.0, t_max + dt, dt)
        c = np.zeros_like(t)
        for d_g, t_dose in zip(doses_g, dose_times_h):
            sub_cmax = (
                self.bioavailability * d_g * 1000.0 / self.vd_L
            )
            elapsed = t - t_dose
            mask_absorption = (elapsed >= 0) & (elapsed < self.tmax_h)
            mask_elimination = elapsed >= self.tmax_h
            c[mask_absorption] += sub_cmax
            c[mask_elimination] += sub_cmax * np.exp(
                -self.k_per_h * (elapsed[mask_elimination] - self.tmax_h)
            )
        return t, c

    # ── 绘图 ──────────────────────────────────────────
    def plot_curve(
        self,
        ax,
        t_max: float = 24.0,
        label: str = None,
        color: str = None,
        linewidth: float = 2.0,
        threshold_color: str = "#888888",
    ):
        """在给定 ax 上画 C(t) 曲线 + 起效参考线. 对应文章图 1."""
        import matplotlib.pyplot as plt
        t, c = self.curve(t_max=t_max)
        if label is None:
            label = (
                f"{self.dose_g:g} g, "
                f"{self.body_weight_kg:g} kg, "
                f"{self.age_group}"
            )
        ax.plot(t, c, label=label, color=color, linewidth=linewidth)
        # 起效浓度参考线 ~10 mg/L — 文章图 1 横向虚线.
        # 经验值, 综述常用, 非临床阈值.
        ax.axhline(10.0, color="#2ca02c", linestyle="--",
                   linewidth=1.0, alpha=0.7,
                   label="退烧起效浓度 ~10 mg/L")
        ax.axhline(self.peak_conc_mg_per_L, color="#ff7f0e",
                   linestyle=":", linewidth=1.0, alpha=0.7)
        ax.axhline(0.0, color="#222222", linewidth=0.8)
        return t, c


# ── 预置场景 (与文章节号一一对应) ────────────────────────────────
#
#   场景函数                   文章节     图 1 线   备注
#   ────────────────────────────────────────────────────────────
#   adult_400mg_single         四 4.2    蓝        文章主曲线
#   adult_q6h_3times_otc       六 6.5    绿        OTC 1.2 g/d
#   adult_overdose_800mg_q6h   六 6.5    红        处方上限 3.2 g/d
#   child_meilin_10mgkg        七 / 五 5.3  —      t½=1.5, Vd/kg=0.30
#   elderly_70yo_400mg         七 / 五 5.3  —      t½=2.5, CL=3.2
#   hepatic_impairment_400mg   七 / 五 5.3  —      t½=3.4, CL=2.1
#
# 几何规则就一条: (1/2)^n.  变的只是 n 的值.


def adult_400mg_single():
    """成人 0.4 g 单次 (70 kg) — 对应文章四 4.2 / 七收束. 图 1 蓝线.

    Cmax ≈ 32.4 mg/L; 24 h 后 ≈ 0.013 mg/L (走完 11.25 个半衰期).
    """
    return IbuprofenPK(
        dose_g=0.4, body_weight_kg=70.0, age_group="adult",
    )


def adult_q6h_3times_otc():
    """成人 0.4 g q6h × 3 次 (24 h 总 1.2 g, OTC 上限) — 对应文章六 6.5 / 六 6.3. 图 1 绿线.

    按 OTC 上限 1.2 g/d 拆 3 次 (0, 6, 12 h). 稳态峰值 ≈ 37 mg/L (R=1.143).
    实测逐剂叠加 (dose 2 = 36.4, dose 3 = 36.9) 与稳态差 < 2% —
    对布洛芬 R 公式可直接当峰值近似用.

    注: 旧版名为 adult_q6h_4times, 1.6 g 略超 OTC 上限, 现按文章节六
    6.5 改名为 _3times_otc, 总剂量对齐 OTC.
    """
    return IbuprofenPK(
        dose_g=0.4, body_weight_kg=70.0, age_group="adult",
    )


def adult_overdose_800mg_q6h():
    """成人 0.8 g q6h × 4 次 (24 h 总 3.2 g, 处方上限) — 对应文章六 6.5. 图 1 红线.

    用于说明处方上限剂量下的浓度. 单剂 Cmax 翻倍到 65 mg/L; q6h 稳态峰值
    ≈ 74 mg/L (文章六 6.5 第二段). 临床警示对比, 不作建议.
    """
    return IbuprofenPK(
        dose_g=0.8, body_weight_kg=70.0, age_group="adult",
    )


def child_meilin_10mgkg():
    """儿童美林 10 mg/kg (15 kg 儿童, 剂量 0.15 g) — 对应文章五 5.3 / 七收束.

    t½ = 1.5 h (儿童代谢稍快); Vd/kg = 0.30 (体液分数高); CL ≈ 1.5 L/h.
    几何规则不变, 11.25 那个数字里的 t½ 用 1.5 代入, n = 22.5/1.5 = 15.
    """
    return IbuprofenPK(
        dose_g=0.15, body_weight_kg=15.0, age_group="child",
        half_life_h=1.5,
    )


def elderly_70yo_400mg():
    """老年人 70 岁 0.4 g (70 kg) — 对应文章五 5.3 / 七收束.

    t½ = 2.5 h (肝血流降低 → CL 降); Vd 略高 (体脂 ↑).
    几何规则不变, 11.25 那个数字里的 t½ 用 2.5 代入, n = 22.5/2.5 = 9.
    """
    return IbuprofenPK(
        dose_g=0.4, body_weight_kg=70.0, age_group="elderly",
        half_life_h=2.5,
    )


def hepatic_impairment_400mg():
    """肝功能不全 0.4 g — 对应文章五 5.3 / 七收束.

    CYP2C9 活性下降 → CL 降约一半 (4.0→2.1 L/h) → t½ 从 2 h 延到约 3.4 h
    (文献: 肝功能受损者 t½ 延至 3.1-3.4 h). Vd 不变 (肝损不改分布).
    几何规则不变, 11.25 那个数字里的 t½ 用 3.4 代入, n = 22.5/3.4 ≈ 6.6, 即
    24 h 后残留 ≈ (1/2)^6.6 ≈ 1%, 远高于健康成人的 0.04%.
    """
    return IbuprofenPK(
        dose_g=0.4, body_weight_kg=70.0, age_group="hepatic",
        half_life_h=3.4,
    )


if __name__ == "__main__":
    # Smoke test
    m = adult_400mg_single()
    print("=== Ibuprofen PK model smoke test ===")
    print(f"Dose: 0.4 g, 70 kg adult")
    print(f"F = {m.bioavailability}, Vd = {m.vd_L:.2f} L, "
          f"CL = {m.cl_L_per_h:.2f} L/h")
    print(f"t1/2 = {m.half_life_h} h, k = {m.k_per_h:.4f} /h")
    print(f"Cmax = {m.peak_conc_mg_per_L:.2f} mg/L (= ug/mL)")
    print(f"AUC  = {m.auc_single_mg_h_per_L:.1f} mg*h/L")
    print()

    # ── 文章节一锚点 (数字一致性核验) ──
    m.verify_article_anchors()
    print()

    # ── 文章节四 4.2 表 (4 个时间点) ──
    print("=== 文章节四 4.2: 4 个时间点浓度 ===")
    print(f"C(1.5) = {m.concentration_at(1.5):.2f} mg/L (Tmax)   (文章 32.4)")
    print(f"C(6)   = {m.concentration_at(6):.2f} mg/L            (文章 6.81)")
    print(f"C(12)  = {m.concentration_at(12):.2f} mg/L            (文章 0.85)")
    print(f"C(24)  = {m.concentration_at(24):.4f} mg/L           (文章 0.013)")
    print()

    # ── 文章节四 4.2: 代数式 vs 几何规则 (1/2)^n 同值验证 ──
    print("=== 文章节四 4.2: exp(-k * t) 与 (1/2)^n 一致性 ===")
    for tt in [6, 12, 24]:
        c_algebraic = m.concentration_at(tt)
        c_geometric = m.remaining_fraction(tt) * m.peak_conc_mg_per_L
        diff = abs(c_algebraic - c_geometric)
        flag = "OK" if diff < 0.01 else "MISMATCH"
        n = m.n_half_lives_since_peak(tt)
        print(f"  t={tt}h, n={n:.4f}:  algebraic={c_algebraic:.4f}, "
              f"geometric={c_geometric:.4f}  [{flag}]")
    print()

    # ── 文章节三 3.1: exp(-k×1) = 1/√2 ≈ 0.707 ──
    c1 = m.peak_conc_mg_per_L * np.exp(-m.k_per_h * 1.0)
    expected_1h = m.peak_conc_mg_per_L / np.sqrt(2)
    print("=== 文章节三 3.1: 每过 1 小时浓度乘 1/sqrt(2) ===")
    print(f"  Cmax * exp(-k * 1)   = {c1:.4f}")
    print(f"  Cmax * 1/sqrt(2) (理论)  = {expected_1h:.4f}")
    print(f"  差值                 = {abs(c1-expected_1h):.6f}  [理论上为 0]")
    print()

    # ── 文章节六 6.2: 蓄积比 (典型间隔表) ──
    print("=== 文章节六 6.2: 蓄积比表 ===")
    print(f"  q6h 蓄积比: {m.accumulation_ratio(6):.3f}  (文章 1.143)")
    print(f"  q6h 稳态 Cmax: {m.steady_state_cmax(6):.2f} mg/L  (文章 37.0)")
    print(f"  q8h 蓄积比: {m.accumulation_ratio(8):.3f}  (文章 1.067)")
    print()

    # ── 文章节六 6.3: 瞬时叠加 vs 稳态峰值 ──
    print("=== 文章节六 6.3: 瞬时叠加峰值 (头几次给药) ===")
    doses = [0.4, 0.4, 0.4]
    times = [0.0, 6.0, 12.0]
    t_arr, c_arr = m.multiple_dose_curve(doses, times, t_max=24.0, dt=0.05)
    # 取每个给药瞬间后 1.5h 的浓度作为该次给药的瞬时峰值近似 (含吸收相)
    print(f"  形式稳态峰值 (R 公式): {m.steady_state_cmax(6):.3f} mg/L  (蓄积 14.3%)")
    # 取 t 在 t_dose+1.5 附近的浓度
    for i, td in enumerate(times):
        idx = int(round((td + 1.5) / 0.05))
        if idx < len(c_arr):
            print(f"  第 {i+1} 次给药 (t={td}h) 瞬时峰值 ≈ {c_arr[idx]:.3f} mg/L")
    print()

    # ── 文章节五 5.3 / 七: 场景对比 ──
    print("=== 文章节五 5.3 / 七: 不同 t1/2 下的 24 h 残留 ===")
    for scenario_name, scenario_fn in [
        ("成人    ", adult_400mg_single),
        ("老年    ", elderly_70yo_400mg),
        ("肝损    ", hepatic_impairment_400mg),
        ("儿童美林", child_meilin_10mgkg),
    ]:
        s = scenario_fn()
        c24 = s.concentration_at(24)
        n24 = s.n_half_lives_since_peak(24)
        print(f"  {scenario_name}: t1/2={s.half_life_h}h, 24h 残留占峰值 "
              f"= {s.remaining_fraction(24)*100:.4f}%  "
              f"(n={n24:.4f} 个半衰期, C(24)={c24:.4f} mg/L)")
    print()

    # ── curve() / concentration_at() 一致性 ──
    print("curve() vs concentration_at() 一致性校验 (t 从服药起算):")
    t_arr, c_arr = m.curve(t_max=24.0, n=481)
    for check_t in [0, 1.5, 6, 12, 24]:
        idx = min(int(round(check_t / 24.0 * 480)), 480)
        c_curve = c_arr[idx]
        c_conc = m.concentration_at(check_t)
        diff = abs(c_curve - c_conc)
        flag = "OK" if diff < 0.01 else "MISMATCH"
        print(f"  t={check_t:5.1f}h: curve={c_curve:7.4f}, "
              f"concentration_at={c_conc:7.4f}  [{flag}]")
    print()
    print("OK: IbuprofenPK model works.")
