const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });

  win.loadFile('renderer/index.html');

  const template = [
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));

  ipcMain.handle('nav:go', (_evt, url) => {
    if (!/^https?:\/\//i.test(url)) {
      url = 'https://duckduckgo.com/?q=' + encodeURIComponent(url);
    }
    win.webContents.loadURL(url);
  });

  ipcMain.handle('nav:back', () => win.webContents.canGoBack() && win.webContents.goBack());
  ipcMain.handle('nav:forward', () => win.webContents.canGoForward() && win.webContents.goForward());
  ipcMain.handle('nav:reload', () => win.webContents.reload());
  ipcMain.handle('nav:get-url', () => win.webContents.getURL());
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});