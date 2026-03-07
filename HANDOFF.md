# Handoff — Terminal Multi-Pane / GNOME Desktop

Data: 2026-03-07

## Onde começamos

- O projeto tinha um protótipo de Terminal Multi-Pane quebrado para GNOME Shell 46.
- O pedido inicial foi transformar isso em um launcher minimalista no topo do GNOME, com modal multi-pane funcional e estética bem contida.
- Em um ponto intermediário, o Terminal Multi-Pane acabou substituindo o UUID do `Vitals@CoreCoding.com`, o que gerou conflito com o widget original do Vitals e depois uma regressão no desktop/dock.

## Onde paramos

- O modal GTK/VTE está funcional e minimalista.
- O layout inicial agora é: esquerda vazia, centro com 1 terminal, direita vazia.
- A faixa superior do modal foi separada da faixa dos painéis.
- O shell visual está quadrado, sem bordas arredondadas.
- A janela do Terminal Multi-Pane foi convertida para comportamento de janela normal:
  - sem `keep_above`
  - sem `skip_taskbar`
  - sem `skip_pager`
  - tipo `NORMAL`
  - header customizado arrastável
- O instalador foi corrigido para:
  - parsear `gsettings` no formato `@as []`
  - instalar o Terminal Multi-Pane no UUID próprio `terminal-multi-pane@habdel.local`
  - restaurar o Vitals original a partir de `terminal-vitals/`
  - habilitar os dois na sessão GNOME
- O Ubuntu Dock apresentou regressão de runtime e foi recarregado; o usuário confirmou que o comportamento do clique voltou ao normal.

## Arquivos principais alterados

- `terminal-multi-pane-scripts/terminal-multi-pane.py`
- `terminal-multi-pane-scripts/install-user.sh`
- `terminal-multi-pane-extension/extension.js`
- `terminal-multi-pane-extension/icons/terminal-multi-pane-symbolic.svg`
- `HANDOFF.md` (este arquivo)

## Estado instalado no sistema

- App GTK/VTE:
  - `~/.local/share/terminal-multi-pane/terminal-multi-pane.py`
- Launcher:
  - `~/.local/bin/terminal-multi-pane`
- Extensão do Terminal Multi-Pane:
  - `~/.local/share/gnome-shell/extensions/terminal-multi-pane@habdel.local`
- Vitals restaurado:
  - `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com`
- Snapshot local do Vitals usado para restauração:
  - `terminal-vitals/`

## Comandos úteis

Validar código:

```bash
cd /home/habdel/Downloads/widgets-backup-20260306/widgets-backup
python3 -m py_compile terminal-multi-pane-scripts/terminal-multi-pane.py
bash -n terminal-multi-pane-scripts/install-user.sh
```

Reinstalar app + extensões:

```bash
cd /home/habdel/Downloads/widgets-backup-20260306/widgets-backup
bash terminal-multi-pane-scripts/install-user.sh
```

Conferir extensões habilitadas:

```bash
gsettings get org.gnome.shell enabled-extensions
gnome-extensions list --enabled
gnome-extensions info Vitals@CoreCoding.com
gnome-extensions info terminal-multi-pane@habdel.local
```

Se o GNOME Shell continuar segurando metadados antigos em memória:

```bash
Alt+F2
r
```

ou logout/login.

## Pendências reais para o próximo agente

1. Verificar visualmente, em uma sessão GNOME limpa, se o Vitals aparece separado do Terminal Multi-Pane na barra superior.
2. Validar manualmente se minimizar/maximizar do Terminal Multi-Pane ficou correto no uso real, não só na configuração da janela.
3. Se o Shell ainda mostrar metadata stale para `Vitals@CoreCoding.com`, fazer um refresh manual do Shell e revalidar os dois widgets no topo.

## Observação importante

- Durante esta sessão, o DBus/live registry do GNOME Shell às vezes continuou mostrando metadata antiga em memória para o UUID do Vitals, mesmo com os arquivos restaurados no disco.
- Isso é cache de runtime do GNOME Shell, não estado final dos arquivos instalados.
