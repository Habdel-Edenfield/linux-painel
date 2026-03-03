# PRD-004: System Tools Reimplementation - Abordagem Incremental

## Objective

Reimplementar extensão `system-tools@user.local` seguindo abordagem incremental rigorosa para evitar crashes e garantir funcionalidade gradual.

## Background

### Problema Anterior

A extensão system-tools criada no PRD-003 causava crashes do GNOME Shell:
- Toda vez que era habilitada, aparecia mensagem "Oh não! Algo deu errado"
- Forçava reinício do computador
- Vitals extensão parava de funcionar
- Extensão foi removida

### Causa Raiz

1. **Implementação complexa de uma vez** - Todos os recursos carregados simultaneamente
2. **Falta de tratamento de erros** - Sem try/catch em operações críticas
3. **Conexões de sinais prematuras** - GObject signals conectados antes de inicialização completa
4. **Nenhum teste de iteração** - Fases completas sem verificação real

## Success Criteria

- [ ] FASE 1: Extensão mínima carrega sem crashes
- [ ] FASE 2: Menu simples funciona sem crashes
- [ ] FASE 3: GSettings integra com tratamento de erros
- [ ] FASE 4: Brightness module funciona isoladamente
- [ ] FASE 5: Integração completa funciona
- [ ] Vitals@CoreCoding.com permanece ACTIVE todo o tempo
- [ ] NENHUM crash de GNOME Shell durante desenvolvimento
- [ ] Documentação atualizada após cada fase

## Approach - Cinco Fases Obrigatórias

### FASE 1: Extensão Mínima (30 minutos)

**Objetivo:** Extensão que carrega sem crashes

**Requisitos:**
1. Criar apenas emoji 🔆 em St.Label no panel
2. NENHUMA funcionalidade além de mostrar ícone
3. NENHUM código de settings ou xrandr
4. Apenas testar carregamento e exibição

**Arquivos:**
- `extension.js` - Classe mínima com apenas St.Label
- `metadata.json` - Metadados básicos
- `stylesheet.css` - CSS mínimo ou vazio

**Test Checklist:**
- [ ] `gnome-extensions enable system-tools@user.local` não causa erro
- [ ] `gnome-extensions info system-tools@user.local` mostra "Estado: ACTIVE"
- [ ] Emoji 🔆 aparece no panel do GNOME
- [ ] NENHUM crash após 5 minutos de uso
- [ ] Vitals@CoreCoding.com permanece ACTIVE
- [ ] `journalctl -u gnome-shell` não mostra erros

**O QUE NÃO fazer:**
- ❌ NÃO usar extensionObject.getSettings()
- ❌ NÃO implementar PopupMenu
- ❌ NÃO usar xrandr ou comandos de sistema

### FASE 2: Menu Simples (20 minutos)

**Objetivo:** PopupMenu que não causa crashes

**Requisitos:**
1. Adicionar PopupMenu básico ao botão
2. 2-3 itens de menu que apenas logam quando clicados
3. NENHUMA funcionalidade real
4. NENHUM xrandr, NENHUM GSettings

**Test Checklist:**
- [ ] Menu abre quando clica no ícone
- [ ] Menu fecha quando clica fora
- [ ] Clicar em itens do menu aparece no log
- [ ] NENHUM crash ao usar menu
- [ ] Vitals permanece ACTIVE

**O QUE NÃO fazer:**
- ❌ NÃO usar GSettings
- ❌ NÃO implementar funcionalidade real

### FASE 3: GSettings Integration (20 minutos)

**Objetivo:** Integração GSettings com tratamento de erros

**Requisitos:**
1. Importar Gio
2. Usar `extensionObject.getSettings()` COM try/catch
3. Logar todos os erros
4. Implementar fallback values

**Test Checklist:**
- [ ] Settings object carrega sem crashes
- [ ] Consegue ler valores de settings
- [ ] Fallback values funcionam quando settings falham
- [ ] NENHUM crash
- [ ] Vitals permanece ACTIVE

### FASE 4: Brightness Module Isolado (30 minutos)

**Objetivo:** Módulo de brilho que funciona sozinho

**Requisitos:**
1. Criar BrightnessModule separado
2. Testar xrandr commands MANUALMENTE primeiro
3. NÃO integrar com menu ainda

**Test Checklist:**
- [ ] BrightnessModule pode ser instanciado
- [ ] getCurrentBrightness() retorna valor válido
- [ ] setBrightness() REALMENTE muda brilho da tela
- [ ] Polling funciona sem crashes
- [ ] Module pode ser destruído limpassamente

**O QUE NÃO fazer:**
- ❌ NÃO integrar com menu
- ❌ NÃO conectar signals ao menu

### FASE 5: Integração Completa (30 minutos)

**Objetivo:** Conectar BrightnessModule ao menu com todos os recursos

**Requisitos:**
1. Integrar BrightnessModule ao menu
2. Mostrar valor atual de brilho
3. Implementar 3 profiles
4. Adicionar hot sensor para mostrar porcentagem

**Test Checklist:**
- [ ] Seção de brilho aparece no menu
- [ ] Brilho atual é mostrado corretamente
- [ ] Clicar em profile MUDA brilho da tela
- [ ] Hot sensor atualiza porcentagem
- [ ] Consegue toggle visibilidade do widget
- [ ] NENHUM crash
- [ ] Vitals permanece ACTIVE

## Testing Strategy

### Após Cada FASE:

1. **Habilitar extensão:** `gnome-extensions enable system-tools@user.local`
2. **Verificar status:** `gnome-extensions info system-tools@user.local`
3. **Esperar estabilidade:** 5 minutos sem crashes
4. **Testar funcionalidade:** Todos os recursos da fase
5. **Verificar logs:** `journalctl -u gnome-shell --since "5 minutos atrás"`
6. **Verificar Vitals:** Confirmar que permanece ACTIVE
7. **SÓ prosseguir se TODOS os testes passarem**

### Smoke Tests Antes de Prosseguir:

```bash
# 1. Verificar se extensão carrega sem erros
gnome-extensions info system-tools@user.local

# 2. Verificar se não há crashes recentes
journalctl -u gnome-shell --since "10 minutos atrás" | grep -i "error\|critical"

# 3. Verificar se Vitals está ativo
gnome-extensions info Vitals@CoreCoding.com

# 4. Verificar se brilho realmente muda
xrandr --verbose | grep brightness
```

## Failure Recovery

### Se GNOME Shell Crashar:

1. **Parar imediatamente:** Pressionar Alt+F2, digitar `r` para reiniciar
2. **Desabilitar extensão:** `gnome-extensions disable system-tools@user.local`
3. **Analisar logs:** `journalctl -u gnome-shell | grep -A 30 "crash\|error"`
4. **Identificar causa exata:** Linha específica causando o crash
5. **Corrigir completamente:** Não prosseguir sem corrigir
6. **Testar extensivamente:** Antes de reabilitar

### Se Vitals Parar de Funcionar:

1. **PARAR trabalho:** Suspender imediatamente
2. **Reabilitar Vitals:** `gnome-extensions enable Vitals@CoreCoding.com`
3. **Reiniciar GNOME Shell:** `killall -SIGUSR1 gnome-shell`
4. **Verificar estabilidade:** Confirmar Vitals está ativa
5. **Só retomar:** Após Vitals estar estável por 5 minutos

## Documentation After Each Phase

Após completar cada fase, criar:

1. `/home/user/agent/PHASE-{N}-COMPLETED.md` com:
   - O que foi implementado
   - Código criado/modificado
   - Testes realizados
   - Problemas e soluções

2. Atualizar `/home/user/agent/README.md` com:
   - Status atual do projeto
   - Fases completas
   - Fases pendentes

3. Atualizar `/home/user/agent/.ralph/agent/memories.md` com:
   - Lições aprendidas
   - Padrões de código
   - Soluções para problemas

4. Atualizar `/home/user/agent/.ralph/agent/tasks.jsonl` com:
   - Marcar tarefas completas
   - Adicionar próximas tarefas

## MCP DeepWiki Integration

### Quando usar:

Use o MCP deepwiki para buscar informações sobre Ralph Orchestrator quando:

1. **Precisar entender comportamento padrão** de configurações
2. **Duvidar sobre como funciona** memories/tasks/handoff
3. **Precisar de referência** sobre hats/events/skills
4. **Encontrar erro ou comportamento inesperado** do Ralph

### Comando:

```
mcp__deepwiki__ask_question
  repoName: "mikeyobrien/ralph-orchestrator"
  question: "Sua pergunta específica aqui"
```

### Exemplos de perguntas úteis:

- "Como o Ralph lida com memórias entre loops?"
- "Qual o formato exato de tasks.jsonl?"
- "Como funciona o sistema de handoff entre sessões?"
- "Quais são os eventos disponíveis no ralph.yml?"
- "Como configurar memories.inject corretamente?"

## Success Metrics

### Quantitativos:
- Extensão carrega sem erros em < 100ms
- Menu abre com refresh instantâneo (< 50ms)
- Zero erros em journalctl após 24h
- Todas as 5 fases completas e testadas

### Qualitativos:
- Vitals permanece ACTIVE durante todo desenvolvimento
- Nenhum crash de GNOME Shell ocorre
- Cada fase é validada antes de prosseguir
- Documentação reflete estado real do sistema

---

**Created:** 2026-03-03
**Status:** READY FOR IMPLEMENTATION
**Fase Atual:** FASE 1 - Extensão Mínima (✅ COMPLETA)
**Próxima Fase:** FASE 2 - Menu Simples
