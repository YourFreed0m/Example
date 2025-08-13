const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('as', {
  pickAudio: () => ipcRenderer.invoke('pick-audio')
});