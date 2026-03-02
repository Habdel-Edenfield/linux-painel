# PRD-002: Ralph Continuous Loop Setup

## Objective
Estabelecer o Ralph em loop contínuo para orquestração autônoma de ferramentas do sistema.

## Success Criteria
- [ ] Ralph loop pode ser iniciado e manter execução em background
- [ ] Loop processa eventos periodicamente (ou sob demanda)
- [ ] Hats coordenam tarefas autonomamente
- [ ] Estado persiste corretamente entre iterações
- [ ] Loop pode ser controlado (start/stop/restart)

## Approach: Continuous Loop com Systemd

O Ralph não foi projetado para rodar continuamente como daemon, mas podemos criar um wrapper que:

1. **Monitora eventos do sistema** - Arquivos de configuração mudam? Widget status muda?
2. **Dispara Ralph quando necessário** - Executa `ralph run` para processar eventos
3. **Loop de polling** - Verifica estado periodicamente e orquestra ações

### Alternativa: Loop Autônomo com Eventos

Usar Ralph em modo autônomo com um PROMPT.md que descreve o loop:

```markdown
# Continuous Orchestration Loop

## Purpose
Orquestrar automaticamente operações de ferramentas do sistema baseado em eventos.

## Event Loop
1. Monitorar estado dos widgets (brightness, obsidian, foldermenu)
2. Aguardar eventos (config changes, user requests, scheduled actions)
3. Processar evento usando hats apropriados
4. Publicar resultado e voltar ao passo 1

## Events to Monitor
- Config file changes in ~/.config/brightness-widget/
- Config file changes in ~/.config/obsidian/
- User requests via trigger files (/tmp/ralph-trigger.json)
- Time-based events (e.g., switch to dark mode after 20:00)

## Loop Behavior
- Use `ralph tools task` para track work items
- Use `ralph tools memory` para armazenar discoveries
- Publique `LOOP_COMPLETE` para marcar fim do ciclo e reiniciar
```

## Implementation Plan

### Phase 1: Test Validation
```bash
# Teste simples para validar Ralph funciona
cd /home/user/agent
ralph run -p "Test: Check status of brightness-widget using ps and grep" --max-iterations 3
```

### Phase 2: Event Trigger System
Criar um sistema de trigger baseado em arquivos:
- `/tmp/ralph-trigger.json` - Arquivo de trigger para solicitações do usuário
- Quando modificado, Ralph processa a requisição
- Estrutura do arquivo:
  ```json
  {
    "action": "brightness.set",
    "params": {"brightness": 0.8, "gamma": "0.8:0.8:0.8"},
    "timestamp": "2026-03-02T22:30:00Z"
  }
  ```

### Phase 3: Wrapper Script
Criar script wrapper que roda Ralph continuamente:
```bash
#!/bin/bash
# /home/user/agent/lib/ralph-loop-wrapper.sh

TRIGGER_FILE="/tmp/ralph-trigger.json"
WORKSPACE="/home/user/agent"

while true; do
    # Check for trigger
    if [ -f "$TRIGGER_FILE" ]; then
        echo "Processing trigger at $(date)"
        cd "$WORKSPACE"
        ralph run -P PROMPT.md --max-iterations 10
        rm "$TRIGGER_FILE"
    fi

    # Monitor widgets (polling every 60s)
    # Check if widgets are running, restart if needed
    # Check config file changes

    sleep 60
done
```

### Phase 4: Systemd Service (Opcional)
Para verdadeiro loop contínuo em background:
```ini
# /etc/systemd/user/ralph-loop.service
[Unit]
Description=Ralph Continuous Loop
After=network.target

[Service]
Type=simple
ExecStart=/home/user/agent/lib/ralph-loop-wrapper.sh
Restart=always
RestartSec=10
WorkingDirectory=/home/user/agent

[Install]
WantedBy=default.target
```

## Dependencies
- Ralph CLI v2.6.0 ✅
- Workspace configurado ✅
- Python 3.12.3 ✅
- Bash shell ✅

## Notes
- Widgets permanecem independentes (não serão integrados)
- Loop não interfere com operação manual dos widgets
- Trigger system permite intervenção manual quando necessário
- Estado persiste em `.ralph/` entre ciclos do loop
