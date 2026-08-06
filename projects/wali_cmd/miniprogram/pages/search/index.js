// pages/search/index.js
Page({
  data: {
    keyword: '',
    platform: 'linux',
    results: [],
    loading: false
  },

  onLoad() {},

  onSearchInput(e) {
    const keyword = e.detail.value;
    this.setData({ keyword });
    if (keyword.trim()) {
      this.doSearch(keyword);
    } else {
      this.setData({ results: [] });
    }
  },

  onSearchClear() {
    this.setData({ keyword: '', results: [] });
  },

  onPlatformChange(e) {
    const platform = e.currentTarget.dataset.platform;
    this.setData({ platform });
    if (this.data.keyword.trim()) {
      this.doSearch(this.data.keyword);
    }
  },

  onCardTap(e) {
    const { id, platform } = e.detail;
    wx.navigateTo({
      url: `/pages/detail/index?id=${id}&platform=${platform}`
    });
  },

  debounce(fn, delay) {
    let timer = null;
    return (...args) => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  },

  doSearch(keyword) {
    if (this._searchTimer) clearTimeout(this._searchTimer);
    this._searchTimer = setTimeout(() => {
      this.setData({ loading: true });
      wx.cloud.callFunction({
        name: 'searchCommands',
        data: {
          keyword,
          platform: this.data.platform,
          limit: 20
        }
      }).then(res => {
        this.setData({
          results: res.result.data || [],
          loading: false
        });
      }).catch(err => {
        console.error('search error:', err);
        this.setData({ results: [], loading: false });
      });
    }, 300);
  }
});