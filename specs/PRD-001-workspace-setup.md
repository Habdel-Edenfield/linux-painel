# PRD-001: Ralph Agent Workspace Setup

## Objective
Estabelecer o workspace `/home/user/agent` com Ralph Orchestrator configurado para orquestração de ferramentas do sistema.

## Success Criteria
- [x] Diretório `/home/user/agent` criado com estrutura completa
- [x] `ralph.yml` configurado com backend Claude e hats definidos
- [ ] Skills customizadas criadas em `skills/` e descobertas por Ralph
- [ ] Loop do Ralph pode ser iniciado com `ralph run -P PROMPT.md`
- [ ] Agente pode executar comandos de sistema (ps, pgrep, subprocess)
- [ ] Estado persiste em `.ralph/` entre execuções

## Components
1. **Workspace Structure** - Criar árvore de diretórios
2. **Ralph Config** - Configurar hats, events, skills
3. **Skills Definition** - Criar skills para operações do sistema
4. **PRD Template** - Template para futuras PRDs
5. **Git Initialization** - Configurar versionamento

## Dependencies
- Ralph CLI v2.6.0 (já instalado)
- Python 3 com subprocess module
- GNOME Shell 46
- xrandr (para brightness widget)

## Notes
- Widgets permanecem independentes (não serão integrados)
- Estética: dark moderno (a ser aplicado em refatoração futura)
- Princípios Ralph: fresh context, backpressure, signal-based steering
