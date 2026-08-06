Component({
  properties: {
    command: {
      type: Object,
      value: {}
    }
  },
  methods: {
    onTap() {
      this.triggerEvent('tap', { id: this.data.command._id, platform: this.data.command.platform || 'linux' });
    }
  }
});