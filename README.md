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
| Extension Base | ✅ Completo | Estrutura base da extensão |
| Brightness Module | ⚠️ Removido (causava crashes) | Módulo de brilho GNOME Shell foi removido por causar crashes |
| Obsidian Module | ⏳ Pendente | Módulo Obsidian GNOME Shell |
| Preferences | ⏳ Pendente | Dialog de configurações |
| Recovery | ✅ Completo | Plano de recuperação executado com sucesso |
| Ralph Integration | ✅ Completo | Hats e events adicionados |

**⚠️ IMPORTANTE:** Veja [RECOVERY-SUMMARY.md](./RECOVERY-SUMMARY.md) para detalhes completos sobre o que aconteceu e como proceder.

**Fonte Vitals:** `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com/`

## Widgets Orchestrated

| Widget | Type | Location | Status |
|--------|------|----------|--------|
| brightness-widget.py | Python GTK | `~/.local/bin/` | ❌ Removido (substituído por system-tools) |
| obsidian-widget.py | Python GTK | `~/.local/bin/` | ❌ Removido (substituído por system-tools) |
| foldermenu@user.local | GNOME Extension | `~/.local/share/gnome-shell/extensions/` | ❌ Removido (não era mais necessário) |
| Vitals@CoreCoding.com | GNOME Extension | `~/.local/share/gnome-shell/extensions/` | ✅ **ACTIVE** e funcionando |
| system-tools@user.local | GNOME Extension | `~/.local/share/gnome-shell/extensions/` | ❌ Removido (causava crashes) |

**✅ Situação Atual:**
- Vitals: **ACTIVE e funcionando perfeitamente** (restaurado com sucesso)
- system-tools: **REMOVIDA** (causava crashes do GNOME Shell)
- foldermenu: **REMOVIDA** (não era mais necessária)
- Widgets Python: **REMOVIDOS** (foram substituídos pela extensão planejada)

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
├── README.md               # Este arquivo
├── START_HERE.md           # Quick start guide
├── RECOVERY-SUMMARY.md     # Documentação completa da recuperação
├── INSTRUCTION-FOR-NEXT-AGENT.md  # Instruções para próximo Ralph Loop
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
└── extensions/            # Novas extensões GNOME
    └── system-tools@user.local/  # REMOVIDA (causava crashes)
```

## State Persistence

- Scratchpad: `.ralph/agent/scratchpad.md`
- Memories: `.ralph/agent/memories.md`
- Tasks: `.ralph/agent/tasks.json`
- Loops: `.ralph/loops.json`

## 📊 Status do Projeto

### O Que Foi Concluído

✅ **Recovery Complete:**
- Vitals extension restaurada e funcionando
- Extensões de usuário reabilitadas
- GSchema instalado globalmente
- Extensões problemáticas removidas

✅ **Documentação Completa:**
- RECOVERY-SUMMARY.md - Análise completa do problema e soluções
- INSTRUCTION-FOR-NEXT-AGENT.md - Instruções detalhadas para re-implementação

### O Que Falta Implementar

⏳ **System-Tools Extension (Re-implementação):**

Deve ser implementada usando **abordagem incremental** para evitar crashes:

**FASE 1: Extensão Mínima** (30 minutos)
- Apenas emoji 🔆 no panel
- NENHUMA funcionalidade
- Testar extensivamente

**FASE 2: Menu Simples** (20 minutos)
- Menu básico com itens que apenas logam
- NENHUM xrandr, NENHUM GSettings

**FASE 3: GSettings Integration** (20 minutos)
- Usar extensionObject.getSettings() COM try/catch
- Implementar fallbacks

**FASE 4: Brightness Module** (30 minutos)
- Criar módulo isolado
- Testar xrandr manualmente primeiro

**FASE 5: Integration Completa** (30 minutos)
- Conectar tudo
- Profiles de brilho
- Hot sensor

⏳ **Obsidian Module:**
- Gerenciamento de vaults Obsidian
- Scan de diretórios
- Integração com menu

⏳ **Preferences Dialog:**
- prefs.js e prefs.ui
- Interface gráfica para configurações

## 🎯 Instruções para Próximo Agente

Veja [INSTRUCTION-FOR-NEXT-AGENT.md](./INSTRUCTION-FOR-NEXT-AGENT.md) para instruções detalhadas sobre como:

1. Implementar system-tools extension sem causar crashes
2. Usar abordagem incremental (uma fase por vez)
3. Proteger Vitals para quebrar nunca
4. Testar cada fase extensivamente
5. Tratar todos os erros adequadamente

## 🚨 Avisos Importantes

1. **Vitals é CRÍTICA** - Nunca quebre a extensão Vitals
2. **Abordagem INCREMENTAL é obrigatória** - Implementar uma fase por vez
3. **TRATAMENTO de erros é essencial** - Use try/catch em tudo
4. **TESTE extensivamente** - Não prossiga sem testar
5. **LEIA a RECOVERY-SUMMARY** - Entenda o que aconteceu antes

## 📞 Recursos de Suporte

- [RECOVERY-SUMMARY.md](./RECOVERY-SUMMARY.md) - Documentação completa da recuperação
- [INSTRUCTION-FOR-NEXT-AGENT.md](./INSTRUCTION-FOR-NEXT-AGENT.md) - Instruções para re-implementação
- [VITALS-DESIGN-REFERENCE.md](./specs/VITALS-DESIGN-REFERENCE.md) - Referência de design

## 📊 Resumo Final

**Estado Atual do Sistema:**
- ✅ Vitals@CoreCoding.com: ACTIVE e funcionando
- ❌ system-tools: REMOVIDA (causava crashes)
- ✅ Extensões de usuário: Habilitadas
- ✅ GSchema: Instalado e disponível

**Próximos Passos:**
1. Implementar system-tools extension usando abordagem incremental
2. Testar cada fase extensivamente
3. Nunca quebrar Vitals
4. Documentar cada fase

---

**Última Atualização:** 2 de Março de 2026
**Status:** Recovery Completo, Pronto para Re-implementação Incremental
