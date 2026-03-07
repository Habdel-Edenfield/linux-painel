# Handoff - Reset do Repositorio e Decisao de Plataforma

Data: 2026-03-07

## Estado local do repositorio

- Clone de trabalho: `/home/habdel/projects/linux-painel`
- Branch local `master`: snapshot GTK3/Terminal Multi-Pane publicado a partir de `Downloads/widgets-backup-20260306/widgets-backup`
- Branch local `archive/pre-reset-20260307`: preserva o antigo `origin/master`
- Branch local `investigation/workspace-architecture-20260307`: auditoria, ADR e roadmap da proxima geracao

## Estado das branches locais

- `master` contem a substituicao do antigo repositorio pelo snapshot GTK3 do Terminal Multi-Pane.
- `investigation/workspace-architecture-20260307` contem a auditoria, o ADR, o roteiro de migracao e este handoff.
- `archive/pre-reset-20260307` preserva a arvore antiga do remoto para comparacao ou recuperacao.

## Achados que nao podem ser perdidos

1. A extensao GNOME instalada resolve e executa `~/.local/share/terminal-multi-pane/terminal-multi-pane.py`.
2. A extensao instalada bate com o snapshot versionado, mas o app GTK instalado nao bate com o snapshot; existe drift de runtime.
3. A captura do problema de maximizacao corresponde a copia instalada, que ainda usa `set_decorated(False)` e margens fixas de `24px`.
4. O snapshot versionado ja contem tentativa de zerar margens em estado maximizado, mas isso ainda nao invalida a auditoria porque nao e a copia instalada no desktop.
5. `maximize` e `fullscreen` sao fluxos diferentes e devem continuar sendo tratados como coisas distintas.

## Decisao arquitetural fechada

- Recomendacao principal: `Electron + React + BaseWindow + WebContentsView + xterm.js + node-pty`
- Plano B nativo Linux: `GTK4/libadwaita + VTE + WebKitGTK`
- Opcao comparada mas nao recomendada como default: `Qt 6 + QWebEngine + QTermWidget`
- Nao recomendar evoluir o GTK3 atual como base principal de longo prazo

Detalhes:

- Auditoria: `docs/audit/current-state-2026-03-07.md`
- ADR: `docs/adr/ADR-0001-workspace-platform.md`
- Roteiro: `docs/roadmap/workspace-migration.md`

## Forma do produto-alvo

- Janela normal e maximizavel, com comportamento nativo
- Sidebar ou trilho para modulos
- Area central com slots horizontais rolaveis
- Persistencia e restauracao de workspace
- Reabertura rapida de projetos frequentes
- Fechamento de um slot sem destruir o restante do workspace
- Continuidade de uso em Ubuntu/GNOME

## Proximo passo recomendado para o executor

1. Criar `feat/electron-workspace-foundation` a partir de `investigation/workspace-architecture-20260307`.
2. Iniciar a nova implementacao em `apps/workspace-electron/`.
3. Manter o prototipo GTK3 congelado como referencia.
4. Entregar primeiro a fundacao do shell Electron, depois slots horizontais, terminais, modulos laterais e browser embutido.

## Publicacao no GitHub

- `archive/pre-reset-20260307` foi publicada no remoto para preservar a arvore anterior.
- `master` foi atualizada para o snapshot GTK3 do Terminal Multi-Pane.
- `investigation/workspace-architecture-20260307` foi publicada com a auditoria, o ADR, o roteiro de migracao e este handoff.
