import { contextBridge } from 'electron';

contextBridge.exposeInMainWorld('workspaceApp', {
  version: '0.1.0',
});
