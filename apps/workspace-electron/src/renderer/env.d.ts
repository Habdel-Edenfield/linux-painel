import type { SidebarModule, WorkspaceState } from '../shared/workspace';

export {};

declare global {
  interface Window {
    workspaceApp: {
      version: string;
      getBootstrapState(): Promise<WorkspaceState>;
      setActiveSidebarModule(module: SidebarModule): Promise<WorkspaceState>;
    };
  }
}
