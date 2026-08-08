// cloudImport 云函数：手动触发，把 markdown 源数据导入云数据库
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const db = cloud.database();
const _ = db.command;

const LINUX_COMMANDS = require('./data/linux_commands.json');
const WINDOWS_COMMANDS = require('./data/windows_commands.json');

exports.main = async (event, context) => {
  const { secret } = event;
  if (secret !== 'import-data-2026') {
    return { code: 401, message: 'Unauthorized' };
  }

  // 批量导入 linux_commands：先按 name 删除旧条目，再 add 新条目
  for (const cmd of LINUX_COMMANDS) {
    try {
      await db.collection('linux_commands').where({ name: cmd.name }).remove();
      await db.collection('linux_commands').add({ data: cmd });
    } catch (err) {
      console.error(`Error importing linux/${cmd.name}:`, err);
    }
  }

  // 批量导入 windows_commands
  for (const cmd of WINDOWS_COMMANDS) {
    try {
      await db.collection('windows_commands').where({ name: cmd.name }).remove();
      await db.collection('windows_commands').add({ data: cmd });
    } catch (err) {
      console.error(`Error importing windows/${cmd.name}:`, err);
    }
  }

  return {
    code: 0,
    linux_count: LINUX_COMMANDS.length,
    windows_count: WINDOWS_COMMANDS.length
  };
};