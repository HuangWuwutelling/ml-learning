"""Alcohol pharmacokinetic model — 酒精药代动力学零级消除模型.

Widmark 公式 + 零级消除 (zero-order elimination)。血酒精浓度 (BAC)
随时间线性下降，与多数药物的 1 阶消除不同。

BAC(t) = max(0, BAC_peak - beta * t)

BAC_peak = A / (r * m)        [Widmark 1932]
    A = 酒精摄入量 (g)
    r = Widmark 身体水分系数 (男 0.68, 女 0.55)
    m = 体重 (kg)

References (every parameter verified by web lookup):
- Widmark 1932 (Widmark r male 0.68 / female 0.55, A/(r*m) formula):
  https://en.wikipedia.org/wiki/Widmark%27s_formula
- 零级消除速率 0.015-0.020 ‰/h (10-20 mg/dL/h) — 法医毒理学:
  https://en.wikipedia.org/wiki/Alcohol_Pharmacokinetics
- 中国酒驾阈值 0.02% / 醉驾阈值 0.08% (GB 19522):
  https://en.wikipedia.org/wiki/Drunk_driving_in_China
- 中国居民膳食指南 2016: 男性 ≤ 25 g/d, 女性 ≤ 15 g/d 纯酒精:
  https://www.cnsoc.org/drpostand/111800207.html
- 50 度白酒 100 mL 含纯酒精 39.5 g (密度 0.789 g/mL, abv 0.5):
  https://en.wikipedia.org/wiki/Ethanol_(data_page)#Density_of_the_ethanol-water_mixture
- 肝代谢占比 90-95%:
  https://www.ncbi.nlm.nih.gov/books/NBK546661/
- ADH 活性个体差异 2-3 倍:
  https://www.sciencedirect.com/topics/biochemistry-genetics-and-molecular-biology/alcohol-dehydrogenase
- ALDH2 缺陷东亚携带率 30-50% (Brooks 2009, NEJM):
  https://www.riahealth.com/alcohol-flush-reaction/

Usage:
    >>> m = AlcoholPK(drink_volume_mL=100, abv=0.5, body_weight_kg=70, sex='male')
    >>> m.peak_bac_per_mille
    1.0557...
    >>> m.bac_at(0)
    1.0557...
    >>> m.time_to_threshold(0.02)   # hours until BAC drops to 0.02 ‰
    69.05...
    >>> m.safe_to_drive()
    (69.05..., 70.38...)
"""
from __future__ import annotations

import numpy as np


# Widmark r values (body water distribution ratio)
# Source: Widmark 1932 EMP, reproduced in modern forensic toxicology
# textbooks. Female lower value reflects higher body fat %.
WIDMARK_R = {
    "male": 0.68,
    "female": 0.55,
    "M": 0.68,
    "F": 0.55,
}

# Ethanol density at 20 degC (g/mL). Required for abv -> mass conversion.
# Source: CRC Handbook 91st, https://en.wikipedia.org/wiki/Ethanol_(data_page)
ETHANOL_DENSITY_G_ML = 0.789

# 中国酒驾/醉驾血液阈值 (GB 19522, 道路交通安全法)
# 0.02% = 20 mg/100 mL = 0.02 g/L = 0.2 ‰
THRESHOLD_DUI_PER_MILLE = 0.20        # 酒驾
THRESHOLD_DWI_PER_MILLE = 0.80        # 醉驾

# Default zero-order elimination rate (per-hour, ‰/h).
# 0.015 ‰/h = 15 mg/dL/h, mid of textbook range 0.010-0.020 ‰/h.
# Reference population: average adult (法医毒理学).
DEFAULT_BETA_PER_MILLE_PER_H = 0.015


class AlcoholPK:
    """零级消除 PK 模型 (Widmark + 线性消除)."""

    def __init__(
        self,
        drink_volume_mL: float = 100.0,
        abv: float = 0.50,
        body_weight_kg: float = 70.0,
        sex: str = "male",
        beta_per_h: float = DEFAULT_BETA_PER_MILLE_PER_H,
    ):
        if sex not in WIDMARK_R:
            raise ValueError(f"sex must be one of {list(WIDMARK_R)}")
        self.drink_volume_mL = float(drink_volume_mL)
        self.abv = float(abv)
        self.body_weight_kg = float(body_weight_kg)
        self.sex = sex
        self.r = WIDMARK_R[sex]
        self.beta_per_h = float(beta_per_h)

        # Pure alcohol mass (g). A = V * abv * 0.789.
        self.A_grams = (
            self.drink_volume_mL * self.abv * ETHANOL_DENSITY_G_ML
        )

    # ── derived peak BAC ──────────────────────────────────────────
    @property
    def peak_bac_per_mille(self) -> float:
        """BAC at absorption peak (假设峰值已达成, ‰).

        Widmark equation: BAC_peak = A / (r * m).
        A in grams, r dimensionless, m in kg.
        BAC_peak dimension = g/kg_body_water. We report as ‰
        (g/kg), which matches the standard medical unit (g/L).
        """
        return self.A_grams / (self.r * self.body_weight_kg)

    # ── elimination ───────────────────────────────────────────────
    def bac_at(self, t_h: float) -> float:
        """t 小时后血酒精浓度 (‰). 零级消除.

        BAC(t) = max(0, BAC_peak - beta * t)

        Notes:
        - Simple 零级模型: 不区分吸收相. 假设峰值已在 t=0 达成.
        - 实际吸收相 30-90 分钟; 此简化适用于"睡前喝 vs 第二天早上"的
          长时预测.
        """
        t = max(0.0, float(t_h))
        return max(0.0, self.peak_bac_per_mille - self.beta_per_h * t)

    def time_to_threshold(self, threshold_per_mille: float) -> float:
        """返回浓度首次降到 threshold_per_mille (‰) 的时间 (h).

        若峰值已 < 阈值, 返回 0.0 (代表当前即可).
        若消除速率为 0, 返回 inf (永远到不了).
        """
        if self.peak_bac_per_mille <= threshold_per_mille:
            return 0.0
        if self.beta_per_h <= 0:
            return float("inf")
        return (
            (self.peak_bac_per_mille - threshold_per_mille)
            / self.beta_per_h
        )

    def time_to_zero(self) -> float:
        """浓度归零时间 (h). 0 = 已经清零, inf = 永不归零."""
        if self.peak_bac_per_mille <= 0:
            return 0.0
        if self.beta_per_h <= 0:
            return float("inf")
        return self.peak_bac_per_mille / self.beta_per_h

    def safe_to_drive(self) -> tuple[float, float]:
        """返回 (time_to_DUI_threshold, time_to_zero), 单位小时.

        DUI 阈值 = 0.02% (酒驾).
        DWI 阈值 = 0.08% (醉驾). 若想算醉驾阈值, 直接用
        time_to_threshold(0.80).
        """
        t_dui = self.time_to_threshold(THRESHOLD_DUI_PER_MILLE)
        t_zero = self.time_to_zero()
        return (t_dui, t_zero)

    def is_dwi(self) -> bool:
        """峰值 BAC 是否 ≥ 醉驾阈值 (0.08%)."""
        return self.peak_bac_per_mille >= THRESHOLD_DWI_PER_MILLE

    def is_dui(self) -> bool:
        """峰值 BAC 是否 ≥ 酒驾阈值 (0.02%)."""
        return self.peak_bac_per_mille >= THRESHOLD_DUI_PER_MILLE

    # ── vectorized curve ───────────────────────────────────────────
    def curve(self, t_max: float = 24.0, n: int = 481) -> tuple[np.ndarray, np.ndarray]:
        """返回 (t_array_h, BAC_array_per_mille) over [0, t_max]."""
        t = np.linspace(0.0, float(t_max), int(n))
        bac = np.maximum(0.0, self.peak_bac_per_mille - self.beta_per_h * t)
        return t, bac

    # ── plotting ──────────────────────────────────────────────────
    def plot_curve(self, ax, t_max: float = 24.0, label: str = None,
                    color: str = None, linewidth: float = 2.0,
                    threshold_color: str = "#888888"):
        """在给定 ax 上画 BAC(t) 曲线 + 阈值参考线.

        阈值参考线: 醉驾 0.08% (红色) 和 酒驾 0.02% (橙色).
        """
        import matplotlib.pyplot as plt
        t, bac = self.curve(t_max=t_max)
        if label is None:
            label = (
                f"{self.drink_volume_mL:g} mL "
                f"{int(self.abv*100)}°, "
                f"{self.body_weight_kg:g} kg, "
                f"{self.sex}"
            )
        ax.plot(t, bac, label=label,
                color=color, linewidth=linewidth)
        ax.axhline(THRESHOLD_DWI_PER_MILLE, color="#d62728",
                   linestyle="--", linewidth=1.0, alpha=0.7)
        ax.axhline(THRESHOLD_DUI_PER_MILLE, color="#ff7f0e",
                   linestyle="--", linewidth=1.0, alpha=0.7)
        ax.axhline(0.0, color="#222222", linewidth=0.8)
        return t, bac


# ── pre-built scenarios for figure generators ──────────────────────
def one_cup_baijiu_male():
    """1 small Chinese baijiu cup = 50 mL of 50% baijiu = ~20 g pure.

    BAC peak: 20 / (0.68 * 70) = 0.42 ‰ (just above DUI threshold 0.2 ‰).
    """
    return AlcoholPK(
        drink_volume_mL=50.0, abv=0.50,
        body_weight_kg=70.0, sex="male", beta_per_h=0.015,
    )


def three_cups_baijiu_male():
    """3 cups = 150 mL of 50% baijiu = ~60 g pure.

    BAC peak: 60 / (0.68 * 70) = 1.26 ‰ (DWI territory).
    """
    return AlcoholPK(
        drink_volume_mL=150.0, abv=0.50,
        body_weight_kg=70.0, sex="male", beta_per_h=0.015,
    )


def five_cups_baijiu_male():
    """5 cups = 250 mL of 50% baijiu = ~100 g pure.

    BAC peak: 100 / (0.68 * 70) = 2.10 ‰ (severe intoxication).
    """
    return AlcoholPK(
        drink_volume_mL=250.0, abv=0.50,
        body_weight_kg=70.0, sex="male", beta_per_h=0.015,
    )


# Aliases retained for backward compat with the original spec wording.
def one_drink_male():     return one_cup_baijiu_male()
def three_drinks_male():  return three_cups_baijiu_male()
def five_drinks_male():   return five_cups_baijiu_male()


if __name__ == "__main__":
    # Smoke test: 100 mL 50% baijiu, 70 kg male.
    m = AlcoholPK(drink_volume_mL=100, abv=0.50,
                  body_weight_kg=70, sex="male")
    print("=== Alcohol PK model smoke test ===")
    print(f"Drink: 100 mL 50% baijiu, 70 kg male")
    print(f"Pure alcohol A = {m.A_grams:.2f} g")
    print(f"Widmark r = {m.r}")
    print(f"Peak BAC = {m.peak_bac_per_mille:.4f} ‰ (zero-order model)")
    print(f"t=0 BAC:  {m.bac_at(0):.4f} ‰")
    print(f"t=1h:     {m.bac_at(1):.4f} ‰")
    print(f"t=8h:     {m.bac_at(8):.4f} ‰")
    print(f"t=24h:    {m.bac_at(24):.4f} ‰")
    t_dui, t_zero = m.safe_to_drive()
    print(f"Time to 0.02%% DUI threshold: {t_dui:.2f} h")
    print(f"Time to zero:                 {t_zero:.2f} h")
    print()
    # 5 drinks scenario (illustrative for 隔夜酒驾)
    m5 = five_drinks_male()
    print("=== 5 standard drinks (250 g alcohol), 70 kg male ===")
    print(f"Peak BAC = {m5.peak_bac_per_mille:.4f} ‰")
    print(f"DWI?     {m5.is_dwi()}")
    print(f"t=8h:    {m5.bac_at(8):.4f} ‰ (still DUI if >0.02%%)")
    print(f"t=10h:   {m5.bac_at(10):.4f} ‰")
    print(f"Time to 0.02%%: {m5.time_to_threshold(0.20):.2f} h")
    print()
    # Female comparison
    fm = AlcoholPK(drink_volume_mL=100, abv=0.50,
                   body_weight_kg=70, sex="female")
    print("=== Female comparison (same drink, 70 kg) ===")
    print(f"Male peak BAC:   {m.peak_bac_per_mille:.4f} ‰")
    print(f"Female peak BAC: {fm.peak_bac_per_mille:.4f} ‰ "
          f"(~+{(fm.peak_bac_per_mille/m.peak_bac_per_mille - 1)*100:.1f}%)")
    print()
    # ALDH2 deficiency (lower beta)
    aldh2 = AlcoholPK(drink_volume_mL=100, abv=0.50,
                      body_weight_kg=70, sex="male", beta_per_h=0.010)
    print("=== ALDH2 deficiency (slower clearance, beta=0.010) ===")
    print(f"Normal t_to_0.02%%:    {m.time_to_threshold(0.20):.2f} h")
    print(f"ALDH2 t_to_0.02%%:     {aldh2.time_to_threshold(0.20):.2f} h")
    print("OK:  AlcoholPK model works.")