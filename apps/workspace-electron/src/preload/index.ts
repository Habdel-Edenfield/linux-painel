import { contextBridge, ipcRenderer } from 'electron';
import type { SidebarModule, WorkspaceState } from '../shared/workspace';

contextBridge.exposeInMainWorld('workspaceApp', {
  version: '0.1.0',
  getBootstrapState: () =>
    ipcRenderer.invoke('workspace:get-bootstrap-state') as Promise<WorkspaceState>,
  setActiveSidebarModule: (module: SidebarModule) =>
    ipcRenderer.invoke(
      'workspace:set-active-sidebar-module',
      module,
    ) as Promise<WorkspaceState>,
});
