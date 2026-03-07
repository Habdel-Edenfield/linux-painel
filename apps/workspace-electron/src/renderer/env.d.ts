export {};

declare global {
  interface Window {
    workspaceApp: {
      version: string;
    };
  }
}
