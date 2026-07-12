/**
 * GB 15618-2018 农用地土壤污染风险管控标准 限值表
 *
 * 来源：GB 15618-2018 表 1（农用地土壤污染风险筛选值）和表 3（农用地土壤污染风险管制值）
 * 数据来源文件：articles/env/GB15618-2018重金属标准限值.xlsx
 * 单位：mg/kg
 *
 * 数据结构：
 *   LIMITS[crop][metal] = { screening: [4 pH 档数值], control: [4 pH 档数值] | null }
 *
 * pH 4 档索引：
 *   0: pH ≤ 5.5
 *   1: 5.5 < pH ≤ 6.5
 *   2: 6.5 < pH ≤ 7.5
 *   3: pH > 7.5
 *
 * 作物 → 标准原文「土地利用分类」映射：
 *   - Cd/Hg/As/Pb/Cr：原文分「水田」「其他」（其他 = 旱地 + 果园）
 *   - Cu：原文分「果园」「其他」（其他 = 水田 + 旱地）
 *   - Ni/Zn：原文不分类，所有作物共用
 *
 * 控制值（control）规则：
 *   - Cd/Hg/As/Pb/Cr：有控制值
 *   - Cu/Ni/Zn：没有控制值（永远不会被判严格管控类）
 *
 * 备注：As 控制值随 pH 升高而降低（与筛选值趋势相反），是 GB 15618 的特别规定。
 */

export const METALS = ['Cd', 'Hg', 'As', 'Pb', 'Cr', 'Cu', 'Zn', 'Ni'];

export const CROPS = ['水田', '旱地', '果园'];

export const PH_BOUNDS = [5.5, 6.5, 7.5]; // pH 4 档分界

export const LIMITS = {
  水田: {
    Cd:  { screening: [0.3, 0.4, 0.6, 0.8],   control: [1.5,   2,    3,    4]    },
    Hg:  { screening: [0.5, 0.5, 0.6, 1.0],   control: [2.0,   2.5,  4,    6]    },
    As:  { screening: [30,  30,  25,  20],     control: [200,   150,  120,  100]  },
    Pb:  { screening: [80,  100, 140, 240],    control: [400,   500,  700,  1000] },
    Cr:  { screening: [250, 250, 300, 350],    control: [800,   850,  1000, 1300] },
    // 水田 Cu 用「其他」组（不是果园组）
    Cu:  { screening: [50,  50,  100, 100],    control: null },
    Zn:  { screening: [200, 200, 250, 300],    control: null },
    Ni:  { screening: [60,  70,  100, 190],    control: null },
  },
  旱地: {
    // 旱地 Cd/Hg/As/Pb/Cr 用「其他」组
    Cd:  { screening: [0.3, 0.3, 0.3, 0.6],   control: [1.5,   2,    3,    4]    },
    Hg:  { screening: [1.3, 1.8, 2.4, 3.4],   control: [2.0,   2.5,  4,    6]    },
    As:  { screening: [40,  40,  30,  25],     control: [200,   150,  120,  100]  },
    Pb:  { screening: [70,  90,  120, 170],    control: [400,   500,  700,  1000] },
    Cr:  { screening: [150, 150, 200, 250],    control: [800,   850,  1000, 1300] },
    // 旱地 Cu 用「其他」组
    Cu:  { screening: [50,  50,  100, 100],    control: null },
    Zn:  { screening: [200, 200, 250, 300],    control: null },
    Ni:  { screening: [60,  70,  100, 190],    control: null },
  },
  果园: {
    // 果园 Cd/Hg/As/Pb/Cr 用「其他」组（旱地 + 果园共组）
    Cd:  { screening: [0.3, 0.3, 0.3, 0.6],   control: [1.5,   2,    3,    4]    },
    Hg:  { screening: [1.3, 1.8, 2.4, 3.4],   control: [2.0,   2.5,  4,    6]    },
    As:  { screening: [40,  40,  30,  25],     control: [200,   150,  120,  100]  },
    Pb:  { screening: [70,  90,  120, 170],    control: [400,   500,  700,  1000] },
    Cr:  { screening: [150, 150, 200, 250],    control: [800,   850,  1000, 1300] },
    // 果园 Cu 用「果园」组
    Cu:  { screening: [150, 150, 200, 200],    control: null },
    Zn:  { screening: [200, 200, 250, 300],    control: null },
    Ni:  { screening: [60,  70,  100, 190],    control: null },
  },
};

/**
 * 把 pH 数值映射到 0..3 索引
 */
export function pHIndex(pH) {
  if (pH <= 5.5) return 0;
  if (pH <= 6.5) return 1;
  if (pH <= 7.5) return 2;
  return 3;
}

/**
 * 取某个 (crop, pH, metal) 的限值
 */
export function getLimits(crop, pH, metal) {
  const limits = LIMITS[crop][metal];
  const idx = pHIndex(pH);
  return {
    screening: limits.screening[idx],
    control: limits.control === null ? null : limits.control[idx],
  };
}

/**
 * 单点评价
 * @param {string} crop 作物（水田/旱地/果园）
 * @param {number} pH 土壤 pH
 * @param {object} metals 8 种重金属浓度 {Cd, Hg, As, Pb, Cr, Cu, Zn, Ni}
 * @returns {object} { riskLevel, maxPi, maxPiControl, details }
 */
export function evaluate(crop, pH, metals) {
  const details = [];
  let maxPi = 0;
  let maxPiControl = 0;
  for (const [metal, measured] of Object.entries(metals)) {
    const { screening, control } = getLimits(crop, pH, metal);
    const pi = measured / screening;
    const piControl = control === null ? 0 : measured / control;
    details.push({ metal, measured, screening, control, pi, piControl });
    if (pi > maxPi) maxPi = pi;
    if (piControl > maxPiControl) maxPiControl = piControl;
  }

  let riskLevel;
  if (maxPi <= 1) {
    riskLevel = '优先保护类';
  } else if (maxPiControl <= 1) {
    riskLevel = '安全利用类';
  } else {
    riskLevel = '严格管控类';
  }
  return { riskLevel, maxPi, maxPiControl, details };
}