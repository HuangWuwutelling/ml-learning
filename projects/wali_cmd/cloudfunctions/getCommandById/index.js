const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();

const COLLECTIONS = ['linux_commands', 'windows_commands'];

exports.main = async (event, context) => {
  const { id, platform } = event;

  if (!id) {
    return { code: 400, message: 'id is required' };
  }

  // 如果指定 platform，只查对应 collection
  const collections = platform ? [`${platform}_commands`] : COLLECTIONS;

  for (const coll of collections) {
    try {
      const res = await db.collection(coll).doc(id).get();
      if (res.data) {
        return { code: 0, data: res.data };
      }
    } catch (err) {
      // doc not found, continue
      continue;
    }
  }

  return { code: 404, message: 'Command not found' };
};
