Component({
  properties: {
    value: {
      type: String,
      value: ''
    },
    placeholder: {
      type: String,
      value: '搜索命令（如 find / ipconfig）'
    }
  },
  methods: {
    onInput(e) {
      this.triggerEvent('input', { value: e.detail.value });
    },
    onClear() {
      this.triggerEvent('clear');
    }
  }
});