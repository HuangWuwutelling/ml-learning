const METAL_KEYS = ['Cd', 'Hg', 'As', 'Pb', 'Cr', 'Cu', 'Zn', 'Ni'];

Page({
  data: {
    crops: ['水田', '旱地', '果园'],
    crop: '',
    pH: 7.0,
    metals: METAL_KEYS.map(k => ({ key: k, value: '' })),
    loading: false,
  },

  onCropChange(e) {
    this.setData({ crop: this.data.crops[e.detail.value] });
  },

  onPHChange(e) {
    this.setData({ pH: e.detail.value });
  },

  onMetalInput(e) {
    const key = e.currentTarget.dataset.key;
    const value = e.detail.value;
    const metals = this.data.metals.map(m =>
      m.key === key ? { ...m, value } : m
    );
    this.setData({ metals });
  },

  async onSubmit() {
    if (!this.data.crop) {
      wx.showToast({ title: '请选择作物', icon: 'none' });
      return;
    }
    const metals = {};
    for (const m of this.data.metals) {
      const v = parseFloat(m.value);
      if (isNaN(v) || v < 0) {
        wx.showToast({ title: `${m.key} 浓度不合法`, icon: 'none' });
        return;
      }
      metals[m.key] = v;
    }
    this.setData({ loading: true });
    try {
      const res = await wx.cloud.callFunction({
        name: 'evaluate',
        data: { crop: this.data.crop, pH: this.data.pH, metals },
      });
      if (res.result && res.result.error) {
        wx.showToast({ title: res.result.error, icon: 'none' });
        return;
      }
      const encoded = encodeURIComponent(JSON.stringify(res.result));
      wx.navigateTo({ url: `/pages/result/result?data=${encoded}` });
    } catch (err) {
      wx.showToast({ title: '调用失败：' + (err.errMsg || err.message), icon: 'none' });
      console.error(err);
    } finally {
      this.setData({ loading: false });
    }
  },
});