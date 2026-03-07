# Roteiro de Migracao para o Workspace de Desenvolvimento

Data: 2026-03-07

## Objetivo fechado

Transformar o prototipo atual em um workspace de desenvolvimento Linux-first com:

- janela normal, maximizavel e com comportamento nativo;
- sidebar ou trilho para modulos;
- area central com slots horizontais rolaveis;
- multiplos terminais;
- browser embutido lado a lado;
- historico de projetos frequentes;
- atalhos e favoritos;
- notas;
- persistencia e restauracao do workspace;
- fechamento isolado de slots sem destruir o restante da sessao.

## Estrategia de repositorio

- Manter o prototipo GTK3 atual como referencia historica, sem expandi-lo como produto principal.
- Preservar o estado remoto anterior em `archive/pre-reset-20260307`.
- Manter `master` como branch tronco do snapshot GTK3.
- Fazer a primeira execucao da nova geracao a partir de `investigation/workspace-architecture-20260307` enquanto o ADR e o roadmap ainda nao tiverem sido mesclados.
- Criar a implementacao nova em `apps/workspace-electron/`, sem reescrever o prototipo GTK3 durante a fase inicial.

## Forma do produto-alvo

### Layout principal

- Header nativo do sistema, sem titlebar manual.
- Coluna lateral fixa para navegacao entre modulos: `Workspace`, `Projetos`, `Atalhos`, `Notas`.
- Regiao central com uma faixa horizontal de slots.
- Cada slot e um modulo aberto no workspace e pode ser `terminal`, `browser` ou `note`.
- A faixa de slots precisa aceitar adicao, remocao e navegacao lateral sem destruir os demais slots.

### Persistencia

- Persistir em `app.getPath('userData')/workspace.json`.
- Modelo minimo de estado:

```json
{
  "window": {
    "bounds": {"width": 1600, "height": 900},
    "isMaximized": true,
    "activeSidebarModule": "workspace"
  },
  "slots": [
    {
      "id": "slot-1",
      "type": "terminal",
      "title": "backend",
      "state": {"cwd": "/home/habdel/projects/linux-painel"}
    },
    {
      "id": "slot-2",
      "type": "browser",
      "title": "Electron docs",
      "state": {"url": "https://www.electronjs.org/docs/latest/api/web-contents-view"}
    },
    {
      "id": "slot-3",
      "type": "note",
      "title": "Scratchpad",
      "state": {"content": "TODO"}
    }
  ],
  "recentProjects": [],
  "shortcuts": []
}
```

- Em v1, restaurar terminais pelo `cwd` salvo e pelo perfil do shell; nao tentar ressuscitar o processo shell anterior.

## Fases de execucao

### Fase 1 - Foundation do shell Electron

- Criar `apps/workspace-electron/` com Electron, React e preload.
- Implementar `BaseWindow` como janela principal.
- Carregar um `WebContentsView` raiz com a aplicacao React.
- Garantir maximizacao nativa, restauracao de bounds e comportamento correto em Ubuntu/GNOME.

### Fase 2 - Modelo de workspace e slots horizontais

- Implementar o store de `workspace.json`.
- Renderizar sidebar fixa e trilho central de slots horizontais rolaveis.
- Permitir adicionar, remover, ativar e reordenar slots.
- Garantir que fechar um slot remova apenas esse item do array `slots`.

### Fase 3 - Terminais do workspace

- Implementar um `PTYService` no processo principal com `node-pty`.
- Expor IPC para criar, destruir, redimensionar e enviar input para sessoes de terminal.
- Implementar `TerminalSlot` no React com `xterm.js`, `@xterm/addon-fit` e `@xterm/addon-web-links`.
- Persistir `cwd`, titulo e metadados de cada terminal.

### Fase 4 - Projetos frequentes, atalhos e notas

- Implementar o modulo lateral `Projetos` com lista de repositorios frequentes e acao de reabrir.
- Implementar o modulo lateral `Atalhos` para apps e links frequentes.
- Implementar o modulo lateral `Notas` com notas leves persistidas localmente.
- Permitir abrir projetos, atalhos e notas sem quebrar o workspace atual.

### Fase 5 - Browser embutido

- Criar `BrowserSlotManager` no processo principal.
- Para cada slot de browser, criar um `WebContentsView` dedicado.
- Sincronizar bounds do slot via IPC a partir do layout React.
- Fechar explicitamente o `webContents` quando o slot for removido.
- Nao usar `BrowserView`.

### Fase 6 - Polimento Linux/GNOME

- Ajustar atalhos, foco, drag, resize e restauracao.
- Validar comportamento em janela normal, maximizada e com varios monitores.
- Empacotar em formato adequado para Ubuntu/GNOME depois que a UX principal estiver estavel.

## Criterios de aceite obrigatorios

1. A janela principal maximiza como janela nativa, sem moldura interna fixa de `24px`.
2. O usuario consegue adicionar e remover slots sem afetar os demais.
3. O usuario consegue navegar horizontalmente por uma quantidade arbitraria de slots.
4. O workspace reabre com a mesma configuracao basica de slots, projetos recentes, atalhos e notas.
5. Reabrir um projeto frequente exige no maximo um clique a partir do modulo `Projetos`.
6. O browser embutido convive lado a lado com os terminais.
7. O app continua utilizavel em Ubuntu/GNOME sem depender de fullscreen.

## Defaults escolhidos para o executor

- Branch inicial do executor: criar `feat/electron-workspace-foundation` a partir de `investigation/workspace-architecture-20260307`.
- Framework de UI: React.
- Tecnologia de terminal: `xterm.js` no renderer e `node-pty` no processo principal.
- Tecnologia de browser embutido: `WebContentsView`.
- Persistencia: JSON local em `userData`.
- O prototipo GTK3 fica congelado como referencia, nao como alvo de extensao.
