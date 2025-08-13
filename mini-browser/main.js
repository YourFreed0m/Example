const { app, BrowserWindow, BrowserView, ipcMain, Menu, Tray, nativeImage } = require('electron');
const path = require('path');

let mainWindow;
let tray;
let tabs = [];
let activeTabIndex = -1;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 12, y: 12 },
    webPreferences: { preload: path.join(__dirname, 'preload.js') }
  });

  mainWindow.loadFile('renderer/index.html');

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

  // Tray
  const iconPath = path.join(__dirname, 'build', 'icon.png');
  const nimg = nativeImage.createFromPath(iconPath);
  tray = new Tray(nimg.isEmpty() ? undefined : nimg);
  tray.setToolTip('Mini Browser');
  tray.on('click', () => {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  });

  createTab('https://www.google.com');
}

function createTab(initialUrl) {
  const view = new BrowserView({ webPreferences: { nodeIntegration: false } });
  mainWindow.setBrowserView(view);
  const bounds = mainWindow.getBounds();
  // leave space for toolbar ~70px
  view.setBounds({ x: 0, y: 70, width: bounds.width, height: bounds.height - 70 });
  view.setAutoResize({ width: true, height: true });
  view.webContents.loadURL(initialUrl);

  tabs.push(view);
  activeTabIndex = tabs.length - 1;
  sendTabInfo();
}

function sendTabInfo() {
  const currentURL = activeTabIndex >= 0 ? tabs[activeTabIndex].webContents.getURL() : '';
  mainWindow.webContents.send('tabs:update', {
    count: tabs.length,
    active: activeTabIndex,
    url: currentURL
  });
}

ipcMain.handle('tabs:new', (_e, url) => {
  if (!/^https?:\/\//i.test(url)) url = 'https://duckduckgo.com/?q=' + encodeURIComponent(url);
  createTab(url);
});

ipcMain.handle('tabs:switch', (_e, index) => {
  if (index < 0 || index >= tabs.length) return;
  activeTabIndex = index;
  const view = tabs[activeTabIndex];
  mainWindow.setBrowserView(view);
  const b = mainWindow.getBounds();
  view.setBounds({ x: 0, y: 70, width: b.width, height: b.height - 70 });
  sendTabInfo();
});

ipcMain.handle('nav:go', (_evt, url) => {
  if (activeTabIndex < 0) return;
  if (!/^https?:\/\//i.test(url)) url = 'https://duckduckgo.com/?q=' + encodeURIComponent(url);
  tabs[activeTabIndex].webContents.loadURL(url);
  sendTabInfo();
});

ipcMain.handle('nav:back', () => {
  if (activeTabIndex < 0) return;
  const wc = tabs[activeTabIndex].webContents;
  if (wc.canGoBack()) wc.goBack();
  sendTabInfo();
});

ipcMain.handle('nav:forward', () => {
  if (activeTabIndex < 0) return;
  const wc = tabs[activeTabIndex].webContents;
  if (wc.canGoForward()) wc.goForward();
  sendTabInfo();
});

ipcMain.handle('nav:reload', () => {
  if (activeTabIndex < 0) return;
  tabs[activeTabIndex].webContents.reload();
  sendTabInfo();
});

ipcMain.handle('nav:get-url', () => {
  if (activeTabIndex < 0) return '';
  return tabs[activeTabIndex].webContents.getURL();
});

ipcMain.handle('tabs:close', (_e, index) => {
  if (index < 0 || index >= tabs.length) return;
  const [removed] = tabs.splice(index, 1);
  if (removed) removed.destroy();
  if (tabs.length === 0) createTab('about:blank');
  activeTabIndex = Math.max(0, Math.min(activeTabIndex, tabs.length - 1));
  const view = tabs[activeTabIndex];
  mainWindow.setBrowserView(view);
  const b = mainWindow.getBounds();
  view.setBounds({ x: 0, y: 70, width: b.width, height: b.height - 70 });
  sendTabInfo();
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