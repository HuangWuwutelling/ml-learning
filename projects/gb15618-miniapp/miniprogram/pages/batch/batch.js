// 模板文件的云存储 ID（部署后由用户替换）
const TEMPLATE_FILE_ID = 'cloud://gb15618-miniapp.XXXX/gb15618_template.xlsx';

Page({
  data: {
    fileID: '',
    filename: '',
    loading: false,
    result: null,
  },

  async onChooseFile() {
    try {
      const res = await wx.chooseMessageFile({
        type: 'file',
        extension: ['xlsx'],
      });
      const file = res.tempFiles[0];
      this.setData({ filename: file.name, fileID: '' });
      const upload = await wx.cloud.uploadFile({
        cloudPath: `batch/${Date.now()}_${file.name}`,
        filePath: file.path,
      });
      this.setData({ fileID: upload.fileID });
      wx.showToast({ title: '上传成功', icon: 'success' });
    } catch (err) {
      wx.showToast({ title: '选择/上传失败', icon: 'none' });
      console.error(err);
    }
  },

  async onDownloadTemplate() {
    if (TEMPLATE_FILE_ID.includes('XXXX')) {
      wx.showToast({ title: '请先在 batch.js 配置模板 fileID', icon: 'none' });
      return;
    }
    try {
      const res = await wx.cloud.downloadFile({ fileID: TEMPLATE_FILE_ID });
      const fs = wx.getFileSystemManager();
      const filePath = `${wx.env.USER_DATA_PATH}/gb15618_template.xlsx`;
      fs.writeFileSync(filePath, res.fileContent, 'binary');
      await wx.openDocument({
        filePath,
        showMenu: true,
      });
    } catch (err) {
      wx.showToast({ title: '模板下载失败', icon: 'none' });
      console.error(err);
    }
  },

  async onUpload() {
    this.setData({ loading: true });
    try {
      const res = await wx.cloud.callFunction({
        name: 'parseExcel',
        data: { fileID: this.data.fileID },
      });
      if (res.result && res.result.error) {
        wx.showToast({ title: res.result.error, icon: 'none', duration: 3000 });
        return;
      }
      this.setData({ result: res.result });
    } catch (err) {
      wx.showToast({ title: '调用失败：' + (err.errMsg || err.message), icon: 'none' });
      console.error(err);
    } finally {
      this.setData({ loading: false });
    }
  },

  onExportCSV() {
    const r = this.data.result;
    if (!r) return;
    const lines = ['riskLevel,total,' + Object.keys(r.summary).join(',')];
    lines.push(`summary,,${r.summary['优先保护类']},${r.summary['安全利用类']},${r.summary['严格管控类']}`);
    if (r.errors && r.errors.length > 0) {
      lines.push('');
      lines.push('row,reason');
      for (const e of r.errors) {
        lines.push(`${e.row},"${e.reason}"`);
      }
    }
    const csv = lines.join('\n');
    const fs = wx.getFileSystemManager();
    const filePath = `${wx.env.USER_DATA_PATH}/gb15618_batch_summary.csv`;
    fs.writeFileSync(filePath, csv, 'utf-8');
    wx.openDocument({ filePath, showMenu: true });
  },
});