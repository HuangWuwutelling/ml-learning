App({
  onLaunch() {
    if (!wx.cloud) {
      console.error('当前微信版本过低，请升级到最新微信版本');
    } else {
      wx.cloud.init({
        env: 'wali-cmd-dev',
        traceUser: true
      });
    }
  }
});
