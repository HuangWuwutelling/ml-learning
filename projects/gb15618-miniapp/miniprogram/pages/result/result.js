Page({
  data: {
    data: null,
    levelClass: '',
  },

  onLoad(query) {
    let parsed;
    try {
      parsed = JSON.parse(decodeURIComponent(query.data));
    } catch (e) {
      wx.showToast({ title: '结果数据解析失败', icon: 'none' });
      return;
    }
    let levelClass = '';
    if (parsed.riskLevel === '优先保护类') levelClass = 'green';
    else if (parsed.riskLevel === '安全利用类') levelClass = 'yellow';
    else levelClass = 'red';
    // 预格式化数字，避免 wxml 里 toFixed 报错
    const formatted = {
      ...parsed,
      maxPiText: parsed.maxPi != null ? parsed.maxPi.toFixed(2) : '',
      details: (parsed.details || []).map(d => ({
        ...d,
        measuredText: d.measured != null ? String(d.measured) : '',
        piText: d.pi != null ? d.pi.toFixed(2) : '',
      })),
    };
    this.setData({ data: formatted, levelClass });
  },

  onExportCSV() {
    const d = this.data.data;
    if (!d || !d.details) return;
    const lines = ['metal,measured,screening,control,pi,piControl'];
    for (const r of d.details) {
      const control = r.control == null ? '' : r.control;
      lines.push(`${r.metal},${r.measured},${r.screening},${control},${r.pi.toFixed(4)},${(r.piControl || 0).toFixed(4)}`);
    }
    lines.push('');
    lines.push(`# riskLevel: ${d.riskLevel}`);
    lines.push(`# maxPi: ${d.maxPi.toFixed(4)}`);
    if (d.maxPiControl != null) lines.push(`# maxPiControl: ${d.maxPiControl.toFixed(4)}`);
    const csv = lines.join('\n');
    const fs = wx.getFileSystemManager();
    const filePath = `${wx.env.USER_DATA_PATH}/gb15618_result.csv`;
    fs.writeFileSync(filePath, csv, 'utf-8');
    wx.openDocument({ filePath, showMenu: true });
  },

  onBack() {
    wx.navigateBack();
  },
});