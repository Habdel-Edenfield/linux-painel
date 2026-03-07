import { app, BaseWindow, Menu, WebContentsView } from 'electron';
import path from 'node:path';

let mainWindow: BaseWindow | null = null;
let rootView: WebContentsView | null = null;

function syncRootViewBounds() {
  if (!mainWindow || !rootView) {
    return;
  }

  const { width, height } = mainWindow.getContentBounds();
  rootView.setBounds({ x: 0, y: 0, width, height });
}

async function createMainWindow() {
  const window = new BaseWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 640,
    show: false,
    title: 'Linux Painel Workspace',
    backgroundColor: '#0b1020',
  });

  const view = new WebContentsView({
    webPreferences: {
      preload: path.join(__dirname, '..', 'preload', 'index.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow = window;
  rootView = view;

  window.contentView.addChildView(view);
  syncRootViewBounds();

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    await view.webContents.loadURL(devServerUrl);
  } else {
    await view.webContents.loadFile(
      path.join(__dirname, '..', 'renderer', 'index.html'),
    );
  }

  view.webContents.once('did-finish-load', () => {
    if (!window.isDestroyed()) {
      window.show();
    }
  });

  window.on('resize', syncRootViewBounds);
  window.on('closed', () => {
    window.removeListener('resize', syncRootViewBounds);
    if (rootView && !rootView.webContents.isDestroyed()) {
      rootView.webContents.close();
    }
    rootView = null;
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  void createMainWindow();

  app.on('activate', () => {
    if (mainWindow === null) {
      void createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
