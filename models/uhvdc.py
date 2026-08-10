"""
UHVDC (特高压直流) 输电线路简化物理模型。

UHVDC vs HVAC：
- UHVDC：1000-3000 km 长距离、点对点大容量输电、总损耗 ~5-7%
- HVAC：500-1000 km 短距离、网状互联、长距离损耗 8-15%
- 长距离 + 大容量 + 异步联网 → UHVDC 唯一可行方案

核心物理（双极直流，V 为单极对地电压，±1100 kV 即 V = 1100 kV）：
    输电容量        P = 2·V·I     (双极两线，各带电流 I)
    电流            I = P / (2·V)
    线路损耗        P_line = 2 · I² · R_dc           (双线返回，R_dc 为单根导线等效电阻)
    换流站损耗      P_conv = (per-station %) × P     (两端各一次 AC/DC 变换)
    总损耗          P_loss = P_line + P_conv
    输电效率        η = (P - P_loss) / P

关键参数（本文默认值，联网核实见 References 区）：
- 最高电压等级 ±1100 kV（昌吉-古泉）
- 单条线路容量 12000 MW（昌吉-古泉）
- 输电距离 1000-3300 km（±800 kV 通常 ~1600 km；±1100 kV ~3300 km）
- 直流线路损耗 3-5%（不含换流站）
- 换流站损耗 0.6-0.8% 每端（CIGRE TB 553 / B4-52）
- 线路电阻 0.01-0.03 Ω/km（JL/G3A-1250/70 导线典型，8 分分裂）
- 4 种电源容量系数：水 50%、火 55%、风 25%、光 17%（中位）

模型边界（教学型简化）：
- 假设双极单回线路、均匀满载
- 不考虑节点潮流、稳定性约束、天气对线路电阻的影响
- 不覆盖调度策略、储能配套
- 不含政治、经济因素

所有物理参数都联网核实（每条至少 1 个 URL），见 References。
docstring 风格与 models/seir.py / models/pv_distribution.py 保持一致
（中文 + 来源 + URL）。

References (all parameters verified by web lookup):

[1] 昌吉-古泉 ±1100 kV 特高压直流（吉泉直流，世界最高等级）
    - 电压 ±1100 kV、容量 12000 MW、距离 3293-3324 km、2019 投运
    - 8×JL/G3A-1250/70 八分裂导线，额定电流 5457 A
    - 2024 年输电量 683.73 亿 kWh（同比 +10.27%）
    - 北极星智能电网：http://www.chinasmartgrid.com.cn/special/?id=630319
    - 国家电网微博：https://www.weibo.com/1730306175/Oiau5mBWO
    - 思源电气：http://www.sieyuan.com/news/show-426.html
    - 昌吉换流站 2024 输电数据：https://www.sohu.com/a/846803405_121072318
    - 工程院论文：https://www.engineering.org.cn/sscae/attachs/2019/04/24/07-cai.pdf
    - 百度百科：https://baike.baidu.com/item/昌吉—古泉±1100千伏特高压直流输电工程/20269684

[1b] 交流对比基准（引言：500 kV 一回线满载约 1000 MW）
    - 500 kV 常规型单回交流线路自然输送功率约 1000 MW（紧凑型约 1300-1370 MW）
    - 对比：昌吉-古泉 ±1100 kV 直流单线 12000 MW ≈ 12 回 500 kV 交流
    - 1000+ km + 大容量是交流的天花板（电容充电 + 同步稳定两条约束）
    - 特高压与超高压交流输电经济比较研究：
      https://www.china5e.com/energy/news-928930-1.html
      https://shupeidian.bjx.com.cn/html/20150709/639954.shtml

[2] 4 条参考 UHVDC 线路（±800 kV 与 ±1100 kV）
    - 锡盟-泰州：±800 kV, 10000 MW, ~1620 km, 2017 投运
      https://www.cspplaza.com/article-10653-1.html
      https://news.bjx.com.cn/html/20170621/832374.shtml
    - 青海-河南：±800 kV, 8000 MW, ~1587 km, 2020 投运（首条 100% 清洁能源外送）
      https://baike.baidu.com/item/青海—河南±800千伏特高压直流工程/23143328
      https://www.seetao.com/details/27129.html
    - 白鹤滩-江苏：±800 kV, 8000 MW, ~2080 km, 2022 投运（首次"常规+柔性"混合级联）
      https://baike.baidu.com/item/白鹤滩-江苏±800千伏特高压直流输电工程/59716348
      http://www.cepca.org.cn/news/show-25267.html

[3] 换流站损耗（CIGRE TB 553 / B4-52）
    - 晶闸管阀损耗 0.6-0.8% 每端（占换流站总损 30-40%）
    - 换流变压器 0.6-0.9%、平波电抗器 0.1-0.2%、滤波器 0.1-0.4%、辅助 0.05-0.1%
    - 换流站总损 ~1.5-2.0% 每端；双极（两端合计）~3.0-4.0%
    - ABB / Siemens / GE LCC-HVDC 技术手册一致
    - CIGRE B4-52 工作组（2011）HVDC grid feasibility study
      https://www.hanspub.org/reference/Reference.aspx?ReferenceID=111919

[4] 4 种电源容量系数（典型区间中位数）
    - 水电 45-55%（中位 50%）：调节性能好、可调度基荷
    - 火电 50-60%（中位 55%）：稳定、可调度基荷
    - 风电 20-30%（中位 25%）：波动大，需配套储能/灵活性电源
    - 光伏 15-20%（中位 17%）：昼夜波动，极难单独调度
    - IEA《Renewables 2024》报告：
      https://www.docin.com/p-4745889639.html
    - 中国 2024 实际利用小时（中电联 / 国家能源局 2025-01）：
      水电 3442 h（39%）、火电 3988 h（46%）、风电 1931 h（22%）、光伏 1132 h（13%）
      https://www.nea.gov.cn/20250121/097bfd7c1cd3498897639857d86d5dac/c.html
      https://xueqiu.com/4079886420/321882383
      （2024 中国实际略低于"典型区间中位"，因来水偏枯 + 新能源装机激增）
    - IEA 2025 全球电力展望：
      https://so.html5.qq.com/rain/a/20251201A03GU100

[5] 直流线路电阻 / 导线
    - JL/G3A-1250/70 钢芯铝绞线（UHVDC 主流）：单根正序电阻 ~0.021 Ω/km
    - 昌吉-古泉 8×JL/G3A-1250/70 八分裂，等效 ~0.0026 Ω/km 每极
    - LGJ-300/40 单根 0.096 Ω/km（用于 ±500 kV 等级）
    - 线路电阻 0.01-0.03 Ω/km 区间对应 6-8 分分裂大截面导线
    - 甘肃特高压工程导线数据：
      https://www.toutiao.com/article/7481568213990507044/
    - 思源电气导线选型：http://www.sieyuan.com/news/show-426.html
    - LGJ 参数表：https://www.docin.com/p-4272469080.html

[6] 减碳计算参数
    - 中国平均供电煤耗 ~320 g 煤/kWh（"供电煤耗"含厂用电损耗）
    - IPCC 2006 默认排放因子：94,600 t CO2/TJ ≈ 2.66 kg CO2/kg 煤
      （other bituminous coal 烟煤，含碳量 ~55-60%）
    - 中国煤电实际范围 2.4-2.8 kg CO2/kg 煤，本文取中位 2.66
    - 单条 12000 MW UHVDC 满载年输电：
      12000 × 8760 × 0.95 = 99,864,000 MWh ≈ 998.64 亿 kWh（容量系数 95%）
    - 国家能源局 / 中电联 2024 年报：
      https://www.cpnn.com.cn/news/hy/202501/t20250126_1769420.html
    - 中国 2024 年 CO2 排放总量 ~111.7 亿 t（BP 口径，多机构引用；文章取约数 110 亿 t）：
      https://www.worldometers.info/co2-emissions/china-co2-emissions/
    - 深圳市 2024 年全社会用电量 1214.9 亿 kWh（南方电网深圳供电局，年用电量首破 1200 亿 kWh）；
      按 320 g 煤/kWh × 2.66 kg CO2/kg 煤 ≈ 1.03 亿 t CO2（文章取约 1 亿 t）：
      https://www.sz.gov.cn/cn/xxgk/zfxxgj/zwdt/content/post_11955463.html
      https://www.news.cn/fortune/20250111/25883bdcd51445edb7280dd3593ce852/c.html

[7] 中国 2024 跨区跨省输电 / 总用电量
    - 跨区跨省合计约 2.5 万亿 kWh（跨区 8506 亿 + 跨省 1.59 万亿，2024 年 1-11 月）
    - 全社会用电量 9.4-9.85 万亿 kWh（同比 +6.8%）
    - 国家能源局：http://www.nea.gov.cn/20250121/097bfd7c1cd3498897639857d86d5dac/c.html
    - 中电联预测报告：http://www.cpnn.com.cn/news/hy/202501/t20250126_1769420.html

Usage:
    >>> line = UHVDC(voltage_kV=1100, capacity_MW=12000, distance_km=3293)
    >>> print(f"Line loss: {line.line_loss():.0f} MW")
    >>> print(f"Total loss: {line.total_loss():.0f} MW")
    >>> print(f"Efficiency: {line.efficiency()*100:.1f}%")
    >>> print(f"Annual coal saved: {line.annual_coal_saved():.0f} t")
    >>> print(f"Annual CO2 reduced: {line.annual_co2_reduced():.0f} t")
    >>> df = UHVDC.compare_4_sources()
    >>> print(df)
    >>> df2 = UHVDC.compare_voltage_levels()
    >>> print(df2)
"""

import numpy as np

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


# -----------------------------------------------------------------------------
# UHVDC 默认参数（联网核实中位数）
# -----------------------------------------------------------------------------
# 4 种电源容量系数（典型区间中位，IEA / CNREC）
CAPACITY_FACTORS = {
    "hydro": 0.50,    # 水电 45-55%（可调度基荷）
    "thermal": 0.55,  # 火电 50-60%（稳定基荷）
    "wind": 0.25,     # 风电 20-30%（波动）
    "solar": 0.17,    # 光伏 15-20%（昼夜波动）
}

# 换流站损耗：CIGRE TB 553 / B4-52 晶闸管阀 0.6-0.8% 每端
# 取中位 0.7%/端 × 2 端 = 1.4% 总换流站损耗
CONVERTER_LOSS_PER_STATION = 0.007  # 0.7% 每端
NUM_CONVERTER_STATIONS = 2           # 送端 + 受端

# UHVDC 满载 / 容量系数（昌吉-古泉等长距离重载线路近满载）
DEFAULT_CAPACITY_FACTOR = 0.95

# 减碳参数
DEFAULT_COAL_RATE_G_PER_KWH = 320.0   # g 煤/kWh（中国平均供电煤耗）
DEFAULT_CO2_PER_COAL_KG = 2.66        # kg CO2/kg 煤（IPCC 2006 default）

# 线路电阻（典型 UHVDC 大截面导线，**单根**电阻区间中位）
# 注：实际 UHVDC 用 6-8 分分裂导线，每极等效 = 单根 / N_sub
#      昌吉-古泉 8×JL/G3A-1250/70：单根 0.022 Ω/km，每极等效 ~0.00275 Ω/km
#      公式 P_loss = 2*I^2*R*L 直接代入单根值（保守高估）
#      想要更接近工程实测的损耗率，传每极等效值（约 0.002-0.003）
DEFAULT_LINE_RESISTANCE_OHM_PER_KM = 0.025  # Ω/km（0.01-0.03 单根区间中位）

# 参考 UHVDC 线路（4 条联网核实）
REFERENCE_LINES = {
    "changji_guquan": {
        "name_zh": "昌吉-古泉",
        "voltage_kV": 1100,
        "capacity_MW": 12000,
        "distance_km": 3293,
        "source": "火电+风电+光伏，2019 投运，世界最高等级",
    },
    "ximeng_taizhou": {
        "name_zh": "锡盟-泰州",
        "voltage_kV": 800,
        "capacity_MW": 10000,
        "distance_km": 1620,
        "source": "火电+风电，2017 投运，世界首个 10 GW 级 ±800 kV",
    },
    "qinghai_henan": {
        "name_zh": "青海-河南",
        "voltage_kV": 800,
        "capacity_MW": 8000,
        "distance_km": 1587,
        "source": "100% 清洁能源（水电+风电+光伏），2020 投运",
    },
    "baihetan_jiangsu": {
        "name_zh": "白鹤滩-江苏",
        "voltage_kV": 800,
        "capacity_MW": 8000,
        "distance_km": 2080,
        "source": "水电，2022 投运，首次常规+柔性混合级联",
    },
}


class UHVDC:
    """UHVDC 特高压直流输电线路简化模型。

    物理结构：
        送端换流站 (AC→DC, 损 ~0.7%)
              |
        直流线路（双极，损 P = 2·I²·R·L）
              |
        受端换流站 (DC→AC, 损 ~0.7%)

    Parameters
    ----------
    voltage_kV : float
        直流电压等级的绝对值（kV），如 1100 表示 ±1100 kV。
    capacity_MW : float
        额定输电容量（MW）。
    distance_km : float
        输电距离（km）。
    capacity_factor : float, optional
        容量系数（0-1），用于年输电量计算。默认 0.95（满载场景）。
    line_resistance_ohm_per_km : float, optional
        直流线路等效电阻（Ω/km）。默认 0.025（典型 UHVDC 8 分分裂
        大截面导线 0.01-0.03 Ω/km 区间中位值）。
    converter_loss_per_station : float, optional
        换流站单端损耗率（0-1）。默认 0.007（CIGRE TB 553 晶闸管阀中位 0.7%）。
    num_stations : int, optional
        换流站数量。默认 2（送端 + 受端）。
    coal_rate_g_per_kWh : float, optional
        替代煤率（g 煤/kWh）。默认 320（中国平均供电煤耗）。
    co2_per_coal_kg : float, optional
        CO2 排放系数（kg CO2/kg 煤）。默认 2.66（IPCC 2006 default）。
    """

    def __init__(self, voltage_kV, capacity_MW, distance_km,
                 capacity_factor=DEFAULT_CAPACITY_FACTOR,
                 line_resistance_ohm_per_km=DEFAULT_LINE_RESISTANCE_OHM_PER_KM,
                 converter_loss_per_station=CONVERTER_LOSS_PER_STATION,
                 num_stations=NUM_CONVERTER_STATIONS,
                 coal_rate_g_per_kWh=DEFAULT_COAL_RATE_G_PER_KWH,
                 co2_per_coal_kg=DEFAULT_CO2_PER_COAL_KG):
        if voltage_kV <= 0:
            raise ValueError(f"voltage_kV must be > 0, got {voltage_kV}")
        if capacity_MW <= 0:
            raise ValueError(f"capacity_MW must be > 0, got {capacity_MW}")
        if distance_km <= 0:
            raise ValueError(f"distance_km must be > 0, got {distance_km}")

        self.voltage_kV = float(voltage_kV)
        self.capacity_MW = float(capacity_MW)
        self.distance_km = float(distance_km)
        self.capacity_factor = float(capacity_factor)
        self.line_resistance_ohm_per_km = float(line_resistance_ohm_per_km)
        self.converter_loss_per_station = float(converter_loss_per_station)
        self.num_stations = int(num_stations)
        self.coal_rate_g_per_kWh = float(coal_rate_g_per_kWh)
        self.co2_per_coal_kg = float(co2_per_coal_kg)

        # 派生量
        # 双极 DC 系统：pole-to-ground 电压 = voltage_kV；
        # pole-to-pole 电压 = 2 × voltage_kV
        # 每极电流 I_pole = P / V_pp = P / (2 × V_pg)
        # （昌吉-古泉 12000 MW / ±1100 kV：I_pole = 5457 A，与官方额定电流一致）
        self.current_kA = self.capacity_MW / (2.0 * self.voltage_kV)
        # 总线路电阻（每极，× 距离）
        self.line_resistance_total_ohm = (
            self.line_resistance_ohm_per_km * self.distance_km
        )

    # -------------------------------------------------------------------------
    # 损耗计算
    # -------------------------------------------------------------------------
    def line_loss(self):
        """直流线路损耗（MW），双线返回：P_loss = 2 × I² × R_dc。

        Returns
        -------
        float : 线路损耗（MW）。
        """
        # I² 单位 A²，R 单位 Ω → W；× 2 双线；/ 1e6 → MW
        return 2.0 * (self.current_kA * 1000.0) ** 2 * self.line_resistance_total_ohm / 1e6

    def converter_loss(self):
        """两端换流站损耗（MW），每端按容量 × 损耗率。

        Returns
        -------
        float : 换流站损耗（MW）。
        """
        return self.capacity_MW * self.converter_loss_per_station * self.num_stations

    def total_loss(self):
        """线路 + 换流站总损耗（MW）。

        Returns
        -------
        float : 总损耗（MW）。
        """
        return self.line_loss() + self.converter_loss()

    def efficiency(self):
        """输电效率 =(capacity - total_loss) / capacity。

        Returns
        -------
        float : 输电效率（0-1）。
        """
        loss = self.total_loss()
        return (self.capacity_MW - loss) / self.capacity_MW

    # -------------------------------------------------------------------------
    # 年输电 / 减碳
    # -------------------------------------------------------------------------
    def annual_transmission(self, capacity_factor=None):
        """年输电量（GWh）= capacity × 8760 × capacity_factor / 1000。

        Parameters
        ----------
        capacity_factor : float, optional
            容量系数（0-1）。默认使用 self.capacity_factor。

        Returns
        -------
        float : 年输电量（GWh）。
        """
        cf = self.capacity_factor if capacity_factor is None else float(capacity_factor)
        # capacity × 8760 h → MWh；/ 1000 → GWh
        return self.capacity_MW * 8760.0 * cf / 1000.0

    def annual_coal_saved(self, coal_rate_g_per_kWh=None):
        """年替代煤量（吨）= 年输电量 × 煤率。

        Parameters
        ----------
        coal_rate_g_per_kWh : float, optional
            替代煤率（g 煤/kWh）。默认 self.coal_rate_g_per_kWh。

        Returns
        -------
        float : 年替代煤量（吨）。
        """
        rate = self.coal_rate_g_per_kWh if coal_rate_g_per_kWh is None else float(coal_rate_g_per_kWh)
        # 年输电量 GWh → kWh：× 1e6
        # g 煤 = kWh × g/kWh
        # t 煤 = g / 1e6
        gwh = self.annual_transmission()
        kwh = gwh * 1e6
        return kwh * rate / 1e6

    def annual_co2_reduced(self, co2_per_coal_kg=None):
        """年 CO2 减排量（吨）= 年替代煤量 × CO2 系数。

        Parameters
        ----------
        co2_per_coal_kg : float, optional
            CO2 排放系数（kg CO2/kg 煤）。默认 self.co2_per_coal_kg。

        Returns
        -------
        float : 年 CO2 减排（吨）。
        """
        coef = self.co2_per_coal_kg if co2_per_coal_kg is None else float(co2_per_coal_kg)
        coal_t = self.annual_coal_saved()
        # 1 t 煤 → 1000 kg 煤 → × coef kg CO2 → t CO2
        return coal_t * 1000.0 * coef / 1000.0

    # -------------------------------------------------------------------------
    # 静态方法：对比
    # -------------------------------------------------------------------------
    @staticmethod
    def compare_4_sources(sources=None, voltage_kV=800, distance_km=2000,
                          capacity_MW=10000,
                          capacity_factor=DEFAULT_CAPACITY_FACTOR):
        """4 种电源（水/火/风/光）对比 + 减碳量。

        Parameters
        ----------
        sources : iterable of str, optional
            电源类型列表（"hydro"/"thermal"/"wind"/"solar"）。默认 4 种全跑。
        voltage_kV : float, optional
            直流电压等级。默认 800。
        distance_km : float, optional
            输电距离。默认 2000。
        capacity_MW : float, optional
            额定容量。默认 10000。
        capacity_factor : float, optional
            容量系数。默认 0.95。

        Returns
        -------
        pandas.DataFrame : 4 行 × 7 列。
            列：source, name_zh, capacity_factor, annual_GWh,
                annual_coal_t, annual_co2_t, line_loss_MW
        """
        if pd is None:
            raise ImportError(
                "compare_4_sources requires pandas; "
                "install with `python -m pip install pandas`."
            )

        name_zh_map = {
            "hydro": "水电",
            "thermal": "火电",
            "wind": "风电",
            "solar": "光伏",
        }
        if sources is None:
            sources = list(CAPACITY_FACTORS)

        rows = []
        for src in sources:
            if src not in CAPACITY_FACTORS:
                raise ValueError(
                    f"source must be one of {list(CAPACITY_FACTORS)}; got {src!r}"
                )
            cf = CAPACITY_FACTORS[src]
            line = UHVDC(
                voltage_kV=voltage_kV,
                capacity_MW=capacity_MW,
                distance_km=distance_km,
                capacity_factor=capacity_factor,
            )
            annual_gwh = line.annual_transmission(capacity_factor=cf)
            # 重建 line 用于不同容量系数的减碳计算
            line.cf_actual = cf
            # 复用年输电 + 减碳公式
            coal_t = annual_gwh * 1e6 * line.coal_rate_g_per_kWh / 1e6
            co2_t = coal_t * 1000.0 * line.co2_per_coal_kg / 1000.0
            rows.append({
                "source": src,
                "name_zh": name_zh_map[src],
                "capacity_factor": cf,
                "annual_GWh": annual_gwh,
                "annual_coal_t": coal_t,
                "annual_co2_t": co2_t,
                "line_loss_MW": line.line_loss(),
            })
        return pd.DataFrame(rows)

    @staticmethod
    def compare_voltage_levels(voltages=(500, 800, 1100), capacity_MW=10000,
                                distance_km=2000,
                                capacity_factor=DEFAULT_CAPACITY_FACTOR):
        """3 种电压等级（±500 / ±800 / ±1100 kV）对比：电流、线路损耗、效率。

        Parameters
        ----------
        voltages : iterable of float
            电压等级列表（kV），如 (500, 800, 1100) 表示 ±500/±800/±1100 kV。
        capacity_MW : float, optional
            额定容量。默认 10000。
        distance_km : float, optional
            输电距离。默认 2000。
        capacity_factor : float, optional
            容量系数。默认 0.95。

        Returns
        -------
        pandas.DataFrame : n 行 × 6 列。
            列：voltage_kV, capacity_MW, current_kA, line_loss_MW,
                converter_loss_MW, total_loss_MW, efficiency_pct
        """
        if pd is None:
            raise ImportError(
                "compare_voltage_levels requires pandas; "
                "install with `python -m pip install pandas`."
            )

        rows = []
        for v in voltages:
            line = UHVDC(
                voltage_kV=float(v),
                capacity_MW=capacity_MW,
                distance_km=distance_km,
                capacity_factor=capacity_factor,
            )
            line_loss = line.line_loss()
            conv_loss = line.converter_loss()
            total_loss = line.total_loss()
            rows.append({
                "voltage_kV": v,
                "capacity_MW": capacity_MW,
                "current_kA": line.current_kA,
                "line_loss_MW": line_loss,
                "converter_loss_MW": conv_loss,
                "total_loss_MW": total_loss,
                "efficiency_pct": line.efficiency() * 100.0,
            })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=" * 78)
    print("UHVDC 4 种电源容量系数（联网核实中位）")
    print("=" * 78)
    for k, v in CAPACITY_FACTORS.items():
        print(f"  {k:<10} = {v*100:.0f}%")
    print()

    # ------------------------------------------------------------------
    # 1) 单条 12000 MW UHVDC 满载减碳量（昌吉-古泉场景）
    # ------------------------------------------------------------------
    print("=" * 78)
    print("昌吉-古泉 ±1100 kV / 12000 MW / 3293 km 满载（容量系数 95%）")
    print("=" * 78)
    cg = UHVDC(voltage_kV=1100, capacity_MW=12000, distance_km=3293)
    print(f"  电压等级        = ±{cg.voltage_kV:.0f} kV")
    print(f"  输电容量        = {cg.capacity_MW:.0f} MW")
    print(f"  输电距离        = {cg.distance_km:.0f} km")
    print(f"  额定电流        = {cg.current_kA:.3f} kA")
    print(f"  线路总电阻      = {cg.line_resistance_total_ohm:.2f} Ω")
    print(f"  线路损耗        = {cg.line_loss():.1f} MW ({cg.line_loss()/cg.capacity_MW*100:.2f}%)")
    print(f"  换流站损耗      = {cg.converter_loss():.1f} MW ({cg.converter_loss()/cg.capacity_MW*100:.2f}%)")
    print(f"  总损耗          = {cg.total_loss():.1f} MW ({cg.total_loss()/cg.capacity_MW*100:.2f}%)")
    print(f"  输电效率        = {cg.efficiency()*100:.2f}%")
    print()
    annual_gwh = cg.annual_transmission()
    coal_t = cg.annual_coal_saved()
    co2_t = cg.annual_co2_reduced()
    print(f"  年输电量        = {annual_gwh:.0f} GWh ({annual_gwh/1e2:.2f} 亿 kWh)")
    print(f"  年替代煤量      = {coal_t:.0f} t ({coal_t/1e4:.1f} 万 t/年)")
    print(f"  年 CO2 减排     = {co2_t:.0f} t ({co2_t/1e4:.1f} 万 t/年)")
    print()
    print(f"  预期区间：替代煤 3000-3500 万 t/年 → 实际 {coal_t/1e4:.0f} 万 t/年")
    print(f"  预期区间：CO2 减排 7800-9100 万 t/年 → 实际 {co2_t/1e4:.0f} 万 t/年")
    print()

    # ------------------------------------------------------------------
    # 1b) 昌吉-古泉（每极等效电阻 = 8 分分裂场景）→ 对齐文章 callout
    # ------------------------------------------------------------------
    # 上例用单根 R = 0.025 Ω/km（保守高估，演示极端）；实际昌吉-古泉用
    # 8×JL/G3A-1250/70 八分裂导线，每极等效 ≈ 0.003 Ω/km。
    print("=" * 78)
    print("昌吉-古泉（每极等效 R=0.003 Ω/km，8×JL/G3A-1250/70 八分裂）")
    print("=" * 78)
    cg_real = UHVDC(voltage_kV=1100, capacity_MW=12000, distance_km=3293,
                    line_resistance_ohm_per_km=0.003)
    print(f"  线路总电阻      = {cg_real.line_resistance_total_ohm:.2f} Ω")
    print(f"  线路损耗        = {cg_real.line_loss():.1f} MW ({cg_real.line_loss()/cg_real.capacity_MW*100:.2f}%)")
    print(f"  换流站损耗      = {cg_real.converter_loss():.1f} MW ({cg_real.converter_loss()/cg_real.capacity_MW*100:.2f}%)")
    print(f"  总损耗          = {cg_real.total_loss():.1f} MW ({cg_real.total_loss()/cg_real.capacity_MW*100:.2f}%)")
    print(f"  输电效率        = {cg_real.efficiency()*100:.2f}%")
    print()

    # ------------------------------------------------------------------
    # 2) 4 种电源对比（默认 ±800 kV, 2000 km, 10 GW）
    # ------------------------------------------------------------------
    print("=" * 78)
    print("4 种电源对比（±800 kV, 10000 MW, 2000 km）")
    print("=" * 78)
    df4 = UHVDC.compare_4_sources()
    print(df4.to_string(index=False, float_format=lambda x: f"{x:,.1f}"))
    print()

    # ------------------------------------------------------------------
    # 3) 3 种电压等级对比（10000 MW, 2000 km）
    # ------------------------------------------------------------------
    print("=" * 78)
    print("3 种电压等级对比（10000 MW, 2000 km）")
    print("=" * 78)
    df3 = UHVDC.compare_voltage_levels()
    print(df3.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))
    print()

    # ------------------------------------------------------------------
    # 4) 4 条参考 UHVDC 线路参数
    # ------------------------------------------------------------------
    print("=" * 78)
    print("4 条参考 UHVDC 线路")
    print("=" * 78)
    print(f"  {'线路':<14}{'电压':<10}{'容量(MW)':<12}{'距离(km)':<12}{'电源'}")
    print("  " + "-" * 74)
    for k, info in REFERENCE_LINES.items():
        print(f"  {info['name_zh']:<12}±{info['voltage_kV']:<8}"
              f"{info['capacity_MW']:<12}{info['distance_km']:<12}{info['source']}")
    print()

    # ------------------------------------------------------------------
    # 5) 单调性 sanity：电压越高，损耗越低
    # ------------------------------------------------------------------
    print("=" * 78)
    print("Sanity check: 电压 ↑ → 电流 ↓ → 损耗 ↓ (P_loss ∝ 1/V^2)")
    print("=" * 78)
    losses = df3["line_loss_MW"].values
    monotonic = all(losses[i] > losses[i + 1] for i in range(len(losses) - 1))
    print(f"  线路损耗单调递减：{monotonic}")
    print(f"  ±500 kV 损耗 = {losses[0]:.1f} MW")
    print(f"  ±800 kV 损耗 = {losses[1]:.1f} MW")
    print(f"  ±1100 kV 损耗 = {losses[2]:.1f} MW")
    print(f"  比值 (+/-500 / +/-1100) = {losses[0]/losses[2]:.2f}x "
          f"(理论 (1100/500)^2 = {(1100/500)**2:.2f}x)")