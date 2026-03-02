# 🚀 Guia de Uso - Ralph Loop Contínuo

## ✅ Status do Sistema

O sistema Ralph Loop está **RODANDO E FUNCIONANDO**!

| Componente | Status | Detalhes |
|-----------|--------|-----------|
| Service systemd | ✅ Ativo | ralph-loop.service (PID: 130330) |
| Wrapper script | ✅ Rodando | Monitorando a cada 60s |
| Widgets | ✅ Operacionais | brightness e obsidian rodando |
| Trigger system | ✅ Funcionando | Comandos sendo processados |

## 🎯 Como Usar

### Enviar Triggers (Principal forma de uso)

```bash
# Ajustar brilho
/home/user/agent/lib/ralph-trigger.sh brightness.set --brightness 0.8 --gamma 0.8:0.8:0.8

# Abrir vault Obsidian
/home/user/agent/lib/ralph-trigger.sh obsidian.open --vault /home/user/Micologia

# Reiniciar todos os widgets
/home/user/agent/lib/ralph-trigger.sh widgets.restart

# Executar tarefa Ralph
/home/user/agent/lib/ralph-trigger.sh ralph.run --prompt "Sua tarefa aqui"
```

### Comando de Ajuda

```bash
/home/user/agent/lib/ralph-trigger.sh help
```

### Verificar Status

```bash
# Ver status do serviço
systemctl --user status ralph-loop.service

# Ver logs em tempo real
journalctl --user -u ralph-loop -f

# Ver logs recentes
journalctl --user -u ralph-loop -n 50
```

## 🔧 Comandos do Sistema

| Comando | Ação |
|----------|--------|
| `systemctl --user start ralph-loop.service` | Iniciar serviço |
| `systemctl --user stop ralph-loop.service` | Parar serviço |
| `systemctl --user restart ralph-loop.service` | Reiniciar serviço |
| `systemctl --user enable ralph-loop.service` | Habilitar no boot |
| `systemctl --user disable ralph-loop.service` | Desabilitar no boot |

## 📊 O Que O Loop Faz

O wrapper script roda continuamente e:

1. **Monitora widgets** a cada 60 segundos
   - Verifica se brightness-widget.py está rodando
   - Verifica se obsidian-widget.py está rodando
   - Reinicia automaticamente se algum widget cair

2. **Processa triggers** do arquivo `/tmp/ralph-trigger.json`
   - brightness.set: Ajusta brilho e gamma
   - obsidian.open: Abre vault específico
   - widgets.restart: Reinicia todos os widgets
   - ralph.run: Executa tarefa com Ralph

3. **Registra tudo no log** systemd
   - Ações executadas
   - Warnings e erros
   - Timestamps de cada operação

## 🧪 Exemplos Práticos

### Criar atalhos no .zshrc

```bash
# Adicionar ao ~/.zshrc
alias ralph-brightness='~/.config/systemd/user/ralph-trigger.sh brightness.set'
alias ralph-obsidian='~/.config/systemd/user/ralph-trigger.sh obsidian.open'
alias ralph-restart='~/.config/systemd/user/ralph-trigger.sh widgets.restart'
alias ralph-status='systemctl --user status ralph-loop.service'
alias ralph-logs='journalctl --user -u ralph-loop -f'
```

### Scripts de Atalho

Criar `/home/user/agent/scripts/` com scripts rápidos:

```bash
#!/bin/bash
# /home/user/agent/scripts/modo-noturno.sh
# Mudar para modo noturno
/home/user/agent/lib/ralph-trigger.sh brightness.set --brightness 0.7 --gamma 0.9:0.9:1.0

#!/bin/bash
# /home/user/agent/scripts/modo-dia.sh
# Mudar para modo dia
/home/user/agent/lib/ralph-trigger.sh brightness.set --brightness 1.0 --gamma 1.0:1.0:1.0
```

## 🔍 Troubleshooting

### Serviço não está rodando

```bash
# Verificar status
systemctl --user status ralph-loop.service

# Reiniciar
systemctl --user restart ralph-loop.service

# Ver logs para erros
journalctl --user -u ralph-loop -n 100
```

### Triggers não são processados

```bash
# Verificar se arquivo de trigger existe
ls -la /tmp/ralph-trigger.json

# Verificar conteúdo
cat /tmp/ralph-trigger.json

# Remover trigger manualmente
rm /tmp/ralph-trigger.json
```

### Widgets não funcionam

```bash
# Verificar se estão rodando
ps aux | grep widget

# Ver logs dos widgets
cat ~/.config/brightness-widget.log
# Obsidian não tem log, verificar via journalctl

# Reiniciar via trigger
/home/user/agent/lib/ralph-trigger.sh widgets.restart
```

## 📚 Documentação Adicional

- [START_HERE.md](./START_HERE.md) - Guia rápido inicial
- [README.md](./README.md) - Documentação completa do workspace
- [specs/PRD-001](./specs/PRD-001-workspace-setup.md) - Setup do workspace
- [specs/PRD-002](./specs/PRD-002-continuous-loop.md) - Especificação do loop

## 🎉 Pronto para Uso!

O sistema está configurado e rodando. Você pode:
1. Enviar triggers via `/home/user/agent/lib/ralph-trigger.sh`
2. Monitorar via `journalctl --user -u ralph-loop -f`
3. Usar widgets normalmente (brightness, obsidian, foldermenu)

O loop se encarrega de manter tudo funcionando automaticamente! 🚀
