// pages/category/index.js
Page({
  data: {
    platform: 'linux',
    categories: []
  },

  onLoad() {
    this.loadCategories('linux');
  },

  onPlatformChange(e) {
    const platform = e.currentTarget.dataset.platform;
    this.setData({ platform });
    this.loadCategories(platform);
  },

  loadCategories(platform) {
    wx.cloud.callFunction({
      name: 'getCategories',
      data: { platform }
    }).then(res => {
      if (res.result.code === 0) {
        const coll = `${platform}_commands`;
        const cats = (res.result.data && res.result.data[coll]) || [];
        cats.sort((a, b) => b.count - a.count);
        this.setData({ categories: cats });
      }
    }).catch(err => {
      console.error('category error:', err);
    });
  },

  onCategoryTap(e) {
    const category = e.currentTarget.dataset.category;
    wx.navigateTo({
      url: `/pages/search/index?category=${encodeURIComponent(category)}&platform=${this.data.platform}`
    });
  }
});