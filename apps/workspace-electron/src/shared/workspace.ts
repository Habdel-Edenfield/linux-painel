export const MIN_WINDOW_WIDTH = 960;
export const MIN_WINDOW_HEIGHT = 640;

export const SIDEBAR_MODULES = [
  'workspace',
  'projects',
  'shortcuts',
  'notes',
] as const;

export type SidebarModule = (typeof SIDEBAR_MODULES)[number];

export const SLOT_TYPES = ['terminal', 'browser', 'note'] as const;

export type SlotType = (typeof SLOT_TYPES)[number];

export interface WindowBounds {
  x?: number;
  y?: number;
  width: number;
  height: number;
}

export interface WorkspaceWindowState {
  bounds: WindowBounds;
  isMaximized: boolean;
  activeSidebarModule: SidebarModule;
}

export interface WorkspaceSlot {
  id: string;
  type: SlotType;
  title: string;
  description: string;
  status: 'placeholder';
  state: Record<string, string | null>;
}

export interface RecentProject {
  id: string;
  label: string;
  path: string;
}

export interface Shortcut {
  id: string;
  label: string;
  target: string;
  type: 'app' | 'path' | 'url';
}

export interface NoteEntry {
  id: string;
  title: string;
  content: string;
  updatedAt: string;
}

export interface WorkspaceState {
  version: 1;
  window: WorkspaceWindowState;
  slots: WorkspaceSlot[];
  recentProjects: RecentProject[];
  shortcuts: Shortcut[];
  notes: NoteEntry[];
}

const DEFAULT_WINDOW_BOUNDS: WindowBounds = {
  width: 1440,
  height: 900,
};

const DEFAULT_SLOTS: WorkspaceSlot[] = [
  {
    id: 'slot-terminal-1',
    type: 'terminal',
    title: 'Terminal placeholder',
    description: 'xterm.js + node-pty wiring lands in a later phase.',
    status: 'placeholder',
    state: {
      cwd: null,
    },
  },
  {
    id: 'slot-browser-1',
    type: 'browser',
    title: 'Browser placeholder',
    description: 'Future WebContentsView browser slots will attach here.',
    status: 'placeholder',
    state: {
      url: null,
    },
  },
  {
    id: 'slot-note-1',
    type: 'note',
    title: 'Notes placeholder',
    description: 'Local note storage is reserved for a later phase.',
    status: 'placeholder',
    state: {
      content: null,
    },
  },
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isSlotType(value: unknown): value is SlotType {
  return SLOT_TYPES.includes(value as SlotType);
}

function toStringOrNull(value: unknown) {
  return typeof value === 'string' ? value : null;
}

function sanitizeSlot(slot: unknown, fallback: WorkspaceSlot): WorkspaceSlot {
  if (!isRecord(slot)) {
    return fallback;
  }

  const state = isRecord(slot.state) ? slot.state : {};
  const nextState: Record<string, string | null> = {};
  for (const [key, value] of Object.entries(state)) {
    nextState[key] = toStringOrNull(value);
  }

  return {
    id: typeof slot.id === 'string' ? slot.id : fallback.id,
    type: isSlotType(slot.type) ? slot.type : fallback.type,
    title: typeof slot.title === 'string' ? slot.title : fallback.title,
    description:
      typeof slot.description === 'string'
        ? slot.description
        : fallback.description,
    status: 'placeholder',
    state: Object.keys(nextState).length > 0 ? nextState : fallback.state,
  };
}

export function isSidebarModule(value: unknown): value is SidebarModule {
  return SIDEBAR_MODULES.includes(value as SidebarModule);
}

export function sanitizeWindowBounds(value: unknown): WindowBounds {
  if (!isRecord(value)) {
    return { ...DEFAULT_WINDOW_BOUNDS };
  }

  const nextBounds: WindowBounds = {
    width:
      isFiniteNumber(value.width) && value.width >= MIN_WINDOW_WIDTH
        ? value.width
        : DEFAULT_WINDOW_BOUNDS.width,
    height:
      isFiniteNumber(value.height) && value.height >= MIN_WINDOW_HEIGHT
        ? value.height
        : DEFAULT_WINDOW_BOUNDS.height,
  };

  if (isFiniteNumber(value.x)) {
    nextBounds.x = value.x;
  }

  if (isFiniteNumber(value.y)) {
    nextBounds.y = value.y;
  }

  return nextBounds;
}

export function createDefaultWorkspaceState(): WorkspaceState {
  return {
    version: 1,
    window: {
      bounds: { ...DEFAULT_WINDOW_BOUNDS },
      isMaximized: false,
      activeSidebarModule: 'workspace',
    },
    slots: DEFAULT_SLOTS.map((slot) => ({
      ...slot,
      state: { ...slot.state },
    })),
    recentProjects: [],
    shortcuts: [],
    notes: [],
  };
}

export function hydrateWorkspaceState(value: unknown): WorkspaceState {
  const defaults = createDefaultWorkspaceState();
  if (!isRecord(value)) {
    return defaults;
  }

  const windowState = isRecord(value.window) ? value.window : {};
  const slots = Array.isArray(value.slots) ? value.slots : defaults.slots;

  return {
    version: 1,
    window: {
      bounds: sanitizeWindowBounds(windowState.bounds),
      isMaximized:
        typeof windowState.isMaximized === 'boolean'
          ? windowState.isMaximized
          : defaults.window.isMaximized,
      activeSidebarModule: isSidebarModule(windowState.activeSidebarModule)
        ? windowState.activeSidebarModule
        : defaults.window.activeSidebarModule,
    },
    slots: slots.map((slot, index) =>
      sanitizeSlot(slot, defaults.slots[index] ?? defaults.slots[0]),
    ),
    recentProjects: Array.isArray(value.recentProjects)
      ? (value.recentProjects as RecentProject[])
      : defaults.recentProjects,
    shortcuts: Array.isArray(value.shortcuts)
      ? (value.shortcuts as Shortcut[])
      : defaults.shortcuts,
    notes: Array.isArray(value.notes)
      ? (value.notes as NoteEntry[])
      : defaults.notes,
  };
}
