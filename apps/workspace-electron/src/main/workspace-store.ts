import { app } from 'electron';
import fs from 'node:fs';
import path from 'node:path';
import type { SidebarModule, WorkspaceState } from '../shared/workspace';
import {
  createDefaultWorkspaceState,
  hydrateWorkspaceState,
} from '../shared/workspace';

const WORKSPACE_FILENAME = 'workspace.json';

export class WorkspaceStore {
  private readonly filePath: string;
  private cachedState: WorkspaceState | null = null;

  constructor(filePath = path.join(app.getPath('userData'), WORKSPACE_FILENAME)) {
    this.filePath = filePath;
  }

  getState() {
    if (this.cachedState) {
      return this.cachedState;
    }

    if (!fs.existsSync(this.filePath)) {
      return this.writeState(createDefaultWorkspaceState());
    }

    try {
      const contents = fs.readFileSync(this.filePath, 'utf8');
      return this.writeState(hydrateWorkspaceState(JSON.parse(contents)));
    } catch {
      return this.writeState(createDefaultWorkspaceState());
    }
  }

  setActiveSidebarModule(module: SidebarModule) {
    return this.update((current) => ({
      ...current,
      window: {
        ...current.window,
        activeSidebarModule: module,
      },
    }));
  }

  update(updater: (state: WorkspaceState) => WorkspaceState) {
    const nextState = hydrateWorkspaceState(updater(this.getState()));
    return this.writeState(nextState);
  }

  private writeState(state: WorkspaceState) {
    fs.mkdirSync(path.dirname(this.filePath), { recursive: true });
    fs.writeFileSync(this.filePath, JSON.stringify(state, null, 2));
    this.cachedState = state;
    return state;
  }
}
