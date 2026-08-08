App({
  onLaunch() {
    if (!wx.cloud) {
      console.error('当前微信版本过低，请升级到最新微信版本');
    } else {
      wx.cloud.init({
        env: 'cloud1-d9g3044ey581a8c86',
        traceUser: true
      });
    }
  }
});
