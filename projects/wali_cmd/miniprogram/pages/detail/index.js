Page({
  data: {
    command: null,
    loading: true
  },

  onLoad(options) {
    const { id, platform } = options;
    if (!id) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      return;
    }
    this.loadCommand(id, platform);
  },

  loadCommand(id, platform) {
    wx.cloud.callFunction({
      name: 'getCommandById',
      data: { id, platform }
    }).then(res => {
      if (res.result.code === 0) {
        this.setData({
          command: res.result.data,
          loading: false
        });
        wx.setNavigationBarTitle({ title: res.result.data.name });
      } else {
        this.setData({ loading: false });
        wx.showToast({ title: '未找到命令', icon: 'none' });
      }
    }).catch(err => {
      console.error('detail error:', err);
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    });
  },

  onCopySyntax() {
    if (this.data.command && this.data.command.syntax) {
      wx.setClipboardData({
        data: this.data.command.syntax,
        success: () => wx.showToast({ title: '已复制语法' })
      });
    }
  },

  onCopyExample(e) {
    const example = e.currentTarget.dataset.example;
    wx.setClipboardData({
      data: example,
      success: () => wx.showToast({ title: '已复制示例' })
    });
  }
});
