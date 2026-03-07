# Auditoria do Estado Atual do Terminal Multi-Pane

Data: 2026-03-07

## Escopo e fontes

- Fonte canônica do repositório nesta data: `terminal-multi-pane-scripts/terminal-multi-pane.py`, `terminal-multi-pane-extension/extension.js` e `HANDOFF.md`.
- Runtime realmente executado pelo GNOME: `~/.local/share/terminal-multi-pane/terminal-multi-pane.py`.
- Extensão instalada no GNOME: `~/.local/share/gnome-shell/extensions/terminal-multi-pane@habdel.local/extension.js`.
- Captura analisada: `~/Imagens/Capturas de tela/Captura de tela de 2026-03-07 15-36-25.png`.
- Handoff anterior: `HANDOFF.md`.

## Sumario executivo

1. O problema de "maximizar sem ocupar a area util" e real e tem explicacao de implementacao, nao apenas de uso.
2. A captura bate com a copia instalada em `~/.local/share/terminal-multi-pane/terminal-multi-pane.py`, nao com o snapshot agora versionado no repositório.
3. Existe drift entre a fonte canônica local e o runtime em producao: o script GTK/VTE instalado diverge do script que foi publicado como base do repositório; a extensao GNOME instalada, por outro lado, bate com o snapshot.
4. A arquitetura atual em GTK3/VTE continua boa como prototipo de launcher com terminais, mas e fraca como base principal para um workspace maior com browser embutido, notas, historico rico, atalhos e navegacao horizontal ampla.

## Evidencias do runtime em producao

### O que a extensao realmente executa

- `terminal-multi-pane-extension/extension.js:14` define `DEFAULT_APP_PATH` como `~/.local/share/terminal-multi-pane/terminal-multi-pane.py`.
- `terminal-multi-pane-extension/extension.js:98-120` resolve o caminho do app e executa `python3 <appPath> <command>`.
- `gsettings get org.gnome.shell enabled-extensions` em 2026-03-07 inclui `terminal-multi-pane@habdel.local`.

### Drift entre snapshot e copia instalada

| Artefato | Hash SHA-256 | Leitura |
| --- | --- | --- |
| `terminal-multi-pane-scripts/terminal-multi-pane.py` | `17e3aa2e9920cfd83db19c75f7b7465a8fa10631b39a0172a25f695f99b0d97e` | Fonte canônica do repositório |
| `~/.local/share/terminal-multi-pane/terminal-multi-pane.py` | `071da8c74c776a8efd2abce6cbb4d4cdbc82f1d3b15a87477409462bdc9babdb` | Runtime em producao; diverge do snapshot |
| `terminal-multi-pane-extension/extension.js` | `5c5cc2f0a2c91303b5b93ce9cfcaed6abe506cf3de5918b0d99e5e2b540844e2` | Igual ao instalado |
| `~/.local/share/gnome-shell/extensions/terminal-multi-pane@habdel.local/extension.js` | `5c5cc2f0a2c91303b5b93ce9cfcaed6abe506cf3de5918b0d99e5e2b540844e2` | Igual ao snapshot |

- O diff entre o snapshot e o runtime instalado mostra 1 arquivo alterado, com 8 insercoes e 31 remocoes.
- O runtime instalado ainda esta na variante com margens fixas no frame externo.
- O snapshot ja contem uma tentativa de ajuste dinamico de margens via `_update_frame_margins()`.

## Confirmacao da causa do bug de expansao

### Evidencia na copia instalada

- `~/.local/share/terminal-multi-pane/terminal-multi-pane.py:1242` usa `self.set_decorated(False)`.
- `~/.local/share/terminal-multi-pane/terminal-multi-pane.py:1272-1277` aplica `24px` fixos de margem ao frame externo.
- `~/.local/share/terminal-multi-pane/terminal-multi-pane.py:1370-1373` alterna apenas `maximize()` e `unmaximize()`.
- `~/.local/share/terminal-multi-pane/terminal-multi-pane.py:1450-1457` usa `F11` para `fullscreen()` e `unfullscreen()`.

### Leitura tecnica

- A janela e uma janela sem decoracao do sistema, com shell visual proprio.
- O frame externo com margens fixas cria uma "moldura interna" permanente.
- Quando a janela entra em estado maximizado, o container da aplicacao continua respeitando esse recuo interno.
- Isso explica por que a captura mostra a janela maximizada, mas sem ocupar toda a area util aparente.

### Distincao que precisa permanecer explicita

- `Maximizar janela` significa pedir ao window manager para expandir a janela normal.
- `Fullscreen` significa entrar em modo tela cheia, removendo a moldura da janela e ocupando a tela inteira.
- O bug auditado aqui e de maximizacao de janela normal, nao de fullscreen.

### O que mudou no snapshot versionado

- `terminal-multi-pane-scripts/terminal-multi-pane.py:1243` ainda usa `self.set_decorated(False)`.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:1273-1276` passa a guardar o frame em `self._frame`.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:1374-1380` define margem `0` quando `_is_maximized` e verdadeiro.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:1464-1470` reaplica margens e regiao de input no `window-state-event`.

- Conclusao operacional: a base versionada atual ja tentou corrigir a folga visual, mas a copia instalada que a extensao dispara ainda e a versao anterior com margens fixas. A captura analisada continua sendo evidencia valida do bug porque bate com o runtime instalado.

## Auditoria da limitacao estrutural

### Como a base atual esta organizada

- `terminal-multi-pane-scripts/terminal-multi-pane.py:445` define `TerminalWidget` como unidade principal de funcionalidade.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:683` define `WidgetColumn` como coluna vertical de widgets.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:711-720` usa `Gtk.ScrolledWindow` vertical para empilhar widgets dentro da coluna.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:1100` define `DynamicLayoutManager` como orchestrador do layout.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:1145-1147` e `1167-1170` empacotam colunas diretamente em um `Gtk.Box` horizontal.
- `terminal-multi-pane-scripts/terminal-multi-pane.py:1314-1317` usa `main_box.set_homogeneous(True)`, o que favorece colunas de largura igual e reduz elasticidade para um workspace horizontal mais rico.

### O que a base atual faz bem

- Lanca e persiste multiplos terminais VTE.
- Permite drag and drop entre colunas.
- Persiste tamanho da janela, estado maximizado e `working_dir`.
- Funciona como launcher leve integrado ao GNOME Shell.

### Onde a base atual fica estruturalmente fraca para o produto-alvo

- O registro de widgets continua praticamente centrado em terminal; o produto descrito pede browser, notas, historico e atalhos como modulos de primeira classe.
- A janela depende de decoracao manual, titlebar customizada e tratamento proprio de maximizacao, o que aumenta o custo de manutencao.
- O layout horizontal amplo com slots dinamicos e rolaveis fica preso a composicao manual de GTK3.
- Embutir browser rico ao lado de terminais aumenta muito a complexidade de foco, resize, input, persistencia e ciclo de vida nessa base.
- O custo para transformar este prototipo GTK3 em workspace completo seria maior do que reiniciar em uma stack mais adequada ao produto descrito.

## Implicacoes para a proxima fase

1. O GTK3 atual deve ser tratado como prototipo validado, nao como base principal de longo prazo.
2. A proxima geracao deve partir de uma arquitetura pensada para layout rico, modulos heterogeneos e persistencia de workspace.
3. O estado instalado no desktop precisa ser sempre distinguido da fonte versionada no GitHub, porque hoje eles nao sao a mesma coisa.
