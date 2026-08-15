"""
Milk powder (奶粉) dissolution kinetics model.

Simplified Noyes-Whitney one-compartment dissolution model with first-order
kinetics, calibrated to four water temperatures (25/40/60/70 degC) and four
milk-powder compositions (infant / adult whole-fat / skim / middle-aged).

Article structure (articles/env/22_奶粉溶解.md, revised 2026-08-15):
    一、溶解方程：Noyes-Whitney 一行        -> Noyes-Whitney equation (fig 1)
    二、水温：最要紧的旋钮                   -> 4-temperature k table (fig 2)
    三、40°C：溶解与营养的平衡点             -> default-temperature rationale
    四、70°C：WHO 的 kill-step 什么时候用     -> WHO 2007 application
    五、回到那罐奶粉                         -> recap + practical tips

Note: MILK_TYPES / compare_4_milk_types() are kept as an auxiliary
capability (4-composition comparison) but are NO LONGER part of the
article's main line (removed in the 2026-08-15 revision).

Core equation:
    dC/dt = k * (Cs - C)
        => C(t) = Cs * (1 - exp(-k * t))

where the lumped rate constant k absorbs the Nernst diffusion-layer
parameters: k = D * A / (V * h).

D (diffusion coefficient) and h (diffusion layer thickness) both depend on
temperature; in water the self-diffusion coefficient climbs from ~2.3e-5
cm2/s at 25 degC to ~5.5e-5 cm2/s at 70 degC (tracer-method data,
    see Refs [4], [10]; a constant-Ea Arrhenius extrapolation would
    overestimate the 70 degC point to ~6.5e-5),
and we encode four operating points as coarse k_per_min values:

    temperature  k_per_min   80% saturation time
    25 degC      0.5         3.2 min
    40 degC      1.5         1.1 min
    60 degC      3.0         0.5 min
    70 degC      4.0         ~0.4 min (but whey denatures, see Note below)

Why "first-order"?
    Full Nernst-Brunner: dC/dt = (D * A) / (V * h) * (Cs - C).
    Assuming A and V quasi-constant (small-particle, well-stirred batch),
    the equation reduces to a first-order ODE in (Cs - C). This is the
    same form as pharmaceutical dissolution testing (USP Apparatus II),
    where a first-order fit is the standard release model for
    non-disintegrating powders.

Why "40 degC" is the default recommendation?
    1) Infant formula preserves probiotics / lactoferrin / heat-labile
       vitamins (see Refs [7]-[8]).
    2) Dissolution is fast enough in practice (~1 min to 80%) that
       clumping is the rate-limiting step, not molecular solubility.
    3) Whey proteins begin to denature at >=60 degC; casein curdles
       at >=70 degC (Refs [8], [9]).

Why 70 degC is special?
    WHO recommends reconstituting powdered infant formula (PIF) with
    water >=70 degC as a kill step for Cronobacter sakazakii and
    Salmonella (Ref [6]). At 70 degC the *dissolution* is fastest
    (~0.4 min to 80%) but the *nutrition* loses heat-sensitive
    fractions. This is the core tradeoff the article explores.

Key parameters (verified by web lookup, see References):
- 4-temperature self-diffusion of water (Holz et al. 2000 / Nature 2021 review)
- Diffusion-layer thickness h, typical 10-100 um (pharmaceutical dissolution)
- Whey:casein 60:40 in first-stage infant formula (Wikipedia / Codex)
- Composition ranges across 4 powder types (Chinese food-composition table)
- Nestle / Feihe / Mead Johnson label temperatures (~40-50 degC default)
- WHO 2007 PIF preparation guideline (70 degC Cronobacter / Salmonella)
- FSANZ Salmonella D-values (heat-inactivation kinetics)

Model boundaries (teaching-level simplification):
- A, V assumed constant (particle size distribution ignored)
- Constant stirring (h does not change with time)
- 70 degC denaturation flagged qualitatively, not modeled as a kinetic term
- Composition differences enter as a fixed k multiplier, not as
  separate solubilities

All physical / empirical parameters have a citation in the References
section; docstring style follows models/uhvdc.py and models/seir.py.

References (every parameter verified by web lookup):

[1] Noyes AA, Whitney WR (1897). The rate of solution of solid substances
    in their own solutions. J Am Chem Soc 19:930-934.
    - Original first-order dissolution equation
    - DOI / ACS landing: https://pubs.acs.org/doi/abs/10.1021/ja02071a007
    - Discussion (Pura 1999, Chem Eng Educ 33(4): 274-277) places the
      equation as the foundation of modern dissolution kinetics and the
      Nernst diffusion-layer concept.

[2] Noyes-Whitney equation (Wikipedia, modern form with Nernst layer)
    - Modern equation: dC/dt = (D * A) / (h * V) * (Cs - C)
    - URL: https://en.wikipedia.org/wiki/Noyes%E2%80%93Whitney_equation

[3] Diffusion-layer thickness h: 10-100 um (typical), 20-150 um
    (broad), ~30 um (default pharmaceutical practice).
    - Pharma lessons overview: https://pharmalessons.com/noyes-whitney-equation/
    - Pharma Approach: https://www.pharmapproach.com/noyes-whitney-equation/
    - Drug dissolution lab notes: https://www.drugdissolution.com/factors-affecting-dissolution/

[4] Self-diffusion coefficient of water vs temperature. Standard
    literature values (tracer-method data compiled by Holz et al. 2000;
    the 70 degC point is from Easteal, Price & Woolf 1989, J Chem Soc
    Faraday Trans 1 85:1091). Used to motivate the four-temperature k
    step (values corrected 2026-08-15; earlier draft used a constant-Ea
    Arrhenius extrapolation that overestimates high-T D):
        25 degC: 2.30e-9 m2/s  (= 2.30e-5 cm2/s)
        40 degC: 3.23e-9 m2/s  (= 3.23e-5 cm2/s)  ratio 1.40
        60 degC: 4.77e-9 m2/s  (= 4.77e-5 cm2/s)  ratio 2.07
        70 degC: 5.50e-9 m2/s  (= 5.50e-5 cm2/s)  ratio 2.39
    - Holz M, Heil SR, Sacco A (2000). Phys Chem Chem Phys 2:4740-4742
      (cited in Nature Sci Rep 2021 review):
      https://www.nature.com/articles/s41598-021-95620-0
    - Stokes-Einstein relation D = kT / (6 pi eta r):
      https://chem.libretexts.org/Courses/University_of_California_Berkeley/Chem_1A/Chem_1A_Textbook/5%3A_Physical_Properties_of_Solutions/5.1%3A_Thermodynamics_of_Stokes-Einstein_Relation
    - Water dynamic viscosity table (eta drops from ~0.89 mPa.s at
      25 degC to ~0.40 mPa.s at 70 degC):
      https://www.engineeringtoolbox.com/water-dynamic-kinematic-viscosity-d_596.html

[5] Milk-powder composition (per 100 g dry powder). Standard Chinese
    food-composition tables (脱脂 / 全脂 / 婴幼儿) put:
        Whole-fat milk powder: protein 24-26 g, fat 26-28 g,
            lactose 38-42 g, ash 6-8 g
        Skim milk powder:      protein 32-36 g, fat 0.5-1.5 g,
            lactose 50-52 g, ash 8-10 g
    - Baidu Baike (whole-fat milk powder): https://baike.baidu.com/item/全脂奶粉
    - 39 Health decomposition and comparison:
      http://baby.39.net/a/201162/1710691.html
    - Chinese milk powder composition overview (Sohu, 2020):
      https://www.sohu.com/a/366049241_120106625

[6] WHO / FAO safe preparation of powdered infant formula (PIF).
    - Reconstitute with water >=70 degC to reduce risk of
      Cronobacter sakazakii and Salmonella, then cool rapidly to
      feeding temperature and use within 2 h.
    - Applies especially to infants <=2 months, pre-term, low-birth-weight,
      or immunocompromised.
    - CDC and AAP note this step also burns-scalds risk; many country
      agencies recommend cool reconstitution with sterile liquid formula
      instead where available.
    - Reference: WHO/FAO "Safe Preparation, Storage and Handling of
      Powdered Infant Formula" guidelines, summarized at:
      https://www.who.int/publications/i/item/9789241595414
    - Practical summary (Cronobacter heat sensitivity, >=60 degC):
      https://www.cdc.gov/cronobacter/about/index.html
      https://www.cdc.gov/infant-formula-php/

[7] Infant formula protein composition: whey-dominant first-stage
    formulas use a whey:casein ratio of 60:40 to approximate human
    milk; some "whey-dominant" lines push this to 70:30 or 80:20.
    - Wikipedia "Infant formula" (composition section):
      https://en.wikipedia.org/wiki/Infant_formula
    - Codex Alimentarius standard for infant formula (CXS 156-1987,
      rev. 2023): https://www.fao.org/fao-who-codexalimentarius/

[8] Whey / casein heat denaturation thresholds. Whey proteins begin
    irreversible denaturation around 60-65 degC; casein starts to
    aggregate at 70+ degC in the presence of calcium. Practical
    infant-formula labels cite this as the reason for the 40-50 degC
    upper bound.
    - Health Q&A: https://www.bohe.cn/ask/view/103213530.html
    - Pediatric advice (family doctor): https://www.familydoctor.com.cn/q/20946942.html
    - Sohu parenting column: https://www.sohu.com/a/835719608_111342

[9] Brand label temperatures. Major CN/EU/US brands ship the same
    40-50 degC recommendation on the can. Examples:
    - Nestle (雀巢能恩金盾 1 段): 40-60 degC warmed water; some EU/US
      labels 37 degC (body temperature) for heat-labile probiotics.
      https://www.nestlebaby.com.cn/product/quechao-chaojinengen3
      https://baike.baidu.com/item/超级能恩/4447776
    - 39 health (cross-brand comparison):
      http://baby.39.net/a/201162/1710691.html
    - Mama.cn brand comparison (Meiji 70 degC, Xianzhi 37 degC,
      defaults 40-50 degC):
      https://www.mama.cn/z/wiki/29086/

[10] Easteal AJ, Price WE, Woolf LA (1989). Diaphragm cell for
    high-temperature diffusion measurements. Tracer diffusion
    coefficients for water to 363 K. J Chem Soc Faraday Trans 1
    85:1091-1097. Source of the high-temperature (40-100 degC)
    water self-diffusion data compiled in Ref [4]; at 70 degC the
    measured self-diffusion coefficient is about 5.5e-9 m2/s.
    - RSC landing: https://pubs.rsc.org/en/Content/ArticleLanding/1989/F1/F19898501091

Usage:
    >>> d40 = Dissolution(K_PER_MIN[40])                   # 40 degC
    >>> print(f"80% saturation time: {d40.time_to_dissolve():.2f} min")
    >>> print(f"C(t=2min) / Cs = {d40.concentration(2):.3f}")
    >>> fig, ax = plt.subplots(figsize=(8, 4))
    >>> d40.plot_curve(t_max=5, ax=ax, label="40 degC (recommended)")
    >>> plt.show()
    >>> df = Dissolution.compare_4_temperatures()
    >>> df2 = Dissolution.compare_4_milk_types()
"""

import math
import os

import numpy as np

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None


# -----------------------------------------------------------------------------
# Default parameters (verified, see References [1]-[9])
# -----------------------------------------------------------------------------

# 4 water temperatures, lumped k_per_min values (engineering estimate;
# motivate by self-diffusion ratio in Ref [4]).
# Order-of-magnitude reasoning:
#   25 degC: baseline room temperature
#   40 degC: brand-recommended for infant formula (Refs [8]-[9])
#   60 degC: sub-boiling, fast dissolution but beginning of denaturation
#   70 degC: WHO kill-step (Ref [6]); the model predicts "fastest"
#            but the article flags protein denaturation
K_PER_MIN = {
    25: 0.5,
    40: 1.5,
    60: 3.0,
    70: 4.0,
}

# Diffusion coefficient relative to 25 degC (used to motivate the k table).
# Ratios match self-diffusion literature (Ref [4]) and rounded to one
# decimal place. Used to drive the *layout* of the 4-temperature comparison,
# not the absolute k values above.
D_RELATIVE = {
    25: 1.0,
    40: 1.4,
    60: 2.1,
    70: 2.4,
}

# Water dynamic viscosity (mPa*s) at the 4 temperatures, used to
# back out the relative diffusion coefficients. Source: Engineering Toolbox,
# 0.89 / 0.65 / 0.47 / 0.40 at 25/40/60/70 degC. Recorded here as a
# reference footnote in the docstring, not consumed by the solver.
WATER_VISCOSITY_MPA_S = {
    25: 0.89,
    40: 0.65,
    60: 0.47,
    70: 0.40,
}

# Default "80% saturation" target for time_to_dissolve / comparison rows.
DEFAULT_TARGET_FRACTION = 0.8

# 4 milk-powder compositions (g per 100 g dry powder). Ranges come from
# Chinese food-composition tables (Ref [5]); mid-points are taken as the
# representative value used to derive a composition multiplier for k.
#
# Composition multiplier (engineering estimate, qualitative):
#   - infant: 1.00 (reference; whey-dominant, ~60% whey proteins,
#     fast hydration; cf. Ref [7])
#   - adult whole-fat: 0.70 (high fat content slows wetting and
#     promotes clumping)
#   - skim: 1.15 (low fat, fast hydration; foaming suppressed)
#   - middle-aged: 0.85 (similar to adult whole-fat, but with added
#     calcium and fiber that slow dissolution slightly)
MILK_TYPES = {
    "infant": {
        "name_zh": "婴幼儿配方",
        "protein_g": 11.0,
        "fat_g": 27.0,
        "lactose_g": 54.0,
        "ash_g": 3.0,
        "k_multiplier": 1.00,
        "note": "含乳清蛋白比例约60%（Ref [7]）；含益生菌，怕高温",
    },
    "adult_whole": {
        "name_zh": "成人全脂",
        "protein_g": 25.0,
        "fat_g": 27.0,
        "lactose_g": 40.0,
        "ash_g": 7.0,
        "k_multiplier": 0.70,
        "note": "脂肪多，易结块",
    },
    "skim": {
        "name_zh": "脱脂",
        "protein_g": 34.0,
        "fat_g": 1.0,
        "lactose_g": 51.0,
        "ash_g": 9.0,
        "k_multiplier": 1.15,
        "note": "低脂，溶解快，无明显蛋白变性顾虑",
    },
    "middle_aged": {
        "name_zh": "中老年",
        "protein_g": 23.5,
        "fat_g": 20.0,
        "lactose_g": 37.5,
        "ash_g": 9.0,
        "k_multiplier": 0.85,
        "note": "钙强化、降脂；矿物质略多，溶解略慢",
    },
}


class Dissolution:
    """First-order Noyes-Whitney dissolution model.

    Solves the simplified Noyes-Whitney equation:

        dC/dt = k * (Cs - C)
        C(0)  = C0
        C(t)  = Cs + (C0 - Cs) * exp(-k * t)

    Equivalent to Nernst-Brunner with A, V, h, D all folded into one
    positive scalar `k_per_min` (1/min). See module docstring Refs
    [1]-[2] for the historical derivation.

    Parameters
    ----------
    k_per_min : float
        First-order dissolution rate constant (1/min). Defaults from
        ``K_PER_MIN`` keyed by water temperature: 0.5/1.5/3.0/4.0 for
        25/40/60/70 degC.
    Cs : float, optional
        Saturation concentration (same units as C). Default 1.0 (= 100%
        saturated solution; the model uses normalised C/Cs units).
    C0 : float, optional
        Initial concentration at t = 0. Default 0.0 (dry powder).

    Attributes
    ----------
    k_per_min : float
        Stored rate constant.
    Cs : float
        Stored saturation concentration.
    C0 : float
        Stored initial concentration.
    tau_min : float
        Characteristic time constant (1 / k), minutes.

    Notes
    -----
    Domain restriction: k_per_min must be > 0; Cs > 0 for the
    normalised fraction C(t)/Cs to be meaningful.
    """

    def __init__(self, k_per_min, Cs=1.0, C0=0.0):
        if k_per_min <= 0:
            raise ValueError(
                f"k_per_min must be > 0, got {k_per_min!r}"
            )
        if Cs <= 0:
            raise ValueError(
                f"Cs must be > 0 (saturation), got {Cs!r}"
            )

        self.k_per_min = float(k_per_min)
        self.Cs = float(Cs)
        self.C0 = float(C0)
        self.tau_min = 1.0 / self.k_per_min

    # -----------------------------------------------------------------
    # Core kinetics
    # -----------------------------------------------------------------
    def concentration(self, t_min):
        """Concentration at time t_min (same units as Cs).

        C(t) = Cs + (C0 - Cs) * exp(-k * t)

        With the default C0 = 0, this reduces to the textbook form
        C(t) = Cs * (1 - exp(-k * t)).

        Parameters
        ----------
        t_min : float or array-like
            Time in minutes (>= 0).

        Returns
        -------
        float or numpy.ndarray
            Concentration C(t), same shape as t_min (scalars returned as
            Python float).
        """
        if np.isscalar(t_min):
            t = float(t_min)
            if t < 0:
                raise ValueError(f"t_min must be >= 0, got {t}")
            return self.Cs + (self.C0 - self.Cs) * math.exp(
                -self.k_per_min * t
            )

        t_arr = np.asarray(t_min, dtype=float)
        if np.any(t_arr < 0):
            raise ValueError("t_min array must be >= 0 everywhere")
        return self.Cs + (self.C0 - self.Cs) * np.exp(
            -self.k_per_min * t_arr
        )

    def fraction(self, t_min):
        """Normalised concentration C(t) / Cs in [0, 1] (default C0=0).

        Convenience wrapper around ``concentration`` for plotting and
        comparison tables.

        Parameters
        ----------
        t_min : float or array-like
            Time in minutes (>= 0).

        Returns
        -------
        float or numpy.ndarray
            Dimensionless fraction in [0, 1].
        """
        return self.concentration(t_min) / self.Cs

    def time_to_dissolve(self, target_C=DEFAULT_TARGET_FRACTION):
        """Time (min) to reach ``target_C`` of saturation.

        From Cs + (C0 - Cs) * exp(-k t) = target_C:

            t = -ln((target_C - Cs) / (C0 - Cs)) / k        if C0 != Cs
            t = -ln(1 - target_C / Cs) / k                  if C0 = 0

        With the default C0 = 0, target_C = 0.8 of Cs (i.e. fraction 0.8),
        the closed-form answer is t = -ln(0.2) / k ≈ 1.6094 / k.

        Parameters
        ----------
        target_C : float, optional
            Absolute target concentration (same units as Cs).
            Default ``DEFAULT_TARGET_FRACTION = 0.8`` interpreted as
            80% of Cs (because Cs = 1.0 by default).

        Returns
        -------
        float
            Time in minutes.

        Raises
        ------
        ValueError
            If ``target_C`` is impossible: must lie strictly between C0
            and Cs.
        """
        if target_C <= self.C0 or target_C >= self.Cs:
            raise ValueError(
                f"target_C must lie strictly between C0 ({self.C0}) "
                f"and Cs ({self.Cs}); got {target_C}"
            )
        return -math.log((target_C - self.Cs) / (self.C0 - self.Cs)) / self.k_per_min

    # -----------------------------------------------------------------
    # Plotting
    # -----------------------------------------------------------------
    def plot_curve(self, t_max=5.0, ax=None, label=None, n=200,
                   target_C=DEFAULT_TARGET_FRACTION):
        """Plot the normalised concentration curve C(t)/Cs from 0 to t_max.

        Adds an optional horizontal line at ``target_C`` and a vertical
        line marking ``time_to_dissolve(target_C)``.

        Parameters
        ----------
        t_max : float, optional
            Upper time bound (minutes). Default 5.0.
        ax : matplotlib axes, optional
            Existing axes to plot into. If None, a new figure+axes is
            created.
        label : str, optional
            Curve label. Default None (no label).
        n : int, optional
            Number of sample points. Default 200.
        target_C : float, optional
            Target saturation fraction for the annotation lines.
            Default ``DEFAULT_TARGET_FRACTION = 0.8``.

        Returns
        -------
        matplotlib.axes.Axes
            The axes that was drawn into.
        """
        if plt is None:
            raise ImportError(
                "matplotlib is required for plot_curve; install with "
                "`python -m pip install matplotlib`."
            )
        owns_fig = ax is None
        if owns_fig:
            fig, ax = plt.subplots(figsize=(8, 4))

        t = np.linspace(0.0, t_max, n)
        ax.plot(t, self.fraction(t), label=label)
        ax.axhline(target_C, color="gray", linestyle=":", linewidth=1)
        t_target = self.time_to_dissolve(target_C)
        ax.axvline(t_target, color="gray", linestyle=":", linewidth=1)

        ax.set_xlabel("t / min")
        ax.set_ylabel("C(t) / Cs")
        ax.set_xlim(0.0, t_max)
        ax.set_ylim(0.0, 1.05)
        ax.grid(True, alpha=0.3)

        if label is not None:
            ax.legend(loc="lower right")

        if owns_fig:
            plt.tight_layout()
        return ax

    # -----------------------------------------------------------------
    # Comparisons
    # -----------------------------------------------------------------
    @staticmethod
    def compare_4_temperatures(temps=(25, 40, 60, 70),
                                target_C=DEFAULT_TARGET_FRACTION):
        """Compare dissolution kinetics across 4 water temperatures.

        Each row is one of the temperatures in ``K_PER_MIN``.

        Parameters
        ----------
        temps : iterable of int, optional
            Water temperatures (degC). Default (25, 40, 60, 70).
        target_C : float, optional
            Target saturation fraction for the time-to-target column.
            Default ``DEFAULT_TARGET_FRACTION = 0.8``.

        Returns
        -------
        pandas.DataFrame
            Columns: temperature_C, k_per_min, D_relative, target_C,
                     t_target_min, tau_min.
        """
        if pd is None:
            raise ImportError(
                "compare_4_temperatures requires pandas; "
                "install with `python -m pip install pandas`."
            )

        rows = []
        for T in temps:
            if T not in K_PER_MIN:
                raise ValueError(
                    f"Temperature {T} not in K_PER_MIN "
                    f"({sorted(K_PER_MIN.keys())}); pass k_per_min "
                    f"explicitly for unlisted temperatures."
                )
            d = Dissolution(K_PER_MIN[T])
            rows.append({
                "temperature_C": T,
                "k_per_min": K_PER_MIN[T],
                "D_relative": D_RELATIVE.get(T, float("nan")),
                "target_C": target_C,
                "t_target_min": d.time_to_dissolve(target_C),
                "tau_min": d.tau_min,
            })
        return pd.DataFrame(rows)

    @staticmethod
    def compare_4_milk_types(temps=(40,), types=None,
                              target_C=DEFAULT_TARGET_FRACTION):
        """Compare dissolution kinetics across 4 milk-powder types.

        ``k_per_min`` is taken from the default ``K_PER_MIN`` table
        and multiplied by the type-specific factor in ``MILK_TYPES``.
        The default temperature is 40 degC (brand recommendation,
        Refs [8]-[9]).

        Parameters
        ----------
        temps : iterable of int, optional
            Water temperatures to evaluate. Default (40,).
        types : iterable of str, optional
            Subset of ``MILK_TYPES`` keys to evaluate
            ({"infant", "adult_whole", "skim", "middle_aged"}).
            Default None = all four.
        target_C : float, optional
            Target saturation fraction. Default 0.8.

        Returns
        -------
        pandas.DataFrame
            Columns: temperature_C, type, name_zh, k_per_min,
                     k_multiplier, k_eff, t_target_min, note.
        """
        if pd is None:
            raise ImportError(
                "compare_4_milk_types requires pandas; "
                "install with `python -m pip install pandas`."
            )

        if types is None:
            types = list(MILK_TYPES)
        rows = []
        for T in temps:
            if T not in K_PER_MIN:
                raise ValueError(
                    f"Temperature {T} not in K_PER_MIN "
                    f"({sorted(K_PER_MIN.keys())}); pass k_per_min "
                    f"explicitly for unlisted temperatures."
                )
            k_base = K_PER_MIN[T]
            for key in types:
                if key not in MILK_TYPES:
                    raise ValueError(
                        f"type {key!r} not in MILK_TYPES "
                        f"({list(MILK_TYPES)})"
                    )
                cfg = MILK_TYPES[key]
                k_eff = k_base * cfg["k_multiplier"]
                d = Dissolution(k_eff)
                rows.append({
                    "temperature_C": T,
                    "type": key,
                    "name_zh": cfg["name_zh"],
                    "k_per_min": k_base,
                    "k_multiplier": cfg["k_multiplier"],
                    "k_eff": k_eff,
                    "target_C": target_C,
                    "t_target_min": d.time_to_dissolve(target_C),
                    "note": cfg["note"],
                })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=" * 78)
    print("Milk-powder Noyes-Whitney dissolution (4 temperatures, 4 milk types)")
    print("=" * 78)

    # ------------------------------------------------------------------
    # 1) Single 40 degC scenario (the recommended brand setting)
    # ------------------------------------------------------------------
    print("=" * 78)
    print("Default scenario: 40 degC (brand recommendation)")
    print("=" * 78)
    d40 = Dissolution(K_PER_MIN[40])
    print(f"  k_per_min       = {d40.k_per_min}")
    print(f"  Cs              = {d40.Cs}")
    print(f"  C0              = {d40.C0}")
    print(f"  tau (1/k)       = {d40.tau_min:.3f} min")
    print(f"  C(0.5 min)/Cs   = {d40.fraction(0.5):.3f}")
    print(f"  C(1 min)/Cs     = {d40.fraction(1.0):.3f}")
    print(f"  C(2 min)/Cs     = {d40.fraction(2.0):.3f}")
    print(f"  80% t_target    = {d40.time_to_dissolve():.3f} min")
    print()
    expected = -math.log(1.0 - DEFAULT_TARGET_FRACTION) / d40.k_per_min
    print(f"  expected        = -ln(0.2)/k = {expected:.3f} min")
    assert abs(d40.time_to_dissolve() - expected) < 1e-9, (
        f"time_to_dissolve mismatch: {d40.time_to_dissolve()} vs {expected}"
    )
    print("  -> closed-form check: passed")
    print()

    # ------------------------------------------------------------------
    # 2) 4-temperature comparison table
    # ------------------------------------------------------------------
    print("=" * 78)
    print("4 temperatures (25/40/60/70 degC) - 80% saturation time")
    print("=" * 78)
    df4 = Dissolution.compare_4_temperatures()
    print(
        df4[
            ["temperature_C", "k_per_min", "D_relative", "t_target_min", "tau_min"]
        ].to_string(index=False, float_format=lambda x: f"{x:,.3f}")
    )
    print()

    # ------------------------------------------------------------------
    # 3) 4 milk-type comparison at 40 degC
    # ------------------------------------------------------------------
    print("=" * 78)
    print("4 milk types at 40 degC - 80% saturation time")
    print("=" * 78)
    df_milk = Dissolution.compare_4_milk_types()
    print(
        df_milk[
            ["type", "name_zh", "k_per_min", "k_multiplier", "k_eff",
             "t_target_min", "note"]
        ].to_string(index=False, float_format=lambda x: f"{x:,.3f}")
    )
    print()

    # ------------------------------------------------------------------
    # 4) Order-of-magnitude sanity checks
    # ------------------------------------------------------------------
    print("=" * 78)
    print("Sanity checks")
    print("=" * 78)
    d25 = Dissolution(K_PER_MIN[25])
    d60 = Dissolution(K_PER_MIN[60])
    d70 = Dissolution(K_PER_MIN[70])
    print(f"  25 degC 80% t  = {d25.time_to_dissolve():.2f} min (spec ~3.2)")
    print(f"  40 degC 80% t  = {d40.time_to_dissolve():.2f} min (spec ~1.1)")
    print(f"  60 degC 80% t  = {d60.time_to_dissolve():.2f} min (spec ~0.5)")
    print(f"  70 degC 80% t  = {d70.time_to_dissolve():.2f} min (fastest, "
          "but protein denatures)")
    print()

    # ------------------------------------------------------------------
    # 5) Optional figure: 4-temperature curve family
    # ------------------------------------------------------------------
    if plt is not None:
        print("=" * 78)
        print("Figure: 4-temperature dissolution curves -> milk_powder.png")
        print("=" * 78)
        fig, ax = plt.subplots(figsize=(9, 3.83))
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        for T in (25, 40, 60, 70):
            d = Dissolution(K_PER_MIN[T])
            d.plot_curve(t_max=5.0, ax=ax, label=f"{T} degC")
        ax.set_title("Milk powder dissolution at 4 temperatures (Noyes-Whitney, "
                     "k table in module)")
        # Annotate 40 degC 80% time on the figure
        t40 = Dissolution(K_PER_MIN[40]).time_to_dissolve()
        ax.annotate(
            f"40 degC -> 80% in {t40:.2f} min",
            xy=(t40, DEFAULT_TARGET_FRACTION),
            xytext=(t40 + 0.4, 0.55),
            arrowprops=dict(arrowstyle="->", color="black"),
            fontsize=9,
        )

        fig_path = os.path.join(
            os.path.dirname(__file__), "..", "articles", "env",
            "milk_powder_dissolution.png",
        )
        fig_path = os.path.abspath(fig_path)
        os.makedirs(os.path.dirname(fig_path), exist_ok=True)
        plt.tight_layout()
        plt.savefig(fig_path, dpi=120)
        plt.close()
        print(f"  saved to: {fig_path}")
        print()
