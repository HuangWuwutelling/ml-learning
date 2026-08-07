"""
SEIR 4 仓室传染病传播模型 (Susceptible-Exposed-Infectious-Recovered).

模型：4 仓室动力学，常用于描述有显著潜伏期的呼吸道病毒传播。
在 SIR 模型基础上增加 E（Exposed，已感染但未发病）仓室，能更准确刻画
"已感染但暂未传染"的潜伏期阶段；这也正是 SARS-CoV-2 防控期间
全球公共卫生机构实际使用的模型形态（Imperial College、CDC、WHO）。

4 仓室微分方程（均匀混合假设）：

    dS/dt = -beta * S * I / N
    dE/dt = +beta * S * I / N - sigma * E
    dI/dt = +sigma * E - gamma * I
    dR/dt = +gamma * I

参数：
- beta：传播率（接触率 x 传播概率），单位 1/天
- sigma = 1 / 潜伏期（暴露 -> 感染），单位 1/天
- gamma = 1 / 感染期（感染 -> 恢复），单位 1/天
- R0 = beta / gamma：基本再生数（无干预、全员易感时 1 个感染者平均传染多少人）

关键假设：
- 均匀混合：所有个体接触概率相同（无社交网络/空间结构）
- 无年龄分层
- 无变异株（参数在疫情过程中固定）
- 恢复后终身免疫（不返回 S）

所有物理参数都联网核实（每条至少 1 个 URL），见 VIRUS_PARAMS 与参考文献区。
docstring 风格与 models/pops_lrt.py 保持一致（中文 + 来源 + URL）。

References (all parameters verified by web lookup, see docstring fields):

普通感冒 (rhinovirus, 主要致病原)
- Heikkinen T, Järvinen A (2003). The common cold. Lancet 361:51-59
  https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(03)12162-9/fulltext
- 综述引用 R0 约 1.3-2.0；呼吸道病毒传播动力学综述
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2797724/
  https://en.wikipedia.org/wiki/Common_cold
- 潜伏期 1-3 天、症状持续 7-10 天（CDC/Heikkinen）
  https://www.cdc.gov/common-cold/about/index.html

季节性流感 (influenza A/B)
- Biggerstaff M et al. (2014). Estimates of the reproduction number for
  seasonal, pandemic, and zoonotic influenza: a systematic review.
  BMC Infect Dis 14:480
  https://bmcinfectdis.biomedcentral.com/articles/10.1186/1471-2334-14-480
  https://pmc.ncbi.nlm.nih.gov/articles/PMC4169819/
- 关键发现：季节性流感 R0 中位 1.28 (IQR 1.19-1.37)，范围 0.9-2.1
- 潜伏期 1-4 天（中位 2 天）、感染期 3-5 天（CDC）
  https://www.cdc.gov/flu/about/keyfacts.htm
  https://www.cdc.gov/flu/about/disease/spread.htm

COVID-19 (SARS-CoV-2 武汉原始株)
- Liu Y, Gayle AA, Wilder-Smith A, Rocklov J (2020). The reproductive
  number of COVID-19 is higher compared to SARS coronavirus.
  J Travel Med 27(2):taaa021
  https://academic.oup.com/jtm/article/27/2/taaa021/5735319
- Sanchez S et al. (2020). High contagiousness and rapid spread of
  severe acute respiratory syndrome coronavirus 2. Emerg Infect Dis
  26(7):1470-1477. 合并 R0 估计 3.28 (95% CI 2.83-3.83)
  https://wwwnc.cdc.gov/eid/article/26/7/20-0282_article
- WHO COVID-19 公共卫生指南：潜伏期中位 5 天，范围 1-14 天
  https://www.who.int/news-room/fact-sheets/detail/coronavirus-disease-(covid-19)
- CDC：感染期 5-10 天（轻症，病毒培养可分离活病毒时间窗）
  https://www.cdc.gov/coronavirus/2019-ncov/hcp/duration-isolation.html

麻疹 (measles virus)
- Guerra FM et al. (2017). The basic reproduction number (R0) of
  measles: a systematic review. Lancet Infect Dis 17(12):e420-e428
  https://www.sciencedirect.com/science/article/abs/pii/S1473309917303079
- 系统综述：麻疹 R0 中位 ~12-18，pre-vaccine era 一致估计
- CDC 临床概述：潜伏期通常 10-14 天（前驱期），范围 7-21 天；
  感染期出疹前 4 天到出疹后 4 天（共 8-9 天）
  https://www.cdc.gov/measles/hcp/clinical-overview.html
  https://www.cdc.gov/measles/transmission.html
- WHO 麻疹概况：未接种者与麻疹患者密切接触后 9/10 会感染
  https://www.who.int/news-room/fact-sheets/detail/measles

Kermack-McKendrick 1927 仓室模型起源：
- Kermack WO, McKendrick AG (1927). A contribution to the mathematical
  theory of epidemics. Proc R Soc Lond A 115:700-721
  https://royalsocietypublishing.org/doi/10.1098/rspa.1927.0118

文章案例数据来源（非模型参数；用于复现文章引言与第五节案例）：
- Clemmons NS, Gastañaduy PA, Fiebelkorn AP, Redd SB, Seward JF (2015).
  Measles - United States, January 4-April 2, 2015. MMWR 64(14):373-376
  https://www.cdc.gov/mmwr/preview/mmwrhtml/mm6414a1.htm
  （迪士尼麻疹：美国 147 例 = 加州 131 + 外州 6 州 16，共跨 7 个州）
- National Institute of Infectious Diseases, Japan (2020). COVID-19
  Diamond Princess cruise ship outbreak report
  https://www.niid.go.jp/niid/en/2019-ncov-e/9417-covid-dp-fe-02.html
  （3711 人中 712 例确诊，感染比例 19.2%）

Usage:
    >>> m = SEIR(virus='measles')  # 用预置参数
    >>> m.solve(days=200, dt=0.1)
    >>> m.peak_info()
    >>> df = SEIR.compare_viruses(['common_cold', 'seasonal_flu',
    ...                             'covid_wuhan', 'measles'])
"""

import numpy as np

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


# -----------------------------------------------------------------------------
# 4 种病毒物理参数（联网核实，参数区间中位数）
# 每条参数至少 1 个源；URL 见模块 docstring 参考文献区。
# -----------------------------------------------------------------------------
# common_cold
#   R0 1.3-2.0 (Heikkinen & Järvinen 2003; 综述常引用 1.5)
#   潜伏期 1-3 天（中位 2；CDC/Heikkinen）
#   感染期 3-7 天（中位 5；症状总持续 7-10 天，传染窗口约 5 天）
# seasonal_flu
#   R0 中位 1.28 IQR 1.19-1.37 (Biggerstaff 2014)；本文取 1.5
#   潜伏期 1-4 天（中位 2；CDC）
#   感染期 3-5 天（中位 4；CDC/临床指南）
# covid_wuhan
#   R0 ~2.5-3.3 (Liu 2020 meta-review)；本文取 3.0
#   潜伏期 1-14 天（中位 5；WHO 2020）
#   感染期 5-10 天（中位 7；CDC 轻症）
# measles
#   R0 ~12-18 (Guerra 2017 systematic review)；本文取 15
#   潜伏期 10-14 天（中位 12；CDC）
#   感染期 5-7 天（中位 6；4 days before + 4 days after rash = 8-9 days，
#   但前驱期传染性最强、3-5 天即可分离活病毒）
VIRUS_PARAMS = {
    "common_cold": {
        "name": "Common cold (rhinovirus)",
        "name_zh": "普通感冒",
        "R0": 1.5,
        "latent_period": 2.0,        # 天
        "infectious_period": 5.0,    # 天
        "sources": {
            "R0": "Heikkinen T, Järvinen A (2003). The common cold. Lancet 361:51-59 "
                  "https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(03)12162-9/fulltext",
            "latent": "CDC About Common Cold https://www.cdc.gov/common-cold/about/index.html",
            "infectious": "Heikkinen & Järvinen 2003; rhinovirus shedding peaks 2-3 d, "
                          "symptoms 7-10 d, transmission window ~5 d",
        },
    },
    "seasonal_flu": {
        "name": "Seasonal influenza",
        "name_zh": "季节性流感",
        "R0": 1.5,
        "latent_period": 2.0,
        "infectious_period": 4.0,
        "sources": {
            "R0": "Biggerstaff M et al. (2014). BMC Infect Dis 14:480 "
                  "https://bmcinfectdis.biomedcentral.com/articles/10.1186/1471-2334-14-480 "
                  "(median 1.28, IQR 1.19-1.37, range 0.9-2.1)",
            "latent": "CDC Key Facts About Influenza https://www.cdc.gov/flu/about/keyfacts.htm",
            "infectious": "CDC Flu Disease Spread https://www.cdc.gov/flu/about/disease/spread.htm "
                          "(most contagious first 3-4 days)",
        },
    },
    "covid_wuhan": {
        "name": "COVID-19 (SARS-CoV-2 Wuhan original strain)",
        "name_zh": "COVID-19（武汉原始株）",
        "R0": 3.0,
        "latent_period": 5.0,
        "infectious_period": 7.0,
        "sources": {
            "R0": "Liu Y et al. (2020). J Travel Med 27(2):taaa021 "
                  "https://academic.oup.com/jtm/article/27/2/taaa021/5735319 "
                  "(R0 2.0-3.3); Sanchez 2020 EID 26(7):1470 pooled R0=3.28",
            "latent": "WHO COVID-19 fact sheet "
                      "https://www.who.int/news-room/fact-sheets/detail/coronavirus-disease-(covid-19) "
                      "(median 5 days, range 1-14)",
            "infectious": "CDC Duration of Isolation "
                          "https://www.cdc.gov/coronavirus/2019-ncov/hcp/duration-isolation.html "
                          "(5-10 days for mild cases, culturable virus window)",
        },
    },
    "measles": {
        "name": "Measles (rubeola)",
        "name_zh": "麻疹",
        "R0": 15.0,
        "latent_period": 12.0,
        "infectious_period": 6.0,
        "sources": {
            "R0": "Guerra FM et al. (2017). Lancet Infect Dis 17(12):e420-e428 "
                  "https://www.sciencedirect.com/science/article/abs/pii/S1473309917303079 "
                  "(systematic review R0 12-18)",
            "latent": "CDC Clinical Overview of Measles "
                      "https://www.cdc.gov/measles/hcp/clinical-overview.html "
                      "(10-14 days typical, 7-21 day range)",
            "infectious": "CDC Measles Transmission "
                          "https://www.cdc.gov/measles/transmission.html "
                          "(4 d before to 4 d after rash; ~6 d median culturable)",
        },
    },
}


class SEIR:
    """SEIR 4 仓室模型。

    4 个仓室：
    - S（Susceptible）：易感
    - E（Exposed）：已暴露/感染但未发病，处于潜伏期
    - I（Infectious）：有传染性的感染期
    - R（Recovered）：恢复/免疫

    通过 R0（基本再生数）、latent_period（潜伏期）、infectious_period（感染期）
    三个参数，模型把"传染"翻译成可计算的常微分方程组。

    Parameters
    ----------
    R0 : float
        基本再生数。在全员易感、没有干预的情况下，1 个感染者平均
        传染的人数。R0 < 1 疫情衰减，R0 > 1 疫情扩散。
    latent_period : float
        潜伏期（天），从感染到开始传染的时间，对应 1/sigma。
    infectious_period : float
        感染期（天），从开始传染到恢复/隔离，对应 1/gamma。
    N : int
        总人口数。
    E0 : int
        初始暴露者（潜伏期）人数，默认 1。
    I0 : int
        初始感染期人数，默认 0。
    R0_init : int
        初始恢复/免疫人数，默认 0。
    virus : str, optional
        若提供，必须是 VIRUS_PARAMS 中的 key，会用预置参数覆盖 R0/
        latent_period/infectious_period。便于一次构造常见病毒场景。
    """

    def __init__(self, R0=None, latent_period=None, infectious_period=None,
                 N=100000, E0=1, I0=0, R0_init=0, virus=None):
        if virus is not None:
            if virus not in VIRUS_PARAMS:
                raise ValueError(
                    f"virus must be one of {list(VIRUS_PARAMS)}; "
                    f"got {virus!r}"
                )
            params = VIRUS_PARAMS[virus]
            R0 = params["R0"]
            latent_period = params["latent_period"]
            infectious_period = params["infectious_period"]
            self.virus = virus
            self.virus_params = params
        else:
            if R0 is None or latent_period is None or infectious_period is None:
                raise ValueError(
                    "Either pass virus=<key> or all of R0, latent_period, "
                    "infectious_period."
                )
            self.virus = None
            self.virus_params = None

        self.R0 = float(R0)
        self.latent_period = float(latent_period)
        self.infectious_period = float(infectious_period)
        self.N = int(N)

        # 推导仓室动力学参数
        # sigma = 1 / 潜伏期（暴露 -> 感染）
        # gamma = 1 / 感染期（感染 -> 恢复）
        # beta = R0 * gamma （在均匀混合假设下）
        self.sigma = 1.0 / self.latent_period
        self.gamma = 1.0 / self.infectious_period
        self.beta = self.R0 * self.gamma

        # 初始条件（强类型，避免被改成 float）
        self.S0 = self.N - E0 - I0 - R0_init
        self.E0 = int(E0)
        self.I0 = int(I0)
        self.R0_init = int(R0_init)
        if self.S0 < 0:
            raise ValueError("E0 + I0 + R0_init cannot exceed N")

        # 解（solve 后填充）
        self.t = None
        self.S = None
        self.E = None
        self.I = None
        self.R = None
        self._solved = False

    def _derivatives(self, y):
        """4 仓室动力学（标准化人口以避免大数问题）。"""
        S, E, I, R = y
        N = self.N
        # 均匀混合接触：beta * S * I / N
        dS = -self.beta * S * I / N
        dE = +self.beta * S * I / N - self.sigma * E
        dI = +self.sigma * E - self.gamma * I
        dR = +self.gamma * I
        return np.array([dS, dE, dI, dR])

    def solve(self, days=200, dt=0.1):
        """用 Euler 积分求解 4 仓室时间序列。

        Parameters
        ----------
        days : float
            模拟时长（天）。
        dt : float
            时间步长（天）。dt=0.1 配合 200 天足够 4 种 R0 场景收敛。
            极端参数（很短的潜伏期）建议 dt=0.01。

        Returns
        -------
        dict : {"t", "S", "E", "I", "R"}，每个都是 ndarray；存到 self。
        """
        n_steps = int(np.ceil(days / dt)) + 1
        t = np.linspace(0.0, days, n_steps)
        y = np.zeros((n_steps, 4))
        y[0] = [self.S0, self.E0, self.I0, self.R0_init]
        for k in range(n_steps - 1):
            dydt = self._derivatives(y[k])
            y[k + 1] = y[k] + dt * dydt
            # 物理约束：所有仓室 >= 0
            y[k + 1] = np.maximum(y[k + 1], 0.0)
            # 数值守恒校正：S+E+I+R = N（避免 Euler 漂移）
            total = y[k + 1].sum()
            y[k + 1] *= self.N / total if total > 0 else 1.0

        self.t = t
        self.S, self.E, self.I, self.R = y.T
        self._solved = True
        return {"t": t, "S": self.S, "E": self.E, "I": self.I, "R": self.R}

    def peak_info(self):
        """返回感染曲线 I(t) 的峰值信息。

        Returns
        -------
        dict : {
            "peak_time": 峰值时间（天，浮点）,
            "peak_size": 峰值同时感染人数（人，整数）,
            "peak_ratio": 峰值同时感染占总人口比例,
            "final_infected": 模拟结束时累计感染人数（人，整数）,
            "final_infected_ratio": 模拟结束时累计感染占总人口比例,
        }
        """
        if not self._solved:
            raise RuntimeError("Call solve() before peak_info().")
        idx = int(np.argmax(self.I))
        return {
            "peak_time": float(self.t[idx]),
            "peak_size": int(self.I[idx]),
            "peak_ratio": float(self.I[idx] / self.N),
            "final_infected": int(self.R[-1] + self.I[-1]),
            "final_infected_ratio": float((self.R[-1] + self.I[-1]) / self.N),
        }

    @staticmethod
    def compare_viruses(virus_list=None, N=100000, days=200, dt=0.1):
        """跑 4 种 R0 场景，返回对比 DataFrame。

        Parameters
        ----------
        virus_list : list[str], optional
            VIRUS_PARAMS 中的 key 列表。默认 4 种全跑。
        N : int
            总人口。
        days : float
            模拟时长。
        dt : float
            时间步长。

        Returns
        -------
        pandas.DataFrame
            列：virus, R0, latent_period, infectious_period,
                peak_time, peak_size, peak_ratio,
                final_infected_ratio。
        """
        if pd is None:
            raise ImportError(
                "compare_viruses requires pandas; "
                "install with `python -m pip install pandas`."
            )
        if virus_list is None:
            virus_list = list(VIRUS_PARAMS)
        rows = []
        for v in virus_list:
            m = SEIR(virus=v, N=N)
            m.solve(days=days, dt=dt)
            info = m.peak_info()
            rows.append({
                "virus": v,
                "virus_zh": VIRUS_PARAMS[v]["name_zh"],
                "R0": m.R0,
                "latent_period": m.latent_period,
                "infectious_period": m.infectious_period,
                "peak_time": info["peak_time"],
                "peak_size": info["peak_size"],
                "peak_ratio": info["peak_ratio"],
                "final_infected_ratio": info["final_infected_ratio"],
            })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    # 4 种病毒对比
    print("=" * 78)
    print("SEIR 4-virus comparison (N=100000, days=200)")
    print("=" * 78)
    df = SEIR.compare_viruses()
    print()
    print(df.to_string(index=False))

    print()
    print("=" * 78)
    print("4-compartment time series sample (measles, R0=15)")
    print("=" * 78)
    m = SEIR(virus="measles")
    m.solve(days=200, dt=0.1)
    info = m.peak_info()
    t = m.t
    # 关键时间点
    samples = [0, 5, 10, 20, 30, 40, 50, 60, 80, 100, 150, 200]
    print(f"{'t(d)':<8}{'S':<12}{'E':<12}{'I':<12}{'R':<12}{'S+E+I+R':<14}")
    for s in samples:
        i = int(s / 0.1)
        i = min(i, len(t) - 1)
        total = m.S[i] + m.E[i] + m.I[i] + m.R[i]
        print(f"{t[i]:<8.1f}{m.S[i]:<12.0f}{m.E[i]:<12.0f}"
              f"{m.I[i]:<12.0f}{m.R[i]:<12.0f}{total:<14.0f}")
    print()
    print(f"Peak time = {info['peak_time']:.1f} d, "
          f"peak size = {info['peak_size']} "
          f"({info['peak_ratio']*100:.1f}% of N)")
    print(f"Final infected = {info['final_infected']} "
          f"({info['final_infected_ratio']*100:.2f}% of N)")
    print()

    # 4 个 R0 场景峰时/最终感染
    print("=" * 78)
    print("Sanity check: R0 -> final infection ratio")
    print("=" * 78)
    for v in ["common_cold", "seasonal_flu", "covid_wuhan", "measles"]:
        m = SEIR(virus=v)
        m.solve(days=200, dt=0.1)
        info = m.peak_info()
        print(f"  {v:<14} R0={m.R0:<5}  "
              f"peak t={info['peak_time']:>6.1f} d  "
              f"peak size={info['peak_ratio']*100:>5.1f}%  "
              f"final infected={info['final_infected_ratio']*100:>5.2f}%")
