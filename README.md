# Ralph Agent Workspace

## 🚀 Como Começar

**Leia [START_HERE.md](./START_HERE.md) para instruções completas de uso.**

> ⚠️ **IMPORTANTE**: Ralph requer execução de **fora** de uma sessão do Claude Code.

## Purpose

Workspace especializado para orquestração de ferramentas do sistema usando Ralph Orchestrator.

Este workspace permite que agentes operem ferramentas do sistema (brightness-widget, obsidian-widget, foldermenu) seguindo os princípios do Ralph:

1. **Fresh Context** - Cada iteração começa do zero
2. **Backpressure** - Portas de qualidade em vez de passos prescritos
3. **Disposable Plans** - Planos são baratos de regenerar
4. **Disk State** - Estado persiste em `.ralph/`
5. **Signal Steering** - Adicionar sinais após falhas
6. **Let Ralph Ralph** - Autonomia sem microgerenciamento

## Quick Start

```bash
# Initialize Ralph (already configured)
cd /home/user/agent

# Run with simple task
ralph run -p "Check status of all system widgets" --max-iterations 5

# Run with PRD
ralph run -P PROMPT.md
```

## Widgets Orchestrated

| Widget | Type | Location | Status |
|--------|------|----------|--------|
| brightness-widget.py | Python GTK | `~/.local/bin/` | Independent |
| obsidian-widget.py | Python GTK | `~/.local/bin/` | Independent |
| foldermenu@user.local | GNOME Extension | `~/.local/share/gnome-shell/extensions/` | Independent |

## Ralph Hats

- **system-coordinator**: Orquestra tarefas e coordena especialistas
- **widget-manager**: Gerencia ciclo de vida dos widgets
- **brightness-specialist**: Controla brilho/gamma
- **obsidian-specialist**: Gerencia vaults Obsidian

## Directory Structure

```
/home/user/agent/
├── ralph.yml              # Ralph configuration
├── PROMPT.md              # Initial task prompt
├── specs/                 # PRDs
│   └── PRD-001-workspace-setup.md
├── skills/                # Custom skills
│   ├── system-widget-manager.md
│   ├── brightness-control.md
│   ├── obsidian-manager.md
│   └── gnome-extension-control.md
└── lib/                   # Utility scripts
```

## State Persistence

- Scratchpad: `.ralph/agent/scratchpad.md`
- Memories: `.ralph/agent/memories.md`
- Tasks: `.ralph/agent/tasks.jsonl`
- Loops: `.ralph/loops.json`
