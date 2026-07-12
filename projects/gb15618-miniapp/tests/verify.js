/**
 * 本地集成验证：模拟 parseExcel 云函数的核心逻辑（不写 db）
 *
 * 验证目标：
 *   1. 10 行正确数据 + 2 行错误数据 → total=10, errors=2
 *   2. 4 行优先保护 + 3 行安全利用 + 3 行严格管控（注意 S010 应被安全利用）
 *   3. 错误处理：缺失 pH、非法 crop
 */
const ExcelJS = require('exceljs');
const path = require('path');
const { evaluate, CROPS, METALS } = require('../data/gb15618_limits.js');

const REQUIRED_HEADERS = ['sampleId', 'crop', 'pH', ...METALS];

function validateRow(row) {
  if (!row.sampleId || typeof row.sampleId !== 'string') return 'sampleId 缺失';
  if (!row.crop || !CROPS.includes(row.crop)) return `crop 非法: ${row.crop}`;
  if (typeof row.pH !== 'number' || isNaN(row.pH) || row.pH < 0 || row.pH > 14) return 'pH 缺失或非法';
  for (const m of METALS) {
    const v = row[m];
    if (typeof v !== 'number' || isNaN(v) || v < 0) return `${m} 缺失或负值`;
  }
  return null;
}

async function main() {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile('tests/test_input.xlsx');
  const ws = wb.getWorksheet(1);

  const headers = (ws.getRow(1).values || []).slice(1);
  console.log('headers:', headers.join(','));
  for (const h of REQUIRED_HEADERS) {
    if (!headers.includes(h)) throw new Error(`缺少列：${h}`);
  }

  const summary = { '优先保护类': 0, '安全利用类': 0, '严格管控类': 0 };
  const errors = [];
  const results = [];
  let rowNumber = 1;

  for (const row of ws.getRows(2, ws.rowCount - 1)) {
    rowNumber++;
    if (rowNumber > ws.rowCount) break;
    const values = row.values.slice(1);
    const obj = {};
    headers.forEach((h, i) => { obj[h] = values[i]; });
    if (typeof obj.pH === 'string') obj.pH = parseFloat(obj.pH);
    for (const m of METALS) {
      if (typeof obj[m] === 'string') obj[m] = parseFloat(obj[m]);
    }

    const err = validateRow(obj);
    if (err) {
      errors.push({ row: rowNumber, reason: err, sampleId: obj.sampleId });
      continue;
    }
    const metalsOnly = {};
    for (const m of METALS) metalsOnly[m] = obj[m];
    const result = evaluate(obj.crop, obj.pH, metalsOnly);
    summary[result.riskLevel]++;
    results.push({ sampleId: obj.sampleId, riskLevel: result.riskLevel, maxPi: result.maxPi.toFixed(2) });
  }

  console.log('\n=== 详细结果 ===');
  for (const r of results) {
    console.log(`  ${r.sampleId}: ${r.riskLevel} (maxPi=${r.maxPi})`);
  }

  console.log('\n=== 汇总 ===');
  console.log('summary:', summary);
  console.log('total:', results.length);
  console.log('errors:', errors);

  console.log('\n=== 断言 ===');
  const assert = (cond, msg) => { if (!cond) { console.error('❌ FAIL:', msg); process.exit(1); } else console.log('✓', msg); };

  assert(summary['优先保护类'] === 4, `优先保护类应有 4 个，实际 ${summary['优先保护类']}`);
  assert(summary['安全利用类'] === 4, `安全利用类应有 4 个（含 Cu/Ni 大幅超标的 S010），实际 ${summary['安全利用类']}`);
  assert(summary['严格管控类'] === 2, `严格管控类应有 2 个，实际 ${summary['严格管控类']}`);
  assert(results.length === 10, `成功评价 10 行，实际 ${results.length}`);
  assert(errors.length === 2, `错误应有 2 行，实际 ${errors.length}`);
  assert(errors.some(e => e.sampleId === 'S011'), 'S011 (pH 缺失) 应被记入错误');
  assert(errors.some(e => e.sampleId === 'S012'), 'S012 (crop 非法) 应被记入错误');

  console.log('\n✅ 所有断言通过');
}

main().catch(e => { console.error(e); process.exit(1); });