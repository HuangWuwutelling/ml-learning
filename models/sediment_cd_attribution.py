"""
河流底泥镉异常高值归因模型（articles/env/26）

要回答的问题：底泥里测出高镉，到底是污染、地质背景，还是矿体？

模型不产生新数据。它做四件事：

1. 换参照系。把同一批实测 Cd 依次代入不同背景值，看 Igeo 跳级。
2. 换统计口径。同一批样品的 X+2S 异常下限，剔除 X±3S 前后差 4 倍。
3. 换分级表。同一个 Igeo / RI 值，Müller 七级表和文献自带的分级表结论不同。
4. 拆粒度。用分粒级中位值独立重算 Sava 论文的判别比值，看一个高值
   到底是泥多还是镉多。

另外用文献给出的统计量回代公式做交叉核对（Er、PLI、ER_frac）。

参数标注沿用仓库约定：[S]=标准 [L]=文献 [E]=估算 [C]=计算 [A]=假设
标注规则：凡是文献原样给出的数标 [L]；由文献数算出来的标 [C]；
文献里没有、自己假设的标 [E] 或 [A]；标 [S] 的来自标准原文。

运行：python models/sediment_cd_attribution.py
"""

import math
import os
import unicodedata


def dwidth(s):
    """字符串的终端显示宽度：CJK 全角算 2 列"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, n, align="<"):
    """按显示宽度对齐（f-string 的 :< 是按字符数，中文表格会歪）"""
    fill = max(0, n - dwidth(s))
    return s + " " * fill if align == "<" else " " * fill + s

# ----------------------------------------------------------------------
# 1. 背景值：同一个国家，不同来源给的数不一样
# ----------------------------------------------------------------------

BG_CHINA_SEDIMENT = 0.11        # [L] 全国水系沉积物 Cd 背景值 mg/kg
BG_WANDA_GEOCHEM = 0.081        # [L] 完达山区域化探 Cd 背景值 mg/kg（文献表 3）
BG_WANDA_STUDY = 0.12           # [L] 完达山研究区 Cd 背景值 mg/kg（文献表 2）
BG_GEM76_SOUTH_MEDIAN = 0.219   # [L] 76 元素地球化学填图（76 GEM）南方 Cd 中位数 219 ug/kg
BG_GUIZHOU_SOIL = 0.66          # [L] 贵州省表层土壤 Cd 背景值 mg/kg

# 安宁河实测（[L] Toxics 2026, PMC13417149, 表 1/表 2）
ANNING = {
    "min": 0.17, "max": 5.39, "mean": 0.85, "sd": 0.80,
    "median": 0.68, "cv": 93.94,
}

# 其他河流 Cd 对照（同上文献表 2，行名照抄原文）
RIVER_COMPARISON = {
    "金沙江": 0.25, "渭河": 0.41, "黄河": 0.90, "黑龙江": 0.13, "丹江": 0.49,
}

# 完达山 1423 件河流沉积物实测（[L] Toxics 2026, PMC13517669）
WANDA = {
    "n": 1423, "min": 0.027, "max": 1.06, "mean": 0.131, "sd": 0.076, "cv": 58.4,
    "times_bg": 1.61,          # Cd 均值 / 完达山区域化探背景值
    "bg": 0.081,               # 完达山区域化探 Cd 背景值 mg/kg
}
# PCA 三个源端元（同上文献正文）
WANDA_ENDMEMBERS = {
    "PC1 自然地质源": ("Cr", "Ni", "Co"),
    "PC2 采矿源": ("Zn", "Hg", "Cu", "Cd"),
    "PC3 农业面源": ("Pb", "As", "Sb"),
}
# APCS-MLR 源贡献率 %（同上文献正文）
WANDA_APCS = {"Cd": 48.92, "Zn": 82.64, "Hg": 74.54, "Cu": 61.09, "Ni": 44.42,
              "As": 42.93, "Pb": 39.16}
WANDA_APCS_MINING = ("Cd", "Zn", "Hg", "Cu", "Ni")   # 采矿源 PC2 主导
WANDA_APCS_AGRI = ("As", "Pb")                       # 农业源 PC3 主导
WANDA_GEOGENIC_MAX = 13.0    # 自然风化源 PC1 对除铬以外所有元素贡献 < 13%
WANDA_GEOGENIC_CR = 23.39    # 唯一例外：铬 23.39%（[L] 同上文献正文）

# 完达山八种元素：均值、研究区背景值（表 2）、区域化探背景值（表 3）
# [L] Toxics 2026, PMC13517669 表 2 / 表 3
WANDA_ELEMENTS = {
    # 元素: (均值, 研究区背景值, 区域化探背景值)
    "Cr": (96.9, 92.3, 88.3),
    "Ni": (20.9, 19.3, 33.1),
    "Cu": (16.4, 16.1, 25.6),
    "Zn": (79.7, 77.5, 87.3),
    "Cd": (0.131, 0.12, 0.081),
    "Pb": (29.9, 29.1, 22.7),
    "Hg": (0.029, 0.024, 0.043),
    "As": (13.31, 11.2, 9.5),
}
# 完达山污染因子 CF 分级的样点数（[L] 同上文献表 4，合计 = 1423）
# CF 档界：<=1 无污染、1-2 轻度、2-3 中度、>=3 重度
WANDA_CF_COUNTS = {
    "Cd": {"无污染": 975, "轻度污染": 339, "中度污染": 80, "重度污染": 29},
    "As": {"无污染": 970, "轻度污染": 254, "中度污染": 81, "重度污染": 118},
    "Hg": {"无污染": 704, "轻度污染": 530, "中度污染": 148, "重度污染": 41},
}
# 完达山 Igeo 分级的样点数（[L] 同上文献表 5，合计 = 1423）
# Igeo 档界跟 CF 不一样：<=0 无污染、0-1 轻度、1-2 中度、>2 重度
WANDA_IGEO_COUNTS = {
    "Cd": {"无污染": 1243, "轻度污染": 151, "中度污染": 28, "重度污染": 1},
    "As": {"无污染": 1154, "轻度污染": 151, "中度污染": 74, "重度污染": 44},
    "Hg": {"无污染": 1036, "轻度污染": 346, "中度污染": 37, "重度污染": 4},
}
# 完达山 PCA 特征值与累计方差（[L] 同上文献表 7）
WANDA_PCA = {"eigenvalues": (7.001, 1.689, 1.343), "variance_pct": 66.886}
# 完达山论文结论：汞和砷是主要污染物元素（Cd 排第三）
WANDA_DOMINANT_POLLUTANTS = ("Hg", "As")
# 完达山污染负荷指数与生态风险指数（[L] 同上文献正文）
WANDA_PLI_MEAN = 0.966        # 1423 个样点逐点算完再平均 -> 未污染档
WANDA_PLI_ZONES = {"轻度污染区": 33.2, "中度污染区": 4.1}   # %，无重度污染区
WANDA_RI_MEAN = 111.45        # -> 低生态风险档（该文自己的分级）
WANDA_RI_ZONES = {"中等生态风险": 19.2, "较高生态风险": 0.8}  # % 的样点占比
WANDA_IGEO_MAX = 4.06         # 全区 Igeo 最大值

# 76 元素地球化学填图（76 GEM）南方 Cd 统计（[L] J. Geochem. Explor. 2014, PMC3990449），单位 ug/kg
# 剔除 X±3S 前后的 X、S 是文献表 2 直接给出的，本模型不重做剔除
GEM76_CD = {
    "min": 24, "p5": 76, "p25": 139, "median": 219, "p75": 398, "p95": 1247,
    "max": 21954, "mean_before": 431, "sd_before": 828,
    "mean_after": 230, "sd_after": 134,
}

# 贵州东部清虚洞组 Pb-Zn 矿化带土壤（[L] Sci Rep 2025, PMC12127453）
GUIZHOU_SOIL = {
    "Cd": {"min": 0.35, "median": 1.93, "max": 29.64, "mean": 3.51, "sd": 4.38,
           "cv": 124.0, "bv": 0.66},
    "Pb": {"mean": 309.0, "bv": 35.2},
    "Zn": {"mean": 617.0, "bv": 99.5},
    # 该文正文：Cr/Ni/Cu 与贵州省背景值相当，Cd/Pb/Zn/As/Hg 超背景值
    "not_elevated": ("Cr", "Ni", "Cu"),
    # 各元素平均含量 / 省背景值（按该文表 1 现算；论文正文另报一套更低的倍数
    # 4.71/6.08/4.31/1.99/4.45，与表 1 自身不自洽，这里取表 1）
    "mean_ratios": {"Cr": 1.07, "Ni": 1.25, "Cu": 1.46,
                    "Cd": 5.32, "Pb": 8.78, "Zn": 6.20, "As": 2.08, "Hg": 4.55},
    # 土壤 pH 5.23~7.60，均值 6.76，>70% 落在 6.5~7.60（该文正文）
    "pH": {"min": 5.23, "max": 7.60, "mean": 6.76},
}

# 湖南 Pb-Zn 矿区河流沉积物（[L] Sci Rep 2024, PMC11369138）
# 该文只有 1 张表（主量元素 + 有机质），Cd/Pb/As 只出现在图 2 的柱状图里，
# 正文没给数值。本模型只取正文写出来的结论，不从图上读数。
HUNAN = {
    "sections": ["上游", "中上游", "中下游", "下游"],
    # 正文（Fig. 2 文字）：上游的 Cd/Pb/As 随粒度变细升高，1-0.5 mm 粗砂最低
    # 同句还写了「中下游」随粒度变细升高，但中下游另有粗砂高值，见 both_ends
    # 下游只在形态（Fig. 4）那一句出现，总含量没有单独给趋势，故不在三组里
    "fine_rich": ["上游"],
    # 正文：中上游反过来，Cd/Pb/As 在 1-0.5 mm 粗砂里高
    "coarse_rich": ["中上游"],
    # 正文：中下游两头都高，除细粒高外 1-0.5 mm 粗砂和 <0.075 mm 粉砂里 Cd 都偏高
    "both_ends": ["中下游"],
    # 正文：上游 Pb/As 最高，Cd 在中下游最高；上游重金属总量低
    "highest": {"Pb": "中上游", "As": "中上游", "Cd": "中下游"},
    # 正文：中上游是矽卡岩型铅锌矿床；中下游是历史矿区，采矿已基本停止
    "mining": {"中上游": "矽卡岩型铅锌矿床", "中下游": "历史矿区，采矿已基本停止"},
    # 正文：历史采矿遗留的黄铁矿是重要来源
    "legacy_source": "历史采矿遗留的黄铁矿",
    # 正文引用的矿物碎屑粒径 mm（闪锌矿/方铅矿/黄铁矿），都比粉砂粗
    "mineral_grain_mm": {"闪锌矿": 0.5, "方铅矿": 1.2, "黄铁矿": 1.0},
    "silt_upper_mm": 0.075,
}

# 安宁河分河段空间格局（[L] Toxics 2026, PMC13417149 正文 3.2 节）
# 论文用 Kriging 插值给出空间分布，正文文字描述各元素高值落在哪一段
ANNING_REACH = {
    "中游": ["Zn", "Cu", "Cd"],   # 铁矿开采 + 金属冶炼厂密集段
    "上游": ["Pb", "Cr", "Ni"],   # Pb 连片富集带；Cr/Ni 高浓度区
}
# 安宁河 PMF 源解析（[L] 同上文献摘要）
ANNING_PMF = {
    "采矿冶炼排放": ("Cd", "Zn"),
    "自然岩性风化": ("V", "Cr", "Ni"),
    "交通/城市混合输入": ("Pb", "Cu"),
    "Tl 专属混合源": ("Tl",),
}
# 安宁河污染/风险指数（[L] 同上文献正文 3.3.2 / 3.3.4）
ANNING_IGEO_MEAN = {"Cd": 2.06, "Pb": 1.29, "Zn": 0.65, "Cu": 0.47,
                     "Cr": 0.42, "Ni": 0.18}
ANNING_RI_MEAN = 303.64        # 200 <= RI < 400 -> 较高生态风险
ANNING_RI_CD_ER = 232.25       # Cd 单元素 Er
ANNING_RI_CD_SHARE = 76.5      # Cd 占总 RI 的百分比
# 安宁河蒙特卡洛风险（[L] 同上文献 3.5 节）
# 确定性：成人 THI 1.64e-1、儿童 6.71e-1，都 < 1
# 概率性：儿童 TCR > 1.0e-4 的概率 60.51%，成人 23.4%
# 关键：TCR 超阈由 Cr 和 Ni 主导，RI 由 Cd 主导，两个口径指向不同元素
ANNING_MC = {
    "thi_adult": 1.64e-1,
    "thi_child": 6.71e-1,
    "child_tcr_prob": 60.51,    # 儿童 TCR > 1.0e-4 的概率 %
    "child_tcr_p95": 2.03e-4,
    "child_tcr_mean": 1.18e-4,
    "adult_tcr_prob": 23.4,     # 成人 %
    "adult_tcr_p95": 1.40e-4,
    "adult_tcr_mean": 8.18e-5,
    "child_thi_prob": 10.0,     # 儿童 THI > 1 的概率（原文 nearly 10%）
    "tcr_drivers": ("Cr", "Ni"),           # 致癌风险的主导元素
    "thi_order": ("Cr", "Pb", "V", "Tl", "Ni", "Cd", "Cu", "Zn"),  # 非致癌风险排序
    "cr_hi_adult": 7.51e-2,
    "cr_hi_child": 2.91e-1,
}
# 安宁河结论：V、Cr、Ni 基本未污染、贴近背景值（[L] 同上文献 5. Conclusions）
# 关键：驱动致癌风险的铬和镍，在污染指标上恰恰是干净的
ANNING_UNPOLLUTED = ("V", "Cr", "Ni")
# 安宁河 3.6 节的管理建议（[L] 同上文献 3.6 Implications for Environmental Management）
# 论文按元素分两条路：Cd/Pb 控源，Cr/Ni 切暴露路径
ANNING_MANAGEMENT = {
    "source_control": ("Cd", "Pb"),
    "pathway": ("Cr", "Ni"),
    "source_measures": "严格监管采矿废水排放、升级尾矿设施防渗漏、从源头处理酸性矿山废水",
    "pathway_measures": "限制儿童进入住宅区附近高污染河岸带；枯水季裸露底泥再悬浮成扬尘，"
                        "靠生态补水和河岸植被恢复削减经口和吸入两条路径",
}
# 安宁河健康评估的局限（[L] 同上文献 4. Limitations）
ANNING_LIMIT = "健康风险只用总含量算，未区分金属形态和生物可利用性，铬的致癌风险就是按总铬算的"

# 安徽秋浦河流域：官方认定的 Cd 高背景区（[L] 资源环境与工程 2025, 39(4): 400-408,
# DOI 10.16536/j.cnki.2097-6666.2025.04.006）
QIUPU = {
    "soil_cd_mean": 0.458,       # 流域土壤 Cd 平均含量 mg/kg（表 1）
    # 下游秋江耕地 5 件土壤样（表 5）：QPTR01 -0.31 / QPTR02 -0.36 /
    # QPTR03 -0.14 / QPTR05 -0.09 / QPTR06 -0.24，均值 -0.23
    # 摘要印成「-0.09‰ ~ 0.36‰」，第二个值漏了负号，与表 5 和均值都对不上，以表 5 为准
    "delta_range": (-0.36, -0.09),
    "delta_mean": -0.23,
    "rock_gufeng": -0.40,                # 表 5 QPYS01 孤峰组硅质岩
    "rock_cambrian_range": (1.04, 1.94),  # 表 5 YST2~YST4 灰岩、YST1 荷塘组炭质岩
    "match_rock": "二叠系孤峰组炭（硅）质岩",
    "avail_up": 50.87,           # 上游有效态 Cd 占比 %
    "avail_mid_low": 58.02,      # 中下游有效态 Cd 占比 %
    # 摘要原文：有效态 = 水溶态 + 离子交换态 + 碳酸盐结合态
    "avail_def": "水溶态 + 离子交换态 + 碳酸盐结合态",
    "title": "安徽秋浦河流域土壤镉赋存特征及其来源解析",
    "authors": "侯克斌; 徐利强; 刘超; 许斌",
    "journal": "资源环境与工程 2025, 39(04): 400-408",
}

# 北江 Cd 同位素（[L] Environ. Pollut. 2013, DOI 10.1016/j.envpol.2013.05.048）
# 摘要可核：delta114/110Cd -0.35 ~ +0.07 per mil，均值 -0.08；
# 冶炼厂和电子废弃物镇采样点分馏量最大
BEIJIANG = {
    "delta_range": (-0.35, 0.07),  # per mil，均值 -0.08
    "delta_mean": -0.08,
}

# 北江冶炼厂下游 1 m 沉积物剖面（[L] Ecotoxicol. Environ. Saf. 2020,
# DOI 10.1016/j.ecoenv.2020.110529）：Cd 107-441 mg/kg，剖面检出绿锌石(CdS)
NORTHRIVER_PROFILE = {
    "cd_range": (107.0, 441.0),   # mg/kg
    "mineral": "绿锌石 (CdS)",
    "source": "冶炼渣",
}

# 韶关铅锌冶炼厂同位素分馏（[L] J. Hazard. Mater. 2021, DOI 10.1016/j.jhazmat.2020.125015）
SHAOGUAN = {
    "model": "Rayleigh 蒸馏",
    "heavy_in": "炉渣",          # 重同位素富集于炉渣
    "light_in": "烟尘",          # 轻同位素富集于烟尘
    "eps_slag": 10.42,           # 炉渣 epsilon114/110Cd
    "eps_dust": -5.68,           # 烟尘 epsilon114/110Cd
    "eps_core": (-0.62, 1.73),   # 下游沉积物柱 epsilon 区间
    "slag_share": (88, 93),      # 二元混合模型：炉渣占比 %
    "dust_share": (7, 12),       # 二元混合模型：烟尘占比 %
}

# Sava 河—Voglajna 断面（[L] Sci Rep 2021, PMC8413453）
# 表 2：Cd 分粒级中位值 mg/kg。S-SS=萨维尼亚河床砂，V-SS=弗格拉亚河床砂，
# SP=萨维尼亚河漫滩，VP=弗格拉亚河漫滩，BGV=本研究区估算的地化背景值
# ER_EU 的分母 Md_EU 是欧洲河流沉积物中位值（文献引 ref 25），表 2 里没有，
# 所以 ER_EU 只能照抄论文表 3，不独立重算
SAVA_T2 = {
    "S-SS": {"fine": 0.39, "coarse": 0.44},
    "V-SS": {"fine": 0.32, "coarse": 0.29},
    "SP":   {"fine": 0.91, "coarse": 0.65},
    "VP":   {"fine": 4.9,  "coarse": 3.5},
    "BGV":  {"fine": 0.18, "coarse": 0.17},
}
# 表 3：论文自己算好的三个判别比值（Cd 行）
SAVA_T3 = {
    "stream":   {"S": {"ereu": 1.6, "erfrac": 1.1}, "V": {"ereu": 1.0, "erfrac": 0.9},
                 "ersource_fine": 6.1, "ersource_coarse": 7.1},
    "alluvial": {"S": {"ereu": 2.3, "erfrac": 0.7}, "V": {"ereu": 13, "erfrac": 0.7},
                 "ersource_fine": 15, "ersource_coarse": 12},
}

# ----------------------------------------------------------------------
# 2. 标准（[S]）
# ----------------------------------------------------------------------

# GB 15618-2018 土壤环境质量 农用地土壤污染风险管控标准（试行）
# Cd 筛选值按 pH 分档：pH<=5.5 / 5.5-6.5 / 6.5-7.5 / >7.5
# 下表是【水田】一行；【其他】（旱地）筛选值更严，0.3 / 0.3 / 0.3 / 0.6
# 表 1 / 表 3 原表：Cd 水田 0.3 0.4 0.6 0.8；其他 0.3 0.3 0.3 0.6；管制值两行相同
GB15618_CD_SCREEN = {"<=5.5": 0.3, "5.5-6.5": 0.4, "6.5-7.5": 0.6, ">7.5": 0.8}
GB15618_CD_SCREEN_DRY = {"<=5.5": 0.3, "5.5-6.5": 0.3, "6.5-7.5": 0.3, ">7.5": 0.6}
GB15618_CD_CONTROL = {"<=5.5": 1.5, "5.5-6.5": 2.0, "6.5-7.5": 3.0, ">7.5": 4.0}

# GB 18668-2002 海洋沉积物质量标准 Cd 一/二/三类
GB18668_CD = {"一类": 0.50, "二类": 1.50, "三类": 5.00}

# GB 5085.3-2007 危险废物鉴别标准 浸出毒性鉴别
# 注意：限值单位是浸出液 mg/L，跟固体相含量 mg/kg 不是一回事，不能直接比倍数。
# 只有走「作废物处置」这条路、而且是测的浸出液浓度，才对得上这个数。
GB50853_CD_LEACH = 1.0  # mg/L（浸出液）

# ----------------------------------------------------------------------
# 3. 指数与分级表
# ----------------------------------------------------------------------

# Igeo 分级表一：Müller 1969 七级（[L]）
# 档名按 Müller 原表的中文通行译法：
# <=0 无污染、0-1 无~中度、1-2 中度、2-3 中~强、3-4 强、4-5 强~极强、>5 极强
IGEO_GRADES = [
    (0, 1, "无~中度污染"),
    (1, 2, "中度污染"),
    (2, 3, "中~强污染"),
    (3, 4, "强污染"),
    (4, 5, "强~极强污染"),
    (5, 99, "极强污染"),
]

# Igeo 分级表二：完达山论文自用的四级（[L] Toxics 2026, PMC13517669 正文）
# Igeo > 2 一律并成「重度污染」，1-2 中度，0-1 轻度，<=0 无污染
IGEO_GRADES_4 = [
    (0, 1, "轻度污染"),
    (1, 2, "中度污染"),
    (2, 99, "重度污染"),
]

# 生态风险指数 RI 分级表：两篇文献各一套（[L]）
RI_BANDS_WANDA = [(0, 150, "低"), (150, 300, "中等"), (300, 600, "较高"), (600, None, "极高")]
RI_BANDS_ANNING = [(0, 110, "低"), (110, 200, "中等"), (200, 400, "较高"),
                   (400, None, "极高")]


def igeo(c, bg, k=1.5):
    """地累积指数 log2(Ci / (k*Bi))，k=1.5 修正岩浆/沉积岩自然波动"""
    if c <= 0 or bg <= 0:
        return float("nan")
    return math.log2(c / (k * bg))


def igeo_grade(v, grades=None):
    """Igeo <0 单独判为无污染；grades 可换成别的文献分级表"""
    grades = grades or IGEO_GRADES
    if v < 0:
        return "无污染"
    for lo, hi, label in grades:
        if lo <= v < hi:
            return label
    return grades[-1][2]


# 毒性系数（[L] Hakanson 1980；安宁河论文另给 Tl = 10）
TRI = {"Cd": 30, "Hg": 40, "As": 10, "Pb": 5, "Cu": 5, "Ni": 5, "Cr": 2, "Zn": 1}


def eri(c, bg, tri=30):
    """单元素污染风险因子 Eri = Tri * (Cs / Cn)"""
    if bg <= 0:
        return float("nan")
    return tri * (c / bg)


def ri_grade(ri, bands):
    """RI 分级。bands 形如 [(下限, 上限, 名称), ...]，上限 None 表示无上限"""
    for lo, hi, label in bands:
        if ri >= lo and (hi is None or ri < hi):
            return label
    return bands[-1][2]


def cf(c, bg):
    """污染因子 CF = Cs / Cn"""
    if bg <= 0:
        return float("nan")
    return c / bg


def cf_grade(v):
    """污染因子分级（[L] 完达山论文正文：CF<=1 无污染，1-2 轻度，2-3 中度，>=3 重度）"""
    if v <= 1:
        return "无污染"
    if v <= 2:
        return "轻度污染"
    if v <= 3:
        return "中度污染"
    return "重度污染"


def pli(concs, bgs):
    """污染负荷指数 PLI = (prod(Ci/Ci0))^(1/n)"""
    n = len(concs)
    if n == 0:
        return float("nan")
    prod = 1.0
    for c, b in zip(concs, bgs):
        prod *= (c / b)
    return prod ** (1.0 / n)


# PLI 分级（[L] 完达山论文正文：PLI<=1 未污染，1-2 轻度，2-3 中度，>3 重度）
def pli_grade(v):
    if v <= 1:
        return "未污染"
    if v <= 2:
        return "轻度污染"
    if v <= 3:
        return "中度污染"
    return "重度污染"


# ----------------------------------------------------------------------
# 4. 地球化学普查的异常下限算法
# ----------------------------------------------------------------------

def threshold_x_plus_ns(x, s, n_sigma=2):
    """T = X + n*S，地球化学普查异常下限（[L] DZ/T 0011-2015 做法）"""
    return x + n_sigma * s


# ----------------------------------------------------------------------
# 5. 三层判别比值（Sava 论文，[L] PMC8413453 正文公式 3/4/5）
# ----------------------------------------------------------------------

def erfrac(md_coarse, md_fine):
    """ER_frac = Md_{0.125-0.063} / Md_{<0.063}：粗粒 / 细粒。
    >1 粗粒富集，<1 细粒富集。"""
    if md_fine <= 0:
        return float("nan")
    return md_coarse / md_fine


# ----------------------------------------------------------------------
# 6. 主验证
# ----------------------------------------------------------------------

def main():
    out_lines = []

    def p(s=""):
        out_lines.append(s)
        print(s)

    p("=" * 76)
    p("表 1  同一批实测 Cd，换背景值，Igeo 跳级")
    p("=" * 76)
    p(f"{'背景值来源':<32}{'Bi':>7} | " + " | ".join(
        f"C={c:<5}" for c in (0.68, 3.0, 5.39)))
    refs = [
        ("全国水系沉积物背景值 [L]", BG_CHINA_SEDIMENT),
        ("完达山区域化探背景值 [L]", BG_WANDA_GEOCHEM),
        ("完达山研究区背景值 [L]", BG_WANDA_STUDY),
        ("76 元素填图南方中位数 [L]", BG_GEM76_SOUTH_MEDIAN),
        ("贵州表层土壤背景值 [L]", BG_GUIZHOU_SOIL),
    ]
    rows = []
    for name, bg in refs:
        cells = []
        for c in (0.68, 3.0, 5.39):
            v = igeo(c, bg)
            cells.append(f"{v:6.2f}")
            rows.append((name, bg, c, v, igeo_grade(v)))
        p(f"{name:<32}{bg:>7.3f} | " + " | ".join(cells))
    p()
    p("同一个 C=3.0 mg/kg，换参照系的分级差异：")
    for name, bg, c, v, g in rows:
        if c == 3.0:
            p(f"  Bi={bg:.3f} -> Igeo {v:5.2f} -> {g}")
    p()
    p("安宁河中位 0.68 mg/kg 换参照系：")
    for name, bg, c, v, g in rows:
        if c == 0.68:
            p(f"  Bi={bg:.3f} -> Igeo {v:5.2f} -> {g}")

    p()
    p("=" * 76)
    p("表 2  76 元素填图：统计口径不同，异常下限差 4 倍")
    p("=" * 76)
    t_before = threshold_x_plus_ns(GEM76_CD["mean_before"], GEM76_CD["sd_before"], 2) / 1000.0
    t_after = threshold_x_plus_ns(GEM76_CD["mean_after"], GEM76_CD["sd_after"], 2) / 1000.0
    p(f"剔除 X±3S 之前：X={GEM76_CD['mean_before']} ug/kg, S={GEM76_CD['sd_before']} ug/kg"
      f"  ->  T = X + 2S = {t_before:.3f} mg/kg")
    p(f"剔除 X±3S 之后：X={GEM76_CD['mean_after']} ug/kg, S={GEM76_CD['sd_after']} ug/kg"
      f"  ->  T = X + 2S = {t_after:.3f} mg/kg")
    p(f"差 {t_before / t_after:.2f} 倍")
    p()
    p(f"全国水系沉积物背景值 {BG_CHINA_SEDIMENT} mg/kg；76 元素填图中位数 "
      f"{GEM76_CD['median'] / 1000:.3f} mg/kg（{GEM76_CD['median'] / 1000 / BG_CHINA_SEDIMENT:.2f} 倍）")
    p(f"75% 分位 {GEM76_CD['p75'] / 1000:.3f}、95% 分位 {GEM76_CD['p95'] / 1000:.3f}、"
      f"最大 {GEM76_CD['max'] / 1000:.1f} mg/kg")
    p("同一批样品，同一套算法，异常下限可以是 0.5 也可以是 2.1 mg/kg。")

    p()
    p("=" * 76)
    p("表 3  泥多还是镉多：Sava 河分粒级中位值 + ER_frac 独立重算 [L] Sci Rep 2021")
    p("=" * 76)
    p(f"{pad('位置', 22)}{'细粒<0.063':>12}{'粗粒0.063-0.125':>17}"
      f"{'粗/细重算':>11}{'论文ER_frac':>13}")
    checks = [
        ("河床砂 萨维尼亚", "S-SS", "stream", "S"),
        ("河床砂 弗格拉亚", "V-SS", "stream", "V"),
        ("漫滩 萨维尼亚", "SP", "alluvial", "S"),
        ("漫滩 弗格拉亚", "VP", "alluvial", "V"),
    ]
    frac_rows = []
    for label, key, grp, who in checks:
        d = SAVA_T2[key]
        calc = erfrac(d["coarse"], d["fine"])
        pub = SAVA_T3[grp][who]["erfrac"]
        frac_rows.append((label, calc, pub))
        p(f"{pad(label, 22)}{d['fine']:>12.2f}{d['coarse']:>17.2f}"
          f"{calc:>11.3f}{pub:>13.1f}")
    p(f"{pad('地化背景值 BGV', 22)}{SAVA_T2['BGV']['fine']:>12.2f}"
      f"{SAVA_T2['BGV']['coarse']:>17.2f}")
    p()
    p("ER_frac = 粗粒中位 / 细粒中位：>1 粗粒富集，<1 细粒富集")
    p("河漫滩 0.7（细粒富集）=> 镉跟着泥走；河床砂 1.1 / 0.9（粗细接近）")
    p()
    p("【对照】湖南 Pb-Zn 矿区河流 [L] Sci Rep 2024，正文文字结论（无数值表）")
    p(f"  {'、'.join(HUNAN['fine_rich'])}：Cd/Pb/As 随粒度变细升高，1-0.5 mm 粗砂最低")
    p(f"  {'、'.join(HUNAN['coarse_rich'])}：反过来，Cd/Pb/As 在粗砂里最高，粒度效应被物源打断")
    p(f"  {'、'.join(HUNAN['both_ends'])}：两头都高，1-0.5 mm 粗砂和 "
      f"<{HUNAN['silt_upper_mm']} mm 粉砂里 Cd 都偏高，粒度效应也被打断")
    p("  各元素最高值所在断面："
      + "、".join(f"{k} {v}" for k, v in HUNAN["highest"].items()))
    p("  矿段：" + "；".join(f"{k} {v}" for k, v in HUNAN["mining"].items()))
    p(f"  中下游打断粒度效应的来源：{HUNAN['legacy_source']}")
    p("  矿物碎屑粒径："
      + "、".join(f"{k} {v} mm" for k, v in HUNAN["mineral_grain_mm"].items())
      + f"，都比粉砂（<{HUNAN['silt_upper_mm']} mm）粗")

    p()
    p("=" * 76)
    p("表 4  Sava 河另外两个判别比值 [L] Sci Rep 2021")
    p("=" * 76)
    p(f"  ER_EU（样品中位 / 欧洲河流沉积物中位）：河漫滩 萨维尼亚 "
      f"{SAVA_T3['alluvial']['S']['ereu']}、弗格拉亚 {SAVA_T3['alluvial']['V']['ereu']}；"
      f"河床砂 萨维尼亚 {SAVA_T3['stream']['S']['ereu']}、"
      f"弗格拉亚 {SAVA_T3['stream']['V']['ereu']}")
    p(f"  ER_source（源下游中位 / 地化背景）：河漫滩 细粒 "
      f"{SAVA_T3['alluvial']['ersource_fine']}、粗粒 "
      f"{SAVA_T3['alluvial']['ersource_coarse']}；"
      f"河床砂 细粒 {SAVA_T3['stream']['ersource_fine']}、"
      f"粗粒 {SAVA_T3['stream']['ersource_coarse']}")
    p("  ER_frac 0.7 < 1 细粒富集 + ER_source 12~15 倍高 => 冶炼厂型污染")
    p("  河床砂 ER_source 6.1~7.1 明显低于漫滩 => 污染集中在漫滩而非河床")

    p()
    p("=" * 76)
    p("表 5  高值 != 污染")
    p("=" * 76)
    p("【a】贵州矿化带土壤（天然矿化，不是工业污染）[L] Sci Rep 2025")
    for el in ("Cd", "Pb", "Zn"):
        d = GUIZHOU_SOIL[el]
        p(f"    {el}: 平均 {d['mean']} / 背景 {d['bv']} mg/kg = {d['mean'] / d['bv']:.2f} 倍")
    p(f"    Cd 中位 {GUIZHOU_SOIL['Cd']['median']}、最大 {GUIZHOU_SOIL['Cd']['max']} mg/kg，"
      f"CV {GUIZHOU_SOIL['Cd']['cv']:.0f}%")
    p(f"    {'、'.join(GUIZHOU_SOIL['not_elevated'])} 与省背景值相当，平均含量是背景值的 "
      + "、".join(f"{GUIZHOU_SOIL['mean_ratios'][e]:.2f} 倍"
                  for e in GUIZHOU_SOIL["not_elevated"]))
    p("    Cd、Pb、Zn、As、Hg 超背景值，平均含量是背景值的 "
      + "、".join(f"{GUIZHOU_SOIL['mean_ratios'][e]:.2f} 倍"
                  for e in ("Cd", "Pb", "Zn", "As", "Hg")))
    p(f"    土壤 pH {GUIZHOU_SOIL['pH']['min']:.2f}~{GUIZHOU_SOIL['pH']['max']:.2f}，"
      f"均值 {GUIZHOU_SOIL['pH']['mean']:.2f}")
    p("【b】安徽秋浦河：官方认定的 Cd 高背景区 [L] 资源环境与工程 2025")
    p(f"    流域土壤 Cd 平均 {QIUPU['soil_cd_mean']} mg/kg，"
      f"是全国水系沉积物背景值的 {QIUPU['soil_cd_mean'] / BG_CHINA_SEDIMENT:.1f} 倍")
    p(f"    下游耕地 5 件土壤样 δ114/110Cd {QIUPU['delta_range'][0]:+.2f} ~ "
      f"{QIUPU['delta_range'][1]:+.2f}‰（均值 {QIUPU['delta_mean']:+.2f}‰），"
      f"中游孤峰组硅质岩 {QIUPU['rock_gufeng']:+.2f}‰，"
      f"上游寒武系—奥陶系岩石 {QIUPU['rock_cambrian_range'][0]:+.2f} ~ "
      f"{QIUPU['rock_cambrian_range'][1]:+.2f}‰ -> 自然来源")
    p(f"    有效态 Cd 占比（{QIUPU['avail_def']}）："
      f"上游 {QIUPU['avail_up']}%、中下游 {QIUPU['avail_mid_low']}%")
    p(f"【c】完达山：采矿是 Cd 的主要人为来源 [L] Toxics 2026")
    p(f"    {WANDA['n']} 件河流沉积物，Cd 均值 {WANDA['mean']} mg/kg 是完达山区域化探背景值 "
      f"{WANDA['bg']} 的 {WANDA['times_bg']} 倍，CV {WANDA['cv']}%，最大 {WANDA['max']} mg/kg")
    for name, els in WANDA_ENDMEMBERS.items():
        p(f"    端元 {name}：{'、'.join(els)}")
    p("    APCS-MLR 采矿源贡献："
      + "、".join(f"{e} {WANDA_APCS[e]}%" for e in WANDA_APCS_MINING))
    p("    APCS-MLR 农业源贡献："
      + "、".join(f"{e} {WANDA_APCS[e]}%" for e in WANDA_APCS_AGRI))
    p(f"    自然风化源 PC1 对除铬以外的所有元素贡献 < {WANDA_GEOGENIC_MAX:.0f}%，"
      f"铬是唯一例外：{WANDA_GEOGENIC_CR}%")
    p(f"    PCA 三个特征值 {' / '.join(str(v) for v in WANDA_PCA['eigenvalues'])}，"
      f"累计解释 {WANDA_PCA['variance_pct']}% 的方差")

    p()
    p("=" * 76)
    p("表 6  同位素把「自然」和「冶炼」分开")
    p("=" * 76)
    p(f"  秋浦河（自然风化）：δ114/110Cd {QIUPU['delta_range'][0]:+.2f} ~ "
      f"{QIUPU['delta_range'][1]:+.2f}‰（均值 {QIUPU['delta_mean']:+.2f}‰），"
      f"与{QIUPU['match_rock']} {QIUPU['rock_gufeng']:+.2f}‰ 一致")
    p(f"  北江（污染河流）：δ114/110Cd {BEIJIANG['delta_range'][0]:+.2f} ~ "
      f"{BEIJIANG['delta_range'][1]:+.2f}‰（均值 {BEIJIANG['delta_mean']:+.2f}‰），"
      f"冶炼厂和电子废弃物镇采样点分馏量最大；"
      "该区间与秋浦河几乎整个重叠 -> 单看 δ 分不开天然与冶炼")
    p(f"  韶关铅锌冶炼（{SHAOGUAN['model']}）：重同位素富集于{SHAOGUAN['heavy_in']}、"
      f"轻同位素富集于{SHAOGUAN['light_in']}")
    p(f"    下游沉积物柱 ε114/110Cd {SHAOGUAN['eps_core'][0]:+.2f} ~ "
      f"{SHAOGUAN['eps_core'][1]:+.2f}，落在炉渣 {SHAOGUAN['eps_slag']:+.2f} 与"
      f"烟尘 {SHAOGUAN['eps_dust']:+.2f} 之间")
    p(f"    二元混合模型：炉渣占 {SHAOGUAN['slag_share'][0]}~{SHAOGUAN['slag_share'][1]}%、"
      f"烟尘占 {SHAOGUAN['dust_share'][0]}~{SHAOGUAN['dust_share'][1]}%")
    p(f"  北江冶炼厂下游 1 m 剖面：Cd {NORTHRIVER_PROFILE['cd_range'][0]:.0f}-"
      f"{NORTHRIVER_PROFILE['cd_range'][1]:.0f} mg/kg，检出"
      f"{NORTHRIVER_PROFILE['mineral']}，来源指向{NORTHRIVER_PROFILE['source']}")

    p()
    p("=" * 76)
    p("表 7  三个出口：同一套标准下的落点")
    p("=" * 76)
    p("GB 15618 是土壤标准，管的是农用地；GB 18668 是海洋沉积物标准。")
    p("底泥本身没有国家级标准，按用途选：回作农用地走 GB 15618，作海洋用途走 GB 18668。")
    p("GB 15618 按 pH 分四档，Cd 水田筛选值 0.3 / 0.4 / 0.6 / 0.8，"
      "管制值 1.5 / 2.0 / 3.0 / 4.0 mg/kg")
    p("（对应 pH <=5.5 / 5.5-6.5 / 6.5-7.5 / >7.5；旱地筛选值更严一档，"
      "0.3 / 0.3 / 0.3 / 0.6，管制值两行相同）。六个场景里只有贵州报了 pH 统计值：")
    p(f"  pH {GUIZHOU_SOIL['pH']['min']:.2f}~{GUIZHOU_SOIL['pH']['max']:.2f}，"
      f"均值 {GUIZHOU_SOIL['pH']['mean']:.2f}，七成以上的样品在 6.50~7.60 之间，"
      "按 6.5~7.5 档算；"
      "其余五个场景没报 pH 统计值（秋浦河测了 pH 但正文没给），按 5.5~6.5 档算")
    p(f"{pad('高值来源', 22)}{'基质':>6}{'pH 档':>9}{'Cd mg/kg':>10}"
      f"{'筛选值':>10}{'管制值':>10}{'Igeo':>8}  背景值")
    scenarios = [
        ("秋浦河高背景区均值", "土壤", "5.5-6.5", QIUPU["soil_cd_mean"], BG_CHINA_SEDIMENT),
        ("贵州矿化带土壤中位", "土壤", "6.5-7.5", GUIZHOU_SOIL["Cd"]["median"], BG_GUIZHOU_SOIL),
        ("贵州矿化带土壤均值", "土壤", "6.5-7.5", GUIZHOU_SOIL["Cd"]["mean"], BG_GUIZHOU_SOIL),
        ("安宁河中位", "底泥", "5.5-6.5", ANNING["median"], BG_CHINA_SEDIMENT),
        ("安宁河最大", "底泥", "5.5-6.5", ANNING["max"], BG_CHINA_SEDIMENT),
        ("完达山最大", "底泥", "5.5-6.5", WANDA["max"], BG_CHINA_SEDIMENT),
    ]
    for name, matrix, tier, c, bg in scenarios:
        screen = GB15618_CD_SCREEN[tier]
        control = GB15618_CD_CONTROL[tier]
        p(f"{pad(name, 22)}{pad(matrix, 6)}{pad(tier, 9)}{c:>10.2f}"
          f"{c / screen:>9.2f} 倍{c / control:>9.2f} 倍{igeo(c, bg):>8.2f}  Bi={bg}")
    p()
    p("Igeo 一列按基质换背景值：贵州两行用贵州省表层土壤背景值 "
      f"{BG_GUIZHOU_SOIL}，底泥三行用全国水系沉积物背景值 {BG_CHINA_SEDIMENT}；"
      "秋浦河是土壤，安徽没有对应的省背景值，"
      f"这里沿用文章里的跨基质对比（是全国水系沉积物背景值的 "
      f"{QIUPU['soil_cd_mean'] / BG_CHINA_SEDIMENT:.1f} 倍）")
    p("（GB 18668 二类 1.50 mg/kg 是海洋沉积物标准，底泥不适用；"
      f"GB 5085.3 的 {GB50853_CD_LEACH} mg/L 是浸出液限值，跟 mg/kg 固体含量不能比倍数）")
    p()
    q_s, q_c = GB15618_CD_SCREEN["5.5-6.5"], GB15618_CD_CONTROL["5.5-6.5"]
    a_c = GB15618_CD_CONTROL["5.5-6.5"]
    g_s, g_c = GB15618_CD_SCREEN["6.5-7.5"], GB15618_CD_CONTROL["6.5-7.5"]
    g_med, g_mean = GUIZHOU_SOIL["Cd"]["median"], GUIZHOU_SOIL["Cd"]["mean"]
    p("落到哪一档，看的是过没过两道线里的一道：")
    p(f"  秋浦河 {QIUPU['soil_cd_mean']} mg/kg，筛选值 {q_s} 的 "
      f"{QIUPU['soil_cd_mean'] / q_s:.2f} 倍、管制值 {q_c} 的 "
      f"{QIUPU['soil_cd_mean'] / q_c:.2f} 倍，过第一道线没过第二道")
    p(f"  安宁河最大 {ANNING['max']} mg/kg，管制值 {a_c} 的 "
      f"{ANNING['max'] / a_c:.2f} 倍，两道都过")
    p(f"  贵州矿化带土壤中位 {g_med} mg/kg，筛选值 {g_s} 的 {g_med / g_s:.2f} 倍、"
      f"管制值 {g_c} 的 {g_med / g_c:.2f} 倍，过第一道线没过第二道")
    p(f"  贵州矿化带土壤均值 {g_mean} mg/kg，筛选值 {g_s} 的 {g_mean / g_s:.2f} 倍、"
      f"管制值 {g_c} 的 {g_mean / g_c:.2f} 倍，两道都过，但源是矿化不是冶炼")
    p("  所以过线只是进门的条件，进门之后按源分三路：治理、豁免、勘查靶区。")

    p()
    p("=" * 76)
    p("表 8  污染分布：多少样点真的落在污染档 [L] 完达山 Toxics 2026 / 安宁河 Toxics 2026")
    p("=" * 76)
    p("【a】完达山 1423 件样品的污染因子 CF 分级（Cd / As / Hg 三个元素）")
    for el, counts in WANDA_CF_COUNTS.items():
        total = sum(counts.values())
        p(f"    {el}: " + "、".join(f"{k} {v} 件（{v / total * 100:.1f}%）"
                                    for k, v in counts.items()))
    p(f"    全区 PLI 平均 {WANDA_PLI_MEAN} -> {pli_grade(WANDA_PLI_MEAN)}；"
      f"{WANDA_PLI_ZONES['轻度污染区']}% 轻度污染区、"
      f"{WANDA_PLI_ZONES['中度污染区']}% 中度污染区，无重度污染区")
    p(f"    全区 RI 平均 {WANDA_RI_MEAN} -> {ri_grade(WANDA_RI_MEAN, RI_BANDS_WANDA)}生态风险；"
      f"{WANDA_RI_ZONES['中等生态风险']}% 中等、{WANDA_RI_ZONES['较高生态风险']}% 较高")
    p(f"    全区 Igeo 最大 {WANDA_IGEO_MAX}")
    p("【b】同样 1423 件样品，换成 Igeo 分级（档界跟 CF 不同）")
    for el, counts in WANDA_IGEO_COUNTS.items():
        total = sum(counts.values())
        p(f"    {el}: " + "、".join(f"{k} {v} 件（{v / total * 100:.1f}%）"
                                    for k, v in counts.items()))
    p()
    p("    同一批样品，两个指数，治理范围差几倍：")
    for el in ("Cd", "As", "Hg"):
        cf_mid = WANDA_CF_COUNTS[el]["中度污染"] + WANDA_CF_COUNTS[el]["重度污染"]
        ig_mid = WANDA_IGEO_COUNTS[el]["中度污染"] + WANDA_IGEO_COUNTS[el]["重度污染"]
        ratio = cf_mid / ig_mid if ig_mid else float("inf")
        p(f"      {el}: CF 中度以上 {cf_mid} 件（{cf_mid / 1423 * 100:.1f}%）、"
          f"Igeo 中度以上 {ig_mid} 件（{ig_mid / 1423 * 100:.1f}%），"
          f"相差 {ratio:.1f} 倍；"
          f"判无污染的 CF {WANDA_CF_COUNTS[el]['无污染']} 件、"
          f"Igeo {WANDA_IGEO_COUNTS[el]['无污染']} 件")
    p(f"    论文结论里的主要污染物是 {' 和 '.join(WANDA_DOMINANT_POLLUTANTS)}，"
      f"不是镉：砷 Igeo 重度污染 {WANDA_IGEO_COUNTS['As']['重度污染']} 件（3.1%）"
      f"是八元素里最多，镉只有 {WANDA_IGEO_COUNTS['Cd']['重度污染']} 件（0.1%）")
    p("【c】安宁河 80 件样品")
    p("    Igeo 均值：" + "、".join(f"{k} {v}" for k, v in ANNING_IGEO_MEAN.items()))
    p(f"    RI 平均 {ANNING_RI_MEAN} -> {ri_grade(ANNING_RI_MEAN, RI_BANDS_ANNING)}生态风险；"
      f"Cd 单元素 Er {ANNING_RI_CD_ER}，占总 RI 的 {ANNING_RI_CD_SHARE}%，"
      f"其余 7 个元素都在低风险档")
    p(f"    确定性人体健康风险：THI 成人 {ANNING_MC['thi_adult']:.2e}、"
      f"儿童 {ANNING_MC['thi_child']:.2e}，都 < 1")
    p(f"    蒙特卡洛：儿童 TCR > 1.0e-4 的概率 {ANNING_MC['child_tcr_prob']}%"
      f"（均值 {ANNING_MC['child_tcr_mean']:.2e}、95 分位 "
      f"{ANNING_MC['child_tcr_p95']:.2e}），成人 {ANNING_MC['adult_tcr_prob']}%"
      f"（95 分位 {ANNING_MC['adult_tcr_p95']:.2e}）")
    p(f"    儿童 THI > 1 的概率约 {ANNING_MC['child_thi_prob']:.0f}%")
    p("    口径分歧：TCR 超阈由 "
      + "、".join(ANNING_MC["tcr_drivers"]) + " 主导，RI 由 Cd 主导")
    p("    非致癌风险元素排序："
      + " > ".join(ANNING_MC["thi_order"]))
    p(f"    而 {'、'.join(ANNING_UNPOLLUTED)} 在污染指标上本来就贴近背景值"
      "（论文结论：基本未污染）")
    p()
    p("    论文给的管理建议按元素分两条路：")
    p(f"      {'、'.join(ANNING_MANAGEMENT['source_control'])} 走控源："
      f"{ANNING_MANAGEMENT['source_measures']}")
    p(f"      {'、'.join(ANNING_MANAGEMENT['pathway'])} 走暴露路径："
      f"{ANNING_MANAGEMENT['pathway_measures']}")
    p(f"    局限：{ANNING_LIMIT}")

    p()
    p("=" * 76)
    p("表 9  换分级表：同一个数，两种叫法 [L]")
    p("=" * 76)
    p(f"  {pad('取值', 34)}{'Muller 七级':<14}{'完达山四级':<12}")
    for v, label in [(igeo(0.68, BG_CHINA_SEDIMENT), "安宁河中位 0.68"),
                     (igeo(3.0, BG_CHINA_SEDIMENT), "C = 3.0"),
                     (WANDA_IGEO_MAX, "完达山 Igeo 最大值")]:
        p(f"  {pad(label + f'（Igeo {v:.2f}）', 34)}{igeo_grade(v):<14}"
          f"{igeo_grade(v, IGEO_GRADES_4):<12}")
    p(f"  RI {WANDA_RI_MEAN}：完达山分级 -> {ri_grade(WANDA_RI_MEAN, RI_BANDS_WANDA)}；"
      f"安宁河分级 -> {ri_grade(WANDA_RI_MEAN, RI_BANDS_ANNING)}")
    p(f"  RI {ANNING_RI_MEAN}：完达山分级 -> {ri_grade(ANNING_RI_MEAN, RI_BANDS_WANDA)}；"
      f"安宁河分级 -> {ri_grade(ANNING_RI_MEAN, RI_BANDS_ANNING)}")

    p()
    p("=" * 76)
    p("表 10  公式回代核对 [C]")
    p("=" * 76)
    er_cd = eri(ANNING["mean"], BG_CHINA_SEDIMENT, TRI["Cd"])
    p(f"  安宁河 Cd 的 Er = 30 x ({ANNING['mean']} / {BG_CHINA_SEDIMENT}) = {er_cd:.2f}，"
      f"文献给 {ANNING_RI_CD_ER}（文献是逐点算 Er 再平均，这里用均值算，"
      f"差 {abs(er_cd - ANNING_RI_CD_ER) / ANNING_RI_CD_ER * 100:.1f}%）")
    pli_mean = pli([v[0] for v in WANDA_ELEMENTS.values()],
                    [v[1] for v in WANDA_ELEMENTS.values()])
    p(f"  完达山 PLI：用八元素均值算 = {pli_mean:.3f} -> {pli_grade(pli_mean)}；"
      f"文献逐点算完再平均 = {WANDA_PLI_MEAN} -> {pli_grade(WANDA_PLI_MEAN)}")
    for el in ("Cd", "As"):
        mean, bg_study, bg_geo = WANDA_ELEMENTS[el]
        p(f"  完达山 {el} 平均 CF：按研究区背景值 {bg_study} 算 = {cf(mean, bg_study):.2f}"
          f"（{cf_grade(cf(mean, bg_study))}）；按区域化探背景值 {bg_geo} 算 = "
          f"{cf(mean, bg_geo):.2f}（{cf_grade(cf(mean, bg_geo))}）")

    p()
    p("=" * 76)
    p("表 11  安宁河样本自身的分布特征")
    p("=" * 76)
    p(f"范围 {ANNING['min']}-{ANNING['max']} mg/kg，均值 {ANNING['mean']} ± {ANNING['sd']}，"
      f"中位 {ANNING['median']}，CV {ANNING['cv']}%")
    p(f"均值 {ANNING['mean']:.2f} > 中位 {ANNING['median']:.2f}，右偏，中位数是更稳的代表值")
    p("对照河流：" + "、".join(f"{k} {v}" for k, v in RIVER_COMPARISON.items()))
    p()
    p("分河段空间格局（正文 3.2 节，Kriging 插值结果）：")
    for reach, els in ANNING_REACH.items():
        p(f"  {reach}：{'、'.join(els)} 的高浓度带集中在这段")
    p("  中游是铁矿开采和金属冶炼厂密集段；上游是 Pb 连片富集带和 Cr/Ni 高浓度区")
    p("  同一条河，不同元素的高值落在不同河段 -> 源的位置由元素组合定位到具体河段")
    p()
    p("PMF 源解析（摘要）：")
    for src, els in ANNING_PMF.items():
        p(f"  {src}：{'、'.join(els)}")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "articles", "env", "data")
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "sediment_cd_attribution.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        f.write("表,行,列,值,单位,说明\n")
        for name, bg, c, v, g in rows:
            f.write(f"参照系,{name},C={c},{v:.4f},Igeo,{g}；Bi={bg}\n")
        f.write(f"统计口径,76幅_剔除X±3S前,T=X+2S,{t_before:.4f},mg/kg,"
                f"X={GEM76_CD['mean_before']}；S={GEM76_CD['sd_before']}\n")
        f.write(f"统计口径,76幅_剔除X±3S后,T=X+2S,{t_after:.4f},mg/kg,"
                f"X={GEM76_CD['mean_after']}；S={GEM76_CD['sd_after']}\n")
        for sec in HUNAN["sections"]:
            if sec in HUNAN["both_ends"]:
                trend = "两头都高"
            elif sec in HUNAN["fine_rich"]:
                trend = "细粒高"
            elif sec in HUNAN["coarse_rich"]:
                trend = "粗粒高"
            else:
                trend = "正文未给趋势"
            f.write(f"粒级,湖南{sec},粒度趋势,{trend},定性,Sci Rep 2024 正文\n")
        for label, calc, pub in frac_rows:
            f.write(f"三层判别,{label},ER_frac重算,{calc:.4f},倍,论文值{pub}\n")
        f.write(f"三层判别,河漫滩_萨维尼亚,ER_EU,{SAVA_T3['alluvial']['S']['ereu']},倍,论文值\n")
        f.write(f"三层判别,河漫滩_弗格拉亚,ER_EU,{SAVA_T3['alluvial']['V']['ereu']},倍,论文值\n")
        f.write(f"三层判别,河漫滩,ER_source_细粒,{SAVA_T3['alluvial']['ersource_fine']},倍,论文值\n")
        f.write(f"三层判别,河漫滩,ER_source_粗粒,{SAVA_T3['alluvial']['ersource_coarse']},倍,论文值\n")
        f.write(f"源判别,秋浦河,土壤Cd均值,{QIUPU['soil_cd_mean']},mg/kg,高背景区\n")
        f.write(f"源判别,秋浦河,delta114/110Cd下限,{QIUPU['delta_range'][0]},permil,"
                f"表5 五件下游耕地土壤样\n")
        f.write(f"源判别,秋浦河,delta114/110Cd上限,{QIUPU['delta_range'][1]},permil,"
                f"表5 五件下游耕地土壤样\n")
        f.write(f"源判别,秋浦河,delta114/110Cd均值,{QIUPU['delta_mean']},permil,"
                f"摘要漏负号以表5为准\n")
        f.write(f"源判别,孤峰组硅质岩,delta114/110Cd,{QIUPU['rock_gufeng']},permil,"
                f"表5 QPYS01\n")
        f.write(f"源判别,寒武系奥陶系岩石,delta114/110Cd下限,"
                f"{QIUPU['rock_cambrian_range'][0]},permil,表5 YST2~YST4 灰岩\n")
        f.write(f"源判别,寒武系奥陶系岩石,delta114/110Cd上限,"
                f"{QIUPU['rock_cambrian_range'][1]},permil,表5 YST1 荷塘组炭质岩\n")
        f.write(f"源判别,北江,delta114/110Cd下限,{BEIJIANG['delta_range'][0]},permil,污染河流\n")
        f.write(f"源判别,北江,delta114/110Cd上限,{BEIJIANG['delta_range'][1]},permil,污染河流\n")
        f.write(f"源判别,完达山,APCS采矿源Cd贡献,{WANDA_APCS['Cd']},percent,采矿源\n")
        f.write(f"污染分布,完达山,PLI平均,{WANDA_PLI_MEAN},无量纲,逐点计算后平均\n")
        f.write(f"污染分布,完达山,RI平均,{WANDA_RI_MEAN},无量纲,低生态风险档\n")
        f.write(f"污染分布,安宁河,RI平均,{ANNING_RI_MEAN},无量纲,较高生态风险档\n")
        f.write(f"污染分布,安宁河,Cd占RI比例,{ANNING_RI_CD_SHARE},percent,单元素\n")
        f.write(f"污染分布,安宁河,儿童TCR超阈概率,{ANNING_MC['child_tcr_prob']},percent,"
                f"蒙特卡洛\n")
        for el, counts in WANDA_IGEO_COUNTS.items():
            for grade, v in counts.items():
                f.write(f"污染分布,完达山_{el},Igeo_{grade},{v},件,"
                        f"占{v / 1423 * 100:.1f}%\n")
        for el, counts in WANDA_CF_COUNTS.items():
            for grade, v in counts.items():
                f.write(f"污染分布,完达山_{el},CF_{grade},{v},件,"
                        f"占{v / 1423 * 100:.1f}%\n")
        f.write(f"源判别,完达山,自然源PC1对铬贡献,{WANDA_GEOGENIC_CR},percent,"
                f"其余元素<{WANDA_GEOGENIC_MAX:.0f}%\n")
        f.write(f"源判别,完达山,PCA累计解释方差,{WANDA_PCA['variance_pct']},percent,"
                f"特征值{'/'.join(str(v) for v in WANDA_PCA['eigenvalues'])}\n")
        f.write(f"健康风险,安宁河,儿童THI,{ANNING_MC['thi_child']:.2e},无量纲,确定性\n")
        f.write(f"健康风险,安宁河,成人THI,{ANNING_MC['thi_adult']:.2e},无量纲,确定性\n")
        for tier in GB15618_CD_SCREEN:
            f.write(f"标准,GB15618,pH{tier}筛选值,{GB15618_CD_SCREEN[tier]},mg/kg,土壤_水田\n")
            f.write(f"标准,GB15618,pH{tier}筛选值,{GB15618_CD_SCREEN_DRY[tier]},mg/kg,土壤_其他旱地\n")
            f.write(f"标准,GB15618,pH{tier}管制值,{GB15618_CD_CONTROL[tier]},mg/kg,土壤_两行相同\n")
        f.write(f"高背景,贵州矿化带,pH均值,{GUIZHOU_SOIL['pH']['mean']},无量纲,"
                f"范围{GUIZHOU_SOIL['pH']['min']:.2f}~{GUIZHOU_SOIL['pH']['max']:.2f}；"
                f"按6.5-7.5档\n")
        for el, ratio in GUIZHOU_SOIL["mean_ratios"].items():
            f.write(f"高背景,贵州矿化带,{el}平均含量是省背景值的倍数,{ratio},倍,"
                    f"按该文表1\n")
        f.write(f"分级表,Muller七级,完达山Igeo最大值,{WANDA_IGEO_MAX},Igeo,"
                f"{igeo_grade(WANDA_IGEO_MAX)}\n")
        f.write(f"分级表,完达山四级,完达山Igeo最大值,{WANDA_IGEO_MAX},Igeo,"
                f"{igeo_grade(WANDA_IGEO_MAX, IGEO_GRADES_4)}\n")
        f.write(f"分级表,完达山RI分级,完达山RI平均,{WANDA_RI_MEAN},RI,"
                f"{ri_grade(WANDA_RI_MEAN, RI_BANDS_WANDA)}\n")
        f.write(f"分级表,安宁河RI分级,完达山RI平均,{WANDA_RI_MEAN},RI,"
                f"{ri_grade(WANDA_RI_MEAN, RI_BANDS_ANNING)}\n")
        f.write(f"公式核对,安宁河,Cd的Er,{er_cd:.2f},无量纲,文献值{ANNING_RI_CD_ER}\n")
        f.write(f"公式核对,完达山,PLI均值口径,{pli_mean:.4f},无量纲,"
                f"逐点平均{WANDA_PLI_MEAN}\n")
    p()
    p(f"CSV 已写出：{os.path.relpath(csv_path)}")

    return "\n".join(out_lines)


if __name__ == "__main__":
    main()
