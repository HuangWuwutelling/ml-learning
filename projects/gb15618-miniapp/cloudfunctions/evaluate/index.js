const cloud = require('wx-server-sdk');
const { evaluate, CROPS, METALS } = require('./gb15618_limits.js');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

/**
 * 单点评价云函数
 *
 * 入参：{ crop: '水田'|'旱地'|'果园', pH: number, metals: {Cd, Hg, As, Pb, Cr, Cu, Zn, Ni} }
 * 返回：{ riskLevel, maxPi, maxPiControl, details } 或 { error: string }
 */
exports.main = async (event) => {
  const { crop, pH, metals } = event || {};

  // 参数校验
  if (!crop || !CROPS.includes(crop)) {
    return { error: `crop must be one of ${CROPS.join('/')}` };
  }
  if (typeof pH !== 'number' || isNaN(pH) || pH < 0 || pH > 14) {
    return { error: 'pH must be a number between 0 and 14' };
  }
  if (!metals || typeof metals !== 'object') {
    return { error: 'metals object is required' };
  }
  for (const m of METALS) {
    const v = metals[m];
    if (typeof v !== 'number' || isNaN(v) || v < 0) {
      return { error: `metals.${m} must be a non-negative number` };
    }
  }

  return evaluate(crop, pH, metals);
};