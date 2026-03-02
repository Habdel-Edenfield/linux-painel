# Como Usar o Workspace Ralph

## 🚀 Início Rápido

O workspace `/home/user/agent` está configurado e pronto para uso com Ralph Orchestrator.

**⚠️ IMPORTANTE**: Ralph requer execução de **fora** de uma sessão do Claude Code. O Claude Code não suporta sessões aninhadas.

## 📋 Pré-requisitos

- Ralph CLI v2.6.0 (já instalado)
- Widgets do sistema rodando (brightness-widget, obsidian-widget, foldermenu)
- Acesso ao terminal fora de Claude Code

## 🎯 Comandos Principais

```bash
# Navegar para o workspace
cd /home/user/agent

# Listar skills disponíveis
ralph tools skill list

# Executar tarefa com prompt inline
ralph run -p "Sua tarefa aqui" --max-iterations 10

# Executar tarefa usando arquivo PROMPT.md
ralph run -P PROMPT.md

# Verificar estado persistido após execução
cat .ralph/agent/memories.md
cat .ralph/agent/tasks.jsonl
```

## 📝 Exemplos de Tarefas

```bash
# Verificar status dos widgets
ralph run -p "Check the status of brightness-widget.py and obsidian-widget.py using ps and grep"

# Ajustar brilho para modo conforto
ralph run -p "Set monitor brightness to comfort mode (80%) using brightness-control skill"

# Abrir vault Obsidian
ralph run -p "Open the Micologia vault in Obsidian using obsidian-manager skill"

# Orquestrar múltiplas operações
ralph run -p "Orchestrate: Set brightness to dark mode (70%) and open personal vault in Obsidian"
```

## 🎩 Hats Disponíveis

- **system-coordinator**: Orquestra tarefas e coordena especialistas
- **widget-manager**: Gerencia ciclo de vida dos widgets
- **brightness-specialist**: Controla brilho/gamma
- **obsidian-specialist**: Gerencia vaults Obsidian

## 🛠️ Skills Disponíveis

| Skill | Descrição |
|--------|------------|
| system-widget-manager | Gerenciamento de widgets (iniciar/parar/status) |
| brightness-control | Controle de brilho via xrandr e perfis |
| obsidian-manager | Gerenciamento de vaults Obsidian |
| gnome-extension-control | Controle de extensões GNOME |

## 📁 Estrutura de Diretórios

```
/home/user/agent/
├── ralph.yml              # Configuração Ralph
├── PROMPT.md              # Prompt inicial do workspace
├── START_HERE.md          # Este arquivo
├── README.md              # Documentação completa
├── specs/                # PRDs
│   └── PRD-001-workspace-setup.md
├── skills/               # Skills customizadas
└── .ralph/               # Estado gerenciado pelo Ralph
    ├── agent/            # Memória do agente
    └── events-*.jsonl   # Histórico de eventos
```

## 🔧 Troubleshooting

### Ralph não responde
- Verifique se está executando de fora de uma sessão Claude Code
- Verifique se `ralph` está no PATH: `which ralph`
- Verifique se os widgets estão rodando: `ps aux | grep widget`

### Skills não encontradas
- Verifique o diretório de skills: `ls -la skills/`
- Verifique a configuração Ralph: `cat ralph.yml | grep skills`
- Liste skills disponíveis: `ralph tools skill list`

### Widgets não respondem
- Verifique se o widget está rodando: `ps aux | grep brightness-widget`
- Verifique o log do widget: `cat ~/.config/brightness-widget/state`
- Reinicie o widget: `pkill -f brightness-widget.py && python3 ~/.local/bin/brightness-widget.py &`

## 📚 Documentação Adicional

- [Ralph Orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)
- [Six Tenets of Ralph](https://deepwiki.com/wiki/mikeyobrien/ralph-orchestrator#3.2)
- [README.md](./README.md) - Documentação completa do workspace
- [PRD-001](./specs/PRD-001-workspace-setup.md) - Detalhes do setup

## 💡 Dicas

1. **Comece pequeno** - Teste com tarefas simples antes de operações complexas
2. **Use verbose** - Adicione `-v` para ver mais detalhes: `ralph run -v -p "..."`
3. **Verifique estado** - Após cada execução, verifique `.ralph/agent/memories.md`
4. **Limpe histórico** - Para começar fresco: `rm -rf .ralph/`
