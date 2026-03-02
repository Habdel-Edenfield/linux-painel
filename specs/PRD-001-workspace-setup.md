# PRD-001: Ralph Agent Workspace Setup

## Objective
Estabelecer o workspace `/home/user/agent` com Ralph Orchestrator configurado para orquestração de ferramentas do sistema.

## Success Criteria
- [x] Diretório `/home/user/agent` criado com estrutura completa
- [x] `ralph.yml` configurado com backend Claude e hats definidos
- [x] Skills customizadas criadas em `skills/` e descobertas por Ralph
- [ ] Loop do Ralph pode ser iniciado com `ralph run -P PROMPT.md` *(requer execução fora de sessão Claude Code)*
- [ ] Agente pode executar comandos de sistema (ps, pgrep, subprocess)
- [ ] Estado persiste em `.ralph/` entre execuções

## Status: Setup Completo ✅

O workspace foi criado e configurado com sucesso. **IMPORTANTE**: Para usar o Ralph, você precisa executá-lo de fora de uma sessão do Claude Code, pois o Claude Code não suporta sessões aninhadas.

## Components
1. ✅ **Workspace Structure** - Criar árvore de diretórios
2. ✅ **Ralph Config** - Configurar hats, events, skills
3. ✅ **Skills Definition** - Criar skills para operações do sistema
4. ✅ **PRD Template** - Template para futuras PRDs
5. ✅ **Git Initialization** - Configurar versionamento

## Como Usar o Workspace

### Do Terminal (Fora do Claude Code)

```bash
# Navegar para o workspace
cd /home/user/agent

# Verificar skills disponíveis
ralph tools skill list

# Executar tarefa simples
ralph run -p "Check status of all system widgets" --max-iterations 5

# Executar tarefa usando PROMPT.md
ralph run -P PROMPT.md

# Verificar estado persistido
cat .ralph/agent/memories.md
cat .ralph/agent/tasks.jsonl
```

### Exemplos de Tarefas

```bash
# Verificar status dos widgets
ralph run -p "Check the status of brightness-widget.py and obsidian-widget.py using ps and grep"

# Orquestrar mudança de brilho
ralph run -p "Set monitor brightness to comfort mode (80%) and gamma to 0.8:0.8:0.8"

# Abrir vault Obsidian
ralph run -p "Open the Micologia vault in Obsidian using the obsidian:// protocol"
```

## Estrutura do Workspace

```
/home/user/agent/
├── ralph.yml              # Configuração Ralph (hats, events, skills)
├── PROMPT.md              # Prompt inicial para workspace
├── README.md              # Documentação
├── .gitignore             # Ignorar arquivos de estado
│
├── .ralph/               # Estado gerenciado pelo Ralph
│   ├── agent/            # Memória do agente
│   │   ├── scratchpad.md
│   │   ├── memories.md
│   │   └── tasks.jsonl
│   └── events-*.jsonl   # Histórico de eventos
│
├── specs/                # PRDs
│   └── PRD-001-workspace-setup.md
│
├── skills/               # Skills customizadas
│   ├── system-widget-manager.md
│   ├── brightness-control.md
│   ├── obsidian-manager.md
│   └── gnome-extension-control.md
│
└── lib/                 # Scripts utilitários (vazio)
```

## Dependencies
- ✅ Ralph CLI v2.6.0 (já instalado em `~/.npm-global/bin/ralph`)
- ✅ Python 3 com subprocess module
- ✅ GNOME Shell 46
- ✅ xrandr (para brightness widget)

## Notes
- Widgets permanecem independentes (não foram integrados)
- Estética: dark moderno (a ser aplicado em refatoração futura)
- Princípios Ralph: fresh context, backpressure, signal-based steering
- **Importante**: Ralph requer execução de fora de sessão Claude Code

## Próximos Passos (Future Work)

1. **Testar o Ralph fora do Claude Code** - Executar comandos do terminal
2. **Criar mais skills** - Adicionar skills para automação avançada
3. **Refatorar widgets** - Aplicar estética dark moderna unificada
4. **Criar painel de controle unificado** (opcional)
5. **Adicionar automatização de perfis baseados em horário**
