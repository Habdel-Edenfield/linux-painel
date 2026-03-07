import {
  app,
  BaseWindow,
  ipcMain,
  Menu,
  WebContentsView,
} from 'electron';
import path from 'node:path';
import type { WorkspaceState } from '../shared/workspace';
import {
  isSidebarModule,
  MIN_WINDOW_HEIGHT,
  MIN_WINDOW_WIDTH,
} from '../shared/workspace';
import { WorkspaceStore } from './workspace-store';

let mainWindow: BaseWindow | null = null;
let rootView: WebContentsView | null = null;
let persistWindowStateTimer: NodeJS.Timeout | null = null;

const workspaceStore = new WorkspaceStore();

function syncRootViewBounds() {
  if (!mainWindow || !rootView) {
    return;
  }

  const { width, height } = mainWindow.getContentBounds();
  rootView.setBounds({ x: 0, y: 0, width, height });
}

function captureWindowState(window: BaseWindow, current: WorkspaceState['window']) {
  const bounds = window.getNormalBounds();

  return {
    ...current,
    bounds: {
      x: bounds.x,
      y: bounds.y,
      width: bounds.width,
      height: bounds.height,
    },
    isMaximized: window.isMaximized(),
  };
}

function flushWindowState() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  workspaceStore.update((current) => ({
    ...current,
    window: captureWindowState(mainWindow!, current.window),
  }));
}

function queueWindowStatePersistence(immediate = false) {
  if (persistWindowStateTimer) {
    clearTimeout(persistWindowStateTimer);
    persistWindowStateTimer = null;
  }

  if (immediate) {
    flushWindowState();
    return;
  }

  persistWindowStateTimer = setTimeout(() => {
    persistWindowStateTimer = null;
    flushWindowState();
  }, 120);
}

function registerWorkspaceIpc() {
  ipcMain.removeHandler('workspace:get-bootstrap-state');
  ipcMain.removeHandler('workspace:set-active-sidebar-module');

  ipcMain.handle('workspace:get-bootstrap-state', () => workspaceStore.getState());
  ipcMain.handle(
    'workspace:set-active-sidebar-module',
    (_event, nextModule: unknown) => {
      if (!isSidebarModule(nextModule)) {
        throw new Error('Invalid sidebar module.');
      }

      return workspaceStore.setActiveSidebarModule(nextModule);
    },
  );
}

async function createMainWindow() {
  const persistedState = workspaceStore.getState();
  const { bounds, isMaximized } = persistedState.window;
  const window = new BaseWindow({
    width: bounds.width,
    height: bounds.height,
    minWidth: MIN_WINDOW_WIDTH,
    minHeight: MIN_WINDOW_HEIGHT,
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

  if (typeof bounds.x === 'number' && typeof bounds.y === 'number') {
    window.setPosition(bounds.x, bounds.y);
  }

  window.contentView.addChildView(view);
  syncRootViewBounds();

  view.webContents.once('did-finish-load', () => {
    if (!window.isDestroyed()) {
      window.show();
    }

    if (isMaximized) {
      setTimeout(() => {
        if (!window.isDestroyed() && !window.isMaximized()) {
          window.maximize();
        }
      }, 80);
    }
  });

  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    await view.webContents.loadURL(devServerUrl);
  } else {
    await view.webContents.loadFile(
      path.join(__dirname, '..', 'renderer', 'index.html'),
    );
  }

  window.on('move', () => {
    queueWindowStatePersistence();
  });
  window.on('resize', () => {
    syncRootViewBounds();
    queueWindowStatePersistence();
  });
  window.on('maximize', () => {
    queueWindowStatePersistence(true);
  });
  window.on('unmaximize', () => {
    queueWindowStatePersistence(true);
  });
  window.on('close', () => {
    queueWindowStatePersistence(true);
  });
  window.on('closed', () => {
    if (persistWindowStateTimer) {
      clearTimeout(persistWindowStateTimer);
      persistWindowStateTimer = null;
    }
    if (rootView && !rootView.webContents.isDestroyed()) {
      rootView.webContents.close();
    }
    rootView = null;
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  registerWorkspaceIpc();
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
