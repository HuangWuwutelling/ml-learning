const cloud = require('wx-server-sdk');
const ExcelJS = require('exceljs');
const { evaluate, CROPS, METALS } = require('./gb15618_limits.js');

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });
const db = cloud.database();
const COLLECTION = 'samples';

const REQUIRED_HEADERS = ['sampleId', 'crop', 'pH', ...METALS];

function validateRow(row) {
  if (!row.sampleId || typeof row.sampleId !== 'string') {
    return 'sampleId 缺失或非字符串';
  }
  if (!row.crop || !CROPS.includes(row.crop)) {
    return `crop 缺失或非法（须为 ${CROPS.join('/')}）`;
  }
  if (typeof row.pH !== 'number' || isNaN(row.pH) || row.pH < 0 || row.pH > 14) {
    return 'pH 缺失或非法（须 0-14）';
  }
  for (const m of METALS) {
    const v = row[m];
    if (typeof v !== 'number' || isNaN(v) || v < 0) {
      return `${m} 缺失或负值`;
    }
  }
  return null;
}

/**
 * Excel 批量评价云函数
 *
 * 入参：{ fileID: string }（云存储文件 ID）
 * 副作用：写云数据库 samples 集合
 * 返回：{
 *   total,         // 成功评价的行数
 *   summary: { '优先保护类': n, '安全利用类': n, '严格管控类': n },
 *   errors: [{ row, reason }]
 * }
 */
exports.main = async (event) => {
  const { fileID } = event || {};
  if (!fileID || typeof fileID !== 'string') {
    return { error: 'fileID is required' };
  }

  // 1. 从云存储下载
  let dlRes;
  try {
    dlRes = await cloud.downloadFile({ fileID });
  } catch (err) {
    return { error: `downloadFile failed: ${err.message || err}` };
  }
  const buffer = dlRes.fileContent;

  // 2. 解析 xlsx
  const wb = new ExcelJS.Workbook();
  try {
    await wb.xlsx.load(buffer);
  } catch (err) {
    return { error: `parse xlsx failed: ${err.message || err}` };
  }
  const ws = wb.getWorksheet(1);
  if (!ws) {
    return { error: 'xlsx 没有 sheet' };
  }

  // 校验表头
  const headers = (ws.getRow(1).values || []).slice(1); // ExcelJS 第 0 位是 undefined
  for (const h of REQUIRED_HEADERS) {
    if (!headers.includes(h)) {
      return { error: `xlsx 缺少必需列：${h}（当前列：${headers.join(', ')}）` };
    }
  }

  // 3. 遍历行
  const summary = { '优先保护类': 0, '安全利用类': 0, '严格管控类': 0 };
  const errors = [];
  let total = 0;
  let rowNumber = 1;

  for (const row of ws.getRows(2, ws.rowCount - 1)) {
    rowNumber++;
    if (rowNumber > ws.rowCount) break;
    const values = row.values.slice(1);
    const obj = {};
    headers.forEach((h, i) => { obj[h] = values[i]; });
    // 转 pH 为 number（ExcelJS 可能存为字符串）
    if (typeof obj.pH === 'string') obj.pH = parseFloat(obj.pH);
    for (const m of METALS) {
      if (typeof obj[m] === 'string') obj[m] = parseFloat(obj[m]);
    }

    const err = validateRow(obj);
    if (err) {
      errors.push({ row: rowNumber, reason: err });
      continue;
    }

    const metalsOnly = {};
    for (const m of METALS) metalsOnly[m] = obj[m];
    const result = evaluate(obj.crop, obj.pH, metalsOnly);
    summary[result.riskLevel]++;
    total++;

    try {
      await db.collection(COLLECTION).add({
        data: {
          sampleId: obj.sampleId,
          crop: obj.crop,
          pH: obj.pH,
          metals: {
            Cd: obj.Cd, Hg: obj.Hg, As: obj.As, Pb: obj.Pb,
            Cr: obj.Cr, Cu: obj.Cu, Zn: obj.Zn, Ni: obj.Ni,
          },
          riskLevel: result.riskLevel,
          maxPi: result.maxPi,
          maxPiControl: result.maxPiControl,
          createdAt: new Date(),
        },
      });
    } catch (err) {
      errors.push({ row: rowNumber, reason: `db write failed: ${err.message || err}` });
    }
  }

  return { total, summary, errors };
};