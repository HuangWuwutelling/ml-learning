const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();
const $ = db.command.aggregate;

const COLLECTIONS = {
  linux: 'linux_commands',
  windows: 'windows_commands'
};

exports.main = async (event, context) => {
  const { platform } = event;

  const targets = platform && COLLECTIONS[platform]
    ? [COLLECTIONS[platform]]
    : Object.values(COLLECTIONS);

  const result = {};

  for (const coll of targets) {
    try {
      // MongoDB aggregate: group by category
      const res = await db.collection(coll).aggregate()
        .group({
          _id: '$category',
          count: $.sum(1)
        })
        .end();

      result[coll] = res.list.map(item => ({
        name: item._id || '未分类',
        count: item.count
      }));
    } catch (err) {
      console.error(`Error aggregating ${coll}:`, err);
      result[coll] = [];
    }
  }

  return { code: 0, data: result };
};
