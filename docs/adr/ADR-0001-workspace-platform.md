# ADR-0001 - Plataforma da Proxima Geracao do Workspace

Status: Aceito

Data: 2026-03-07

## Contexto

O Terminal Multi-Pane deixou de ser apenas um widget com dois ou tres terminais. O produto-alvo agora e um workspace de desenvolvimento Linux-first, com:

- janela principal persistente e maximizavel, sem fullscreen obrigatorio;
- sidebar ou trilho para modulos;
- area central com slots horizontais rolaveis;
- multiplos terminais;
- browser embutido lado a lado;
- historico de projetos frequentes;
- atalhos e favoritos;
- notas;
- fechamento isolado de slots sem destruir o restante do workspace.

A auditoria de 2026-03-07 mostrou que a base atual em GTK3/VTE continua boa como prototipo, mas ja sofre com decoracao manual de janela, layout horizontal rigido e alto custo de evolucao para modulos heterogeneos.

## Decisao

Adotar `Electron + React + BaseWindow + WebContentsView + xterm.js + node-pty` como arquitetura principal da proxima geracao do produto.

### Forma fechada da arquitetura

- Janela principal: `BaseWindow`.
- Shell de interface: um `WebContentsView` principal carregando a aplicacao React.
- Slots de browser embutido: `WebContentsView` dedicados por slot, gerenciados no processo principal e acoplados ao layout por bounds sincronizados.
- Slots de terminal: componentes React com `xterm.js` no renderer, conectados por IPC a um servico de PTY no processo principal baseado em `node-pty`.
- Persistencia: um `workspace.json` em `app.getPath('userData')`, contendo estado da janela, slots, modulos, projetos recentes, atalhos e notas.
- Regra de embedding: nao usar `BrowserView`, que ja esta deprecated; nao usar `<webview>` como base da arquitetura preferencial.

## Comparacao das opcoes

Escala: `1` = fraco para o produto-alvo, `5` = forte para o produto-alvo.

| Criterio | Opcao A - Electron + React + WebContentsView + xterm.js + node-pty | Opcao B - GTK4/libadwaita + VTE + WebKitGTK | Opcao C - Qt 6 + QWebEngine + QTermWidget |
| --- | --- | --- | --- |
| Facilidade para terminais multiplos | `5` - `xterm.js` + `node-pty` e combinacao madura para multiplexar sessoes | `4` - VTE e forte para terminal nativo | `4` - QTermWidget e embeddable e maduro |
| Browser embutido lado a lado | `5` - `WebContentsView` foi feito para hospedar `WebContents` | `3` - possivel com WebKitGTK, mas exige mais acoplamento manual | `4` - `QWebEngineView` e maduro para browser embutido |
| Slots horizontais ilimitados com rolagem lateral | `5` - layout web e o caminho de menor atrito | `3` - possivel, mas o custo de composicao custom cresce | `4` - Qt lida melhor com area dividida que GTK3, mas ainda exige UI custom |
| Persistencia de workspace | `5` - estado JSON simples e natural | `4` - factivel, mas mais manual | `4` - factivel, mas mais manual |
| Historico de repositorios, atalhos e notas | `5` - modelagem de modulos e listas em React e direta | `3` - viavel, mas aumenta a superficie de UI nativa | `4` - viavel, com mais custo de widgets e integracao |
| Integracao com Linux/GNOME | `3` - suficiente, mas nao nativa | `5` - melhor encaixe visual e comportamental | `3` - boa no desktop, mas menos alinhada ao GNOME |
| Complexidade de manutencao futura | `4` - stack rica, com ecossistema amplo e iteration speed alta | `3` - forte, mas com maior atrito para UI rica e embedding | `2` - mais pesada para o alvo GNOME-first pessoal |
| Risco tecnico | `4` - risco controlado se o ciclo de vida de `WebContents` for bem tratado | `3` - risco medio pelo acoplamento entre VTE, WebKitGTK e layout custom | `2` - risco maior de empacotamento, integracao e custo operacional |
| Qualidade de UX para usuario nao tecnico | `5` - mais liberdade para lapidar navegacao, onboarding e densidade visual | `3` - boa UX nativa, mas menor elasticidade para um workspace rico | `4` - boa UX possivel, com custo maior |

## Justificativa da decisao

### Por que Electron e a recomendacao principal

- O produto-alvo pede layout rico, heterogeneo e expansivel, mais proximo de um workspace/IDE leve do que de um terminal nativo simples.
- `BaseWindow` permite controlar a janela e usar `contentView.addChildView(...)` para views filhas.
- `WebContentsView` e a API atual para exibir `WebContents`, enquanto `BrowserView` ja foi marcado como deprecated desde Electron 30.
- `xterm.js` e um frontend de terminal para browser e Electron; `node-pty` fornece o backend de pseudo-terminal no host.
- O shell React resolve melhor sidebar, slots horizontais, historico, favoritos, notas e outras superfices de produtividade do que uma continuidade em GTK3.

### Custos aceitos da decisao

- O runtime sera mais pesado do que GTK4/VTE puro.
- Empacotamento e distribuicao vao depender do toolchain Electron.
- O processo principal precisa fechar explicitamente `webContents` de views removidas para evitar vazamento de memoria.

Esses custos sao aceitaveis para um produto pessoal, Linux-first, cujo foco principal e velocidade de evolucao e UX mais rica.

## Plano B fechado

Se a prioridade absoluta mudar para `app Linux nativo enxuto`, com menor consumo e sem ambicao forte de browser embutido e layout web-like complexo, usar `GTK4/libadwaita + VTE + WebKitGTK`.

### Forma do plano B

- Janela nativa com decoracao do sistema e maximizacao padrao.
- VTE para terminais.
- WebKitGTK apenas para slots de browser realmente necessarios.
- Sidebar e slots horizontais implementados em GTK4, sem reaproveitar a janela customizada do GTK3 atual.

Este plano B continua valido como alternativa nativa, mas nao e a recomendacao default para o produto descrito.

## Opcao nao recomendada

Nao continuar expandindo a base atual em `GTK3 + VTE + janela customizada sem decoracao` como solucao principal de longo prazo.

Motivos:

- o problema atual de maximizacao ja mostrou fragilidade na camada de janela;
- o layout continua muito amarrado a composicao manual;
- browser, notas, historico e modulos heterogeneos aumentariam rapidamente o custo da manutencao;
- o ganho de aproveitar o prototipo nao compensa o custo de estender a base para o produto-alvo.

## Referencias oficiais e primarias

- Electron BaseWindow: <https://www.electronjs.org/docs/latest/api/base-window>
- Electron WebContentsView: <https://www.electronjs.org/docs/latest/api/web-contents-view>
- Electron Web Embeds: <https://www.electronjs.org/pt/docs/latest/tutorial/web-embeds>
- Electron migration from BrowserView to WebContentsView: <https://www.electronjs.org/blog/migrate-to-webcontentsview>
- xterm.js: <https://github.com/xtermjs/xterm.js>
- node-pty: <https://github.com/microsoft/node-pty>
- VTE docs: <https://gnome.pages.gitlab.gnome.org/vte/>
- VTE GTK4 Terminal reference: <https://gnome.pages.gitlab.gnome.org/vte/gtk4/class.Terminal.html>
- WebKitGTK stable references: <https://webkitgtk.org/reference/webkitgtk/stable/>
- WebKitGTK migration to GTK 4: <https://webkitgtk.org/reference/webkitgtk/stable/migrating-to-webkitgtk-6.0.html>
- Qt QWebEngineView: <https://doc.qt.io/qtforpython-6.5/PySide6/QtWebEngineWidgets/QWebEngineView.html>
- QTermWidget: <https://github.com/lxqt/qtermwidget>
