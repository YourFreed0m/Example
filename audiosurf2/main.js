const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 1280,
    height: 820,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

ipcMain.handle('pick-audio', async () => {
  const res = await dialog.showOpenDialog(win, { filters: [{ name: 'Audio', extensions: ['mp3','wav','ogg','m4a','flac'] }], properties: ['openFile'] });
  if (res.canceled || res.filePaths.length === 0) return null;
  return res.filePaths[0];
});

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});