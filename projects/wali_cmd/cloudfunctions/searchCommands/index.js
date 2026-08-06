// 云函数：在云数据库里搜索命令
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();
const _ = db.command;

const COLLECTIONS = {
  linux: 'linux_commands',
  windows: 'windows_commands'
};

exports.main = async (event, context) => {
  const { keyword, platform, category, limit = 20 } = event;

  if (!keyword || keyword.trim() === '') {
    return { code: 0, data: [] };
  }

  const trimmedKeyword = keyword.trim();

  // 构造查询条件
  const matchCondition = _.or([
    { name: db.RegExp({ regexp: trimmedKeyword, options: 'i' }) },
    { description: db.RegExp({ regexp: trimmedKeyword, options: 'i' }) },
    { tags: trimmedKeyword }
  ]);

  const baseCondition = {
    ...matchCondition
  };
  if (category) {
    baseCondition.category = category;
  }

  // 决定查哪些 collection
  const targets = platform && COLLECTIONS[platform]
    ? [COLLECTIONS[platform]]
    : Object.values(COLLECTIONS);

  const results = [];
  for (const coll of targets) {
    try {
      const res = await db.collection(coll).where(baseCondition)
        .orderBy('popularity', 'desc')
        .limit(limit)
        .field({ _id: true, name: true, category: true, syntax: true, description: true, tags: true, popularity: true })
        .get();
      results.push(...res.data);
    } catch (err) {
      console.error(`Error querying ${coll}:`, err);
    }
  }

  // 按 popularity 排序，取 top limit
  results.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
  return { code: 0, data: results.slice(0, limit) };
};