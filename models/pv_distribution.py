"""
4 节点低压配电网简化模型：分布式光伏并网对节点电压 / 反向潮流的影响。

模型结构（4 节点 / 3 段馈线，1 km 总长）：

    节点 0  (变压器低压侧，10 kV / 0.38 kV，固定 1.0 pu)
        |
        R1 = 0.1 Ω     (馈线第一段，约 0.33 km)
    节点 1
        |
        R2 = 0.1 Ω     (馈线第二段，约 0.33 km)
    节点 2
        |
        R3 = 0.1 Ω     (馈线第三段，约 0.33 km)
    节点 3             (馈线末端)

每段馈线电阻 0.1 Ω，总电阻 0.3 Ω，对应 1 km 长 0.4 kV 馈线
（电阻率 0.3 Ω/km；实测配电网馈线电阻率 0.1-0.3 Ω/km 区间中段值）。

核心物理（简化 DC Power Flow，单相近似 + 中性线 2 倍返回）：

    各节点净功率：    P_net_i = P_pv_i - P_load_i   (kW，注入为正)
    馈线段电流：      I_k     = -Σ_{i>k} P_net_i / V_phase
                              (流出变压器方向为正)
    馈线段压降：      ΔV_k   = -2 × I_k × R_k
    节点电压：        V_n     = V_0 + Σ_{k<=n} ΔV_k

物理含义：
    - 中午 PV 满发 + 最小负荷：P_net > 0，反向电流，节点电压升高（V_3 > V_0）
    - 夜间最大负荷 + 无 PV：  P_net < 0，正向电流，节点电压降低（V_3 < V_0）
    - 变压器侧（节点 0）固定 1.0 pu（10 kV 侧视为无穷大母线）

模型边界（教学型简化）：
    - 忽略 3 相不平衡、谐波、频率响应
    - 假设均匀负荷 / 均匀 PV 分布
    - 用 DC Power Flow 简化（实际 AC Power Flow 是非线性）
    - 实际工程用 Newton-Raphson 潮流；本模型保留关键物理（I·R 压降）即可定性分析

所有参数联网核实（每条至少 1 个 URL），见模块 docstring 末尾 References。
docstring 风格与 models/seir.py 保持一致（中文 + 来源 + URL）。

References (all parameters verified by web lookup):

[1] GB/T 12325-2008《电能质量 供电电压偏差》
    - 220 V 单相供电：+7% / -10%（198-235 V）
    - 380 V 三相供电：±7%（353-407 V）
    - 20 kV 及以下三相：±7%
    - 35 kV 及以上：正负偏差绝对值之和不超过 10%
    https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=75EBBCF838AA40D281EDA854B8F63AD7
    https://www.safehoo.com/Standard/Trade/Electric/202010/5613854.shtml

[2] 国家能源局《分布式光伏发电开发建设管理办法》（国能发新能规〔2025〕7号）
    - 自然人户用：自有住宅、连接点 ≤380 V，无硬性单户 kW 上限
    - 非自然人户用：≤10 (20) kV，≤6 MW 总装机
    - 2013 老办法曾规定单户 ≤5 kW；2025 新办法改为按主体性质 / 电压等级划分
    7 kW 为典型单户屋顶光伏装机中位数（市场实际数据）
    https://www.gov.cn/zhengce/202502/content_7004211.htm
    https://www.sohu.com/a/852453755_163278

[3] JGJ 242-2011《住宅建筑电气设计规范》
    - A 套（≤60 m²）：3 kW / 户；B 套（61-90 m²）：4 kW / 户
    - C 套（91-150 m²）：6 kW / 户；D 套（≥150 m²）：8 kW / 户
    7 kW 为常见 D 套设计容量，本文取中位数
    https://gf.1190119.com/article-16693.htm

[4] 国家电网 / 南方电网 配电网典型设计
    - 400 / 630 / 800 kVA 为常见配变容量等级
    - 0.4 kV 馈线长度 0.5-2 km（中位 1 km）
    - 馈线电阻 0.1-0.3 Ω/km（视导线截面 LGJ-120/150/185）
    https://max.book118.com/html/2021/0913/8142037104004003.shtm
    https://www.docin.com/p-2725938030.html

[5] 国家能源局 2024 年光伏发电建设情况（2025-01-23 发布会）
    - 截至 2024 年底分布式光伏累计装机 3.7 亿千瓦 (370 GW)
    - 2024 年新增分布式 1.2 亿千瓦 (120 GW)
    - 占全部光伏发电装机 42%
    https://news.mysteel.com/a/25012408/1CA43634FFD3587B.html
    https://www.ithome.com/0/826/764.htm

[6] IEEE Std 1547-2018《DER 并网与互操作标准》
    - Category A 正常运行电压范围：0.88-1.10 pu
    - 持续运行区间：0.95-1.05 pu
    - DER 应在区间内 ride-through，不脱网
    https://standards.ieee.org/ieee/1547/5915/

[7] 渗透率定义（学术通行）
    - 装机渗透率 (capacity penetration) = PV 装机容量 / 峰值负荷
    - 发电量渗透率 (energy penetration) = 年 PV 发电量 / 年用电量
    - 本文用前者（与电压越限直接相关）
    参考：IEA PVPS 报告系列、IEEE 1547 评估指南

Usage:
    >>> grid = DistributionGrid()
    >>> v = grid.solve_peak()           # 4 节点电压（pu）
    >>> print(v)
    >>> df = DistributionGrid.compare_penetration()
    >>> print(df)
    >>> limit = DistributionGrid().find_penetration_limit(max_voltage=1.07)
    >>> print(f"临界渗透率: {limit:.1%}")
"""

import numpy as np

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


# -----------------------------------------------------------------------------
# 4 节点低压配电网默认参数（联网核实中位数）
# -----------------------------------------------------------------------------
# 馈线参数：3 段 0.4 kV 馈线，每段 0.1 Ω，总长 1 km
# 电阻率 0.3 Ω/km（导线截面较大，如 LGJ-150/185）
FEEDER_RESISTANCE_PER_SEGMENT_OHM = 0.1
NUM_FEEDER_SEGMENTS = 3
FEEDER_TOTAL_LENGTH_KM = 1.0

# 基础电压：380 V 线电压 / 220 V 相电压
BASE_VOLTAGE_LINE_TO_LINE_V = 380.0
BASE_VOLTAGE_PHASE_V = 220.0

# 单户 PV / 负荷（联网核实中位数）
PV_PER_NODE_KW = 7.0          # 单户屋顶光伏典型装机
PEAK_LOAD_PER_NODE_KW = 7.0   # 单户峰值负荷（夏季空调 + 炊具 + 热水器）

# 变压器
TRANSFORMER_KVA = 400.0       # 配变典型容量
# 满载电流（二次侧 380 V）：400 / (√3 × 0.38) ≈ 608 A
TRANSFORMER_FULL_LOAD_CURRENT_A = (
    TRANSFORMER_KVA * 1000.0 / (np.sqrt(3) * BASE_VOLTAGE_LINE_TO_LINE_V)
)

# 渗透率定义
PENETRATION_DEFINITION = "capacity"   # 装机渗透率（本文）

# 中午最小负荷系数（worst case：中午 PV 满发时负荷最低）
# 用于电压_profile('noon') 场景；典型居民中午负荷约峰值 30%，
# 这里取 0 是因为模型目的就是演示反向潮流 / 电压越限的极端情况。
NOON_LOAD_FACTOR = 0.0

# 电压限值（GB/T 12325-2008）
VOLTAGE_UPPER_LIMIT_PU = 1.07   # 220 V 上限 235 V
VOLTAGE_LOWER_LIMIT_PU = 0.93   # 220 V 下限 198 V
# IEEE 1547-2018 上限 1.10 pu（持续运行）


class DistributionGrid:
    """4 节点低压配电网简化模型。

    物理结构：
    - 节点 0：变压器低压侧（10 kV / 0.38 kV，固定 1.0 pu）
    - 节点 1-3：3 个分支节点（每节点代表 1 户居民）
    - 3 段馈线，每段 0.1 Ω，总长 1 km

    Parameters
    ----------
    pv_per_node : float
        每节点 PV 装机（kW）。默认 7 kW（单户中位数）。
    peak_load_per_node : float
        每节点峰值负荷（kW）。默认 7 kW。
    transformer_kVA : float
        配变容量（kVA）。默认 400。
    feeder_resistance_per_km : float
        馈线电阻率（Ω/km）。默认 0.3（0.1 Ω / 段 × 3 段 / 1 km）。
        实际范围 0.1-0.3 Ω/km。
    base_voltage : float
        线电压（V）。默认 380。
    num_nodes : int
        馈线上的负荷节点数（不含节点 0）。默认 3。
    """

    def __init__(self, pv_per_node=PV_PER_NODE_KW,
                 peak_load_per_node=PEAK_LOAD_PER_NODE_KW,
                 transformer_kVA=TRANSFORMER_KVA,
                 feeder_resistance_per_km=0.3,
                 base_voltage=BASE_VOLTAGE_LINE_TO_LINE_V,
                 num_nodes=NUM_FEEDER_SEGMENTS):
        self.pv_per_node = float(pv_per_node)
        self.peak_load_per_node = float(peak_load_per_node)
        self.transformer_kVA = float(transformer_kVA)
        self.feeder_resistance_per_km = float(feeder_resistance_per_km)
        self.base_voltage = float(base_voltage)
        # 相电压 = 线电压 / √3（单相近似 + 中性线返回）
        self.base_voltage_phase = self.base_voltage / np.sqrt(3.0)
        self.num_nodes = int(num_nodes)

        # 馈线段电阻：每段长度 1 km / 3 段 = 0.333 km
        self.feeder_length_per_segment_km = FEEDER_TOTAL_LENGTH_KM / self.num_nodes
        self.feeder_resistance_per_segment = (
            self.feeder_resistance_per_km * self.feeder_length_per_segment_km
        )

        # 变压器满载电流（二次侧）
        self.transformer_full_load_current_A = (
            self.transformer_kVA * 1000.0 / (np.sqrt(3.0) * self.base_voltage)
        )

        # PV 装机（默认每节点相等，存为 dict 便于 add_pv 修改）
        self.pv_installed = {
            i: self.pv_per_node for i in range(1, self.num_nodes + 1)
        }

    def add_pv(self, node_id, pv_kw):
        """在某节点追加 PV 装机（kW）。

        Parameters
        ----------
        node_id : int
            节点编号（1 到 num_nodes）。
        pv_kw : float
            追加的 PV 容量（kW）。会累加到现有值。
        """
        if node_id < 1 or node_id > self.num_nodes:
            raise ValueError(
                f"node_id must be 1-{self.num_nodes}, got {node_id}"
            )
        self.pv_installed[node_id] = (
            self.pv_installed.get(node_id, 0.0) + float(pv_kw)
        )

    # -------------------------------------------------------------------------
    # 内部潮流计算
    # -------------------------------------------------------------------------
    def _node_net_power(self, pv_factor, load_factor):
        """各节点净功率（kW），正 = 注入电网。

        Parameters
        ----------
        pv_factor : float
            PV 出力系数（0-1），1.0 = 满发。
        load_factor : float
            负荷系数（相对峰值），0.0 = 最小，1.0 = 峰值。

        Returns
        -------
        list[float] : 节点 1 到 num_nodes 的净功率（kW）。
        """
        p_net = []
        for i in range(1, self.num_nodes + 1):
            pv_kw = self.pv_installed.get(i, 0.0) * pv_factor
            load_kw = self.peak_load_per_node * load_factor
            p_net.append(pv_kw - load_kw)
        return p_net

    def _segment_currents(self, p_net):
        """各段馈线电流（A），流出变压器方向为正。

        Parameters
        ----------
        p_net : list[float]
            各节点净功率（kW），正 = 注入。

        Returns
        -------
        list[float] : 段 1 到 num_nodes 的电流（A）。
                      正值 = 电流从变压器流出（负荷消耗）
                      负值 = 电流流入变压器（PV 反向潮流）
        """
        # 段 k（节点 k-1 与 k 之间）承载节点 k 及其下游所有净功率
        # 下游累积净功率 = Σ_{i>=k} P_net_i
        # I_k = -下游累积 / V_phase
        #   （下游净注入为正时，电流从下游流向变压器，方向与"流出"相反）
        currents = []
        downstream_net_kw = 0.0
        for k in range(self.num_nodes, 0, -1):
            downstream_net_kw += p_net[k - 1]
            i_seg = -downstream_net_kw * 1000.0 / self.base_voltage_phase
            currents.insert(0, i_seg)
        return currents

    def _voltages_from_currents(self, currents):
        """根据段电流计算各节点电压（V，含节点 0）。

        单相近似 + 中性线返回：ΔV_k = -2 × I_k × R_k
        （电流流出变压器时，电压沿馈线下降；电流流入变压器时，电压上升）
        """
        v0 = self.base_voltage_phase
        r = self.feeder_resistance_per_segment
        voltages = [v0]
        v = v0
        for i_seg in currents:
            v = v - 2.0 * i_seg * r
            voltages.append(v)
        return voltages

    def _solve(self, pv_factor, load_factor):
        """通用潮流求解。返回 (节点电压 V、段电流 I、节点净功率 P_net)。"""
        p_net = self._node_net_power(pv_factor, load_factor)
        currents = self._segment_currents(p_net)
        voltages = self._voltages_from_currents(currents)
        return voltages, currents, p_net

    # -------------------------------------------------------------------------
    # 对外接口
    # -------------------------------------------------------------------------
    def voltage_profile(self, time='noon'):
        """返回节点电压（pu dict）。

        Parameters
        ----------
        time : str
            - 'noon'：中午 PV 满发 + 最小负荷（默认，演示反向潮流）
            - 'night'：夜间最大负荷 + 无 PV（演示电压跌落）

        Returns
        -------
        dict : {节点编号: 电压 pu}，键 0, 1, ..., num_nodes。
        """
        if time == 'noon':
            pv_factor, load_factor = 1.0, NOON_LOAD_FACTOR
        elif time == 'night':
            pv_factor, load_factor = 0.0, 1.0
        else:
            raise ValueError(f"time must be 'noon' or 'night', got {time!r}")

        voltages, _, _ = self._solve(pv_factor, load_factor)
        return {i: v / self.base_voltage_phase for i, v in enumerate(voltages)}

    def solve_peak(self):
        """中午 PV 满发 + 最小负荷，计算 4 节点电压（pu）。

        Returns
        -------
        dict : {0: V0_pu, 1: V1_pu, 2: V2_pu, 3: V3_pu}
        """
        return self.voltage_profile(time='noon')

    def reverse_power_kw(self, time='noon'):
        """总反向潮流功率（kW）。正值 = 净功率从馈线流向变压器（PV 注入）。"""
        if time == 'noon':
            pv_factor, load_factor = 1.0, NOON_LOAD_FACTOR
        elif time == 'night':
            pv_factor, load_factor = 0.0, 1.0
        else:
            raise ValueError(f"time must be 'noon' or 'night', got {time!r}")

        voltages, currents, _ = self._solve(pv_factor, load_factor)
        if not currents:
            return 0.0
        # 段 1 电流（流出变压器方向为正，负值 = 反向）
        # 反向功率 = -I_seg_1 × V_phase / 1000
        return -currents[0] * self.base_voltage_phase / 1000.0

    def find_penetration_limit(self, max_voltage=VOLTAGE_UPPER_LIMIT_PU,
                               tol=1e-3, max_iter=50):
        """二分搜索找到最大渗透率（noon 场景），不超过 max_voltage。

        渗透率定义为 Σ P_pv / Σ P_peak_load。在 noon 场景下（PV 满发 +
        最小负荷），找到使 V_3 = max_voltage 的临界渗透率。

        Parameters
        ----------
        max_voltage : float
            电压上限（pu），默认 1.07（GB/T 12325）。
        tol : float
            渗透率搜索精度。
        max_iter : int
            二分迭代上限。

        Returns
        -------
        float : 最大渗透率（0-1）。
        """
        # 保存原 PV 配置
        original_pv = dict(self.pv_installed)

        def v3_at_penetration(p):
            for i in range(1, self.num_nodes + 1):
                self.pv_installed[i] = self.peak_load_per_node * p
            v = self.solve_peak()
            return v[self.num_nodes]

        try:
            lo, hi = 0.0, 2.0
            for _ in range(max_iter):
                mid = 0.5 * (lo + hi)
                v3 = v3_at_penetration(mid)
                if v3 > max_voltage:
                    hi = mid
                else:
                    lo = mid
                if hi - lo < tol:
                    break
            return 0.5 * (lo + hi)
        finally:
            # 恢复原 PV 配置
            self.pv_installed = original_pv

    @staticmethod
    def compare_penetration(levels=(0.1, 0.3, 0.5, 0.7),
                            peak_load_per_node=PEAK_LOAD_PER_NODE_KW,
                            **kwargs):
        """4 行 × 5 列对比（渗透率、PV 峰值、节点 1 电压、节点 3 电压、反向潮流）。

        Parameters
        ----------
        levels : iterable of float
            渗透率列表（0-1）。默认 (0.1, 0.3, 0.5, 0.7)。
        peak_load_per_node : float
            单节点峰值负荷（kW）。默认 7。
        **kwargs
            透传给 DistributionGrid 构造函数（transformer_kVA、
            feeder_resistance_per_km、base_voltage、num_nodes 等）。

        Returns
        -------
        pandas.DataFrame : 4 行 × 5 列。
            列：penetration, pv_total_kw, v_node1_pu, v_node3_pu,
               reverse_power_kw
        """
        if pd is None:
            raise ImportError(
                "compare_penetration requires pandas; "
                "install with `python -m pip install pandas`."
            )

        rows = []
        for p in levels:
            pv_per_node = peak_load_per_node * p
            grid = DistributionGrid(
                pv_per_node=pv_per_node,
                peak_load_per_node=peak_load_per_node,
                **kwargs,
            )
            voltages = grid.solve_peak()
            reverse_kw = grid.reverse_power_kw()
            total_pv = grid.pv_per_node * grid.num_nodes
            total_load = grid.peak_load_per_node * grid.num_nodes
            rows.append({
                "penetration": p,
                "pv_total_kw": total_pv,
                "load_total_kw": total_load,
                "v_node1_pu": voltages[1],
                "v_node3_pu": voltages[3],
                "reverse_power_kw": reverse_kw,
            })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=" * 78)
    print("4 节点低压配电网 + 4 种渗透率对比")
    print("=" * 78)
    print()

    # 默认参数
    print("默认参数：")
    g = DistributionGrid()
    print(f"  pv_per_node         = {g.pv_per_node} kW")
    print(f"  peak_load_per_node  = {g.peak_load_per_node} kW")
    print(f"  transformer_kVA     = {g.transformer_kVA} kVA")
    print(f"  feeder_resistance_per_segment = {g.feeder_resistance_per_segment} Ω")
    print(f"  feeder_length_per_segment_km  = {g.feeder_length_per_segment_km} km")
    print(f"  transformer_full_load_current = {g.transformer_full_load_current_A:.1f} A")
    print()

    # 1) 加载默认参数 + 跑 4 种渗透率对比
    print("=" * 78)
    print("4 种渗透率 noon 场景对比（PV 满发 + 最小负荷）")
    print("=" * 78)
    df = DistributionGrid.compare_penetration()
    print()
    print(df.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()

    # 2) 验证单调性：节点 3 电压随渗透率单调递增
    v3 = df["v_node3_pu"].values
    monotonic = all(v3[i] < v3[i + 1] for i in range(len(v3) - 1))
    print(f"节点 3 电压单调递增：{monotonic}  (V_3 = {v3.tolist()})")
    print(f"渗透率 70% 时 V_3 = {v3[-1]:.3f} pu (> 1.10 pu 越限: {v3[-1] > 1.10})")
    print()

    # 3) find_penetration_limit：找到使 V_3 = 1.07 pu 的临界渗透率
    print("=" * 78)
    print("find_penetration_limit(max_voltage=1.07)：")
    print("=" * 78)
    g2 = DistributionGrid()
    limit = g2.find_penetration_limit(max_voltage=1.07)
    print(f"  临界渗透率 = {limit:.1%}  (noon 场景，GB/T 12325 上限)")
    print()

    # 4) noon vs night 场景对比
    print("=" * 78)
    print("noon vs night 场景对比（默认 PV=7 kW, load=7 kW）")
    print("=" * 78)
    g3 = DistributionGrid()
    v_noon = g3.voltage_profile(time='noon')
    v_night = g3.voltage_profile(time='night')
    rev_noon = g3.reverse_power_kw(time='noon')
    print(f"  {'节点':<6}{'noon (V)':<14}{'noon (pu)':<14}"
          f"{'night (V)':<14}{'night (pu)':<14}")
    for i in range(g3.num_nodes + 1):
        v_n_v = v_noon[i] * g3.base_voltage_phase
        v_ng_v = v_night[i] * g3.base_voltage_phase
        print(f"  {i:<6}{v_n_v:<14.2f}{v_noon[i]:<14.4f}"
              f"{v_ng_v:<14.2f}{v_night[i]:<14.4f}")
    print(f"  noon 反向潮流 = {rev_noon:.2f} kW")
