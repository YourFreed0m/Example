const { contextBridge, ipcRenderer } = require('electron');
const QRCode = require('qrcode');

contextBridge.exposeInMainWorld('mb', {
  go: (url) => ipcRenderer.invoke('nav:go', url),
  back: () => ipcRenderer.invoke('nav:back'),
  forward: () => ipcRenderer.invoke('nav:forward'),
  reload: () => ipcRenderer.invoke('nav:reload'),
  getUrl: () => ipcRenderer.invoke('nav:get-url'),
  newTab: (url) => ipcRenderer.invoke('tabs:new', url),
  switchTab: (index) => ipcRenderer.invoke('tabs:switch', index),
  closeTab: (index) => ipcRenderer.invoke('tabs:close', index),
  onTabsUpdate: (cb) => ipcRenderer.on('tabs:update', (_e, data) => cb(data)),
  qrFor: async (text) => QRCode.toDataURL(text, { margin: 1, width: 128 })
});