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

## 🎨 Vitals Design Reference

Este workspace usa **Vitals GNOME Shell Extension** como referência de design para desenvolvimento de widgets.

### Por que Vitals?

Vitals é um exemplo excelente de extensão GNOME Shell bem implementada:
- ✅ **Arquitetura nativa** - PanelMenu.Button, não AppIndicator
- ✅ **CSS minimalista** - Estilização consistente e eficiente
- ✅ **Ícones symbolic** - SVG 16px com suporte a temas
- ✅ **Async polling** - Updates não-bloqueantes
- ✅ **GSettings** - Configuração persistente padrão GNOME

### Documentação

- **[VITALS-DESIGN-REFERENCE.md](./specs/VITALS-DESIGN-REFERENCE.md)** - Documentação completa da arquitetura Vitals
- **[skills/vitals-reference.md](./skills/vitals-reference.md)** - Skill de referência para Ralph agents
- **[PRD-003-vitals-integration.md](./specs/PRD-003-vitals-integration.md)** - Roadmap de integração Vitals

### Status da Integração

| Phase | Status | Description |
|-------|--------|-------------|
| Documentation | ✅ Completo | Referências e skills criadas |
| Extension Base | ⏳ Pendente | Estrutura base da extensão |
| Brightness Module | ⏳ Pendente | Módulo de brilho GNOME Shell |
| Obsidian Module | ⏳ Pendente | Módulo Obsidian GNOME Shell |
| Preferences | ⏳ Pendente | Dialog de configurações |
| Ralph Integration | ✅ Completo | Hats e events adicionados |

**Fonte Vitals:** `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com/`

## Widgets Orchestrated

| Widget | Type | Location | Status |
|--------|------|----------|--------|
| brightness-widget.py | Python GTK | `~/.local/bin/` | Legacy (será migrado) |
| obsidian-widget.py | Python GTK | `~/.local/bin/` | Legacy (será migrado) |
| foldermenu@user.local | GNOME Extension | `~/.local/share/gnome-shell/extensions/` | ✅ OK |
| system-tools@user.local | GNOME Extension | `/home/user/agent/extensions/` | ⏳ Planejado |

## Ralph Hats

- **system-coordinator**: Orquestra tarefas e coordena especialistas
- **widget-manager**: Gerencia ciclo de vida dos widgets
- **brightness-specialist**: Controla brilho/gamma
- **obsidian-specialist**: Gerencia vaults Obsidian
- **design-coordinator**: Valida design contra padrões Vitals
- **gnome-dev-specialist**: Desenvolve extensões GNOME Shell

## Directory Structure

```
/home/user/agent/
├── ralph.yml              # Ralph configuration (hats, events, skills)
├── PROMPT.md              # Initial task prompt
├── specs/                 # PRDs e documentação
│   ├── PRD-001-workspace-setup.md
│   ├── PRD-002-continuous-loop.md
│   ├── PRD-003-vitals-integration.md
│   └── VITALS-DESIGN-REFERENCE.md  # Referência completa Vitals
├── skills/                # Custom skills
│   ├── system-widget-manager.md
│   ├── brightness-control.md
│   ├── obsidian-manager.md
│   ├── gnome-extension-control.md
│   └── vitals-reference.md  # Skill de referência Vitals
├── lib/                   # Utility scripts
│   ├── ralph-loop-wrapper.sh  # Loop contínuo
│   ├── ralph-trigger.sh       # Envio de comandos
│   └── test-system.sh         # Test suite
└── extensions/            # Novas extensões GNOME (planejado)
    └── system-tools@user.local/  # Unified extension
```

## State Persistence

- Scratchpad: `.ralph/agent/scratchpad.md`
- Memories: `.ralph/agent/memories.md`
- Tasks: `.ralph/agent/tasks.jsonl`
- Loops: `.ralph/loops.json`
