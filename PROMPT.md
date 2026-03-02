# Ralph Agent Workspace - System Tool Orchestration

## Context
Este workspace está configurado para orquestração de ferramentas do sistema usando Ralph Orchestrator.

### Orquestração de Ferramentas
- **brightness-widget.py** - Controla brilho e gamma do monitor
- **obsidian-widget.py** - Acesso rápido a vaults Obsidian
- **foldermenu@user.local** - Extensão GNOME para navegação de pastas

### Princípios do Ralph
1. Fresh Context - Cada iteração começa do zero
2. Backpressure - Use validações e tests em vez de passos prescritos
3. Disposable Plans - Planos podem ser regenerados a qualquer momento
4. Disk State - Estado persiste em `.ralph/`
5. Signal Steering - Adicione sinais após falhas
6. Let Ralph Ralph - Trabalhe autonomamente

## Available Hats
- **system-coordinator**: Orquestra tarefas e coordena especialistas
- **widget-manager**: Gerencia ciclo de vida dos widgets
- **brightness-specialist**: Controla brilho/gamma
- **obsidian-specialist**: Gerencia vaults Obsidian

## Available Skills
- system-widget-manager.md - Gerenciamento de widgets
- brightness-control.md - Controle de brilho via xrandr
- obsidian-manager.md - Gerenciamento de vaults Obsidian
- gnome-extension-control.md - Controle de extensões GNOME

## Task Instructions

Quando receber uma tarefa de orquestração de sistema:

1. **Analyze the request** - Determine quais widgets/ferramentas são envolvidas
2. **Load appropriate skills** - Use `ralph tools skill load <name>` para carregar skills necessárias
3. **Execute operations** - Use subprocess e comandos shell para operar as ferramentas
4. **Validate results** - Verifique que as operações foram executadas com sucesso
5. **Report completion** - Publique `TASK_COMPLETE` com evidências do que foi realizado

## Completion Criteria

Uma tarefa está completa quando:
- Todas as operações solicitadas foram executadas
- Os estados dos widgets refletem as mudanças solicitadas
- Evidências foram coletadas (logs, configs, status)
- O evento `TASK_COMPLETE` foi publicado com resumo

## Example Tasks

- "Check status of all system widgets and report their running state"
- "Orchestrate: Set brightness to comfort mode and open Micologia vault in Obsidian"
- "Restart the foldermenu GNOME extension"
