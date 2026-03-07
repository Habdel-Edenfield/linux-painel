# Fase 1 - Relatório de Refatoração
**Terminal Multi-Pane Widget**
**Data:** 2026-03-05

---

## 1. Objetivo da Sessão

Transformar a arquitetura engessada do Terminal Multi-Pane de uma estrutura hardcoded com 3 colunas fixas e delays arbitrários para uma arquitetura modular, orientada a configuração e escalável.

---

## 2. Status: ✅ CONCLUÍDO

---

## 3. Alterações Realizadas

### 3.1 Estrutura de Arquivos

```
terminal-multi-pane/
├── terminal-multi-pane.py          # Refatorado (novo)
├── terminal-multi-pane-original.py # Backup do código original
├── backups/
│   └── terminal-multi-pane-backup-20260305-0910SS.tar.gz
├── backup.sh                        # Script de backup automatizado
└── FASE1-RELATORIO.md              # Este documento
```

### 3.2 Classes Removidas/Refatoradas

| Antes | Depois | Mudança |
|-------|--------|---------|
| `TerminalWrapper` | `TerminalWidget` | Agora implementa interface `Widget` |
| `TerminalColumn` | `WidgetColumn` | Aceita qualquer tipo de widget, não só terminais |
| `TerminalMultiPaneWindow._build_ui()` | Usa `DynamicLayoutManager` | Layout orientado a dados, sem hardcodes |

### 3.3 Novas Classes Criadas

```python
# Interface abstrata para todos os widgets
class Widget(ABC):
    @abstractmethod
    def create_widget(self) -> Gtk.Widget
    @abstractmethod
    def get_state(self) -> dict
    @abstractmethod
    def restore_state(self, state: dict) -> None

# Factory para criação dinâmica
class WidgetFactory:
    _widget_types: Dict[str, type] = {'terminal': TerminalWidget, ...}

    @classmethod
    def create(cls, widget_type: str, widget_id: str, config: dict, column: WidgetColumn) -> Widget
    @classmethod
    def register(cls, widget_type: str, widget_class: type) -> None

# Gerenciador de layout orientado a dados
class DynamicLayoutManager:
    def load_layout(self, layout_config: dict) -> None
    def add_column(self, name: str) -> str
    def get_state(self) -> dict
```

---

## 4. Problemas Resolvidos

### 4.1 Hardcoded Columns ❌ → ✅

**Antes:**
```python
self.col1 = TerminalColumn("Painel 1")
self.col2 = TerminalColumn("Painel 2")
self.col3 = TerminalColumn("Painel 3")
main_box.pack_start(self.col1, True, True, 0)
main_box.pack_start(self.col2, True, True, 0)
main_box.pack_start(self.col3, True, True, 0)
```

**Depois:**
```python
DEFAULT_LAYOUT = {
    "columns": [
        {"id": "col-1", "name": "Painel 1", "widgets": ["term-1"]},
        {"id": "col-2", "name": "Painel 2", "widgets": ["term-2"]},
        {"id": "col-3", "name": "Painel 3", "widgets": ["term-3"]}
    ]
}
self.layout_manager.load_layout(DEFAULT_LAYOUT)
```

### 4.2 Delays Hardcoded ❌ → ✅

**Antes:**
```python
GLib.timeout_add(100, lambda: self.col1.add_terminal() and False)
GLib.timeout_add(200, lambda: self.col2.add_terminal() and False)
GLib.timeout_add(300, lambda: self.col3.add_terminal() and False)
```

**Depois:**
```python
def _start_terminal_async(self) -> None:
    """Inicialização assíncrona sem delays arbitrários."""
    GLib.idle_add(self._initialize_terminal)

def _initialize_terminal(self) -> bool:
    # ... criação do terminal
    return False  # Executa apenas uma vez (não reagenda)
```

### 4.3 Terminal Acoplado ❌ → ✅

**Antes:**
```python
class TerminalColumn:
    def add_terminal(self):
        wrapper = TerminalWrapper(self)  # VTE instanciado diretamente
```

**Depois:**
```python
class WidgetFactory:
    @classmethod
    def create(cls, widget_type: str, widget_id: str, config: dict, column: WidgetColumn):
        widget_class = cls._widget_types.get(widget_type)
        return widget_class(widget_id, config, column)

# Uso:
widget = WidgetFactory.create('terminal', 'term-1', config, column)
```

---

## 5. Funcionalidades Mantidas (Zero Regressão)

| Funcionalidade | Status |
|----------------|--------|
| Transparência RGBA visual | ✅ |
| AppIndicator na barra do sistema | ✅ |
| Drag & Drop entre colunas | ✅ |
| Menu de contexto (botão direito) | ✅ |
| Atalhos (Esc, F11, Ctrl+Shift+W) | ✅ |
| Estilos CSS | ✅ |
| Shell padrão (SHELL env) | ✅ |

---

## 6. Type Hints e Documentação

Todas as novas classes incluem:
- Type hints completos (`-> Gtk.Widget`, `widget_id: str`, etc.)
- Docstrings claras explicando propósito e parâmetros
- Comentários explicando decisões arquiteturais

---

## 7. Código de Exemplo: Adicionando Novo Widget

Para futura implementação de widgets não-terminais:

```python
# 1. Criar classe
class NotesWidget(Widget):
    def __init__(self, widget_id: str, config: Dict[str, Any], column: WidgetColumn):
        super().__init__(widget_id, config)
        self.column = column

    def create_widget(self) -> Gtk.Widget:
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # ... criar UI com Gtk.TextView
        return container

    def get_state(self) -> Dict[str, Any]:
        return {'content': self.text_buffer.get_text(...)}

    def restore_state(self, state: Dict[str, Any]) -> None:
        if 'content' in state:
            self.text_buffer.set_text(state['content'])

# 2. Registrar
WidgetFactory.register('notes', NotesWidget)

# 3. Usar
config = {"type": "notes", "content": "Minhas notas"}
column.add_widget('notes', config)
```

---

## 8. Linhas de Código

| Arquivo | Linhas |
|---------|--------|
| Original (`terminal-multi-pane-original.py`) | 572 |
| Refatorado (`terminal-multi-pane.py`) | 650 |

*Aumento justificado pela nova arquitetura modular com factory, interface abstrata e gerenciador de layout.*

---

## 9. Próximo Passo: Fase 2 - Persistência

**Objetivo:** Implementar salvamento e restauração do estado da aplicação.

---

## 10. Plano para Fase 2: Persistência

### 2.1 Objetivos

1. Criar `StateManager` para gerenciar persistência
2. Salvar estado em `~/.config/terminal-multi-pane/state.json`
3. Restaurar sessão automaticamente ao abrir
4. Implementar auto-save com debounce (não salvar a cada mudança)

### 2.2 Estado a Ser Persistido

```json
{
  "version": 1,
  "window": {
    "width": 1600,
    "height": 900,
    "is_maximized": true
  },
  "layout": {
    "columns": [
      {
        "id": "col-1",
        "name": "Painel 1",
        "widgets": ["term-1", "notes-1"]
      },
      {
        "id": "col-2",
        "name": "Painel 2",
        "widgets": ["term-2"]
      }
    ]
  },
  "widgets": {
    "term-1": {
      "type": "terminal",
      "title": "bash",
      "working_dir": "file:///home/user/projetos"
    },
    "notes-1": {
      "type": "notes",
      "content": "TODO:\n- Finalizar refatoração"
    },
    "term-2": {
      "type": "terminal",
      "title": "bash",
      "working_dir": "file:///home/user"
    }
  }
}
```

### 2.3 Classes a Implementar

```python
class StateManager:
    """Gerencia persistência com auto-save."""

    def __init__(self, state_file: Path)
    def load(self) -> dict
    def save(self, force: bool = False) -> None
    def set(self, path: str, value: Any) -> None  # Notação de ponto
    def get(self, path: str, default=None) -> Any
    def _schedule_auto_save(self) -> None  # Debounce 2s
```

### 2.4 Integração com Código Existente

1. **`TerminalMultiPaneApp.do_activate()`**
   - Carregar estado salvo
   - Passar para `TerminalMultiPaneWindow`

2. **`TerminalMultiPaneWindow.__init__()`**
   - Receber `StateManager`
   - Restaurar tamanho/maximized

3. **`TerminalWidget`**
   - Conectar ao sinal `cwd-changed` do VTE
   - Salvar working directory quando mudar

4. **`DynamicLayoutManager`**
   - Usar `get_state()` do layout para salvar
   - `load_layout()` com config restaurada

### 2.5 Auto-save Strategy

```python
# Debounce: salva apenas 2s após última mudança
def set(self, path: str, value: Any):
    # Atualiza estado
    self._dirty = True
    # Cancela timer anterior se existir
    if self._auto_save_timer:
        GLib.source_remove(self._auto_save_timer)
    # Agenda novo save
    self._auto_save_timer = GLib.timeout_add(2000, self._auto_save)
```

### 2.6 Triggers de Salvamento

| Evento | Ação |
|--------|------|
| Terminal muda diretório | `StateManager.set(f'widgets.{id}.working_dir', cwd)` |
| Widget adicionado/removido | Atualizar `layout.columns[].widgets` |
| Janela redimensionada | `StateManager.set('window.width', w)` |
| Aplicação fechar | `StateManager.save(force=True)` |

### 2.7 Ordem de Implementação

1. `StateManager` básico (load/save)
2. Integração com `TerminalMultiPaneWindow`
3. Integração com `DynamicLayoutManager`
4. Hook em `TerminalWidget` para cwd
5. Auto-save com debounce
6. Testes de restauração

---

## 11. Solicitação de Suporte ao Colaborador

### 11.1 Contexto para o Colaborador

O Terminal Multi-Pane foi refatorado de uma estrutura hardcoded para uma arquitetura modular usando Factory Pattern. A próxima fase é implementar persistência de estado.

### 11.2 Pontos para Investigação

1. **Comparação com Ferramentas Similares**
   - Como o Tilix, Terminator ou GNOME Terminal lidam com persistência?
   - Existe algum padrão de arquivo de configuração recomendado?

2. **GTK3 State Management**
   - Existe alguma biblioteca GTK específica para persistência?
   - `Gtk.Application` tem algum built-in para salvar/restaurar estado?

3. **Best Practices**
   - Debounce value: 2s é adequado ou deve ser configurável?
   - Deve salvar em formato JSON ou outro (TOML, YAML, XML)?

4. **Edge Cases**
   - O que fazer se o arquivo de estado estiver corrompido?
   - Como lidar com migração de versão quando mudar o formato?

### 11.3 Perguntas para Responder

1. A estrutura do JSON proposta acima parece adequada?
2. Há algum aspecto de persistência que está faltando?
3. Devo considerar compressão do estado se crescer muito?
4. Devemos implementar "snapshots" (múltiplos estados salvos) para rollback?

---

## 12. Resumo Executivo

**O que foi feito:**
- Refatoração completa para arquitetura modular (Factory Pattern)
- Eliminação de hardcodes e delays arbitrários
- Criação de interface abstrata `Widget` para extensibilidade
- Layout gerenciado via configuração (pronto para JSON)

**O que foi mantido:**
- Todas as funcionalidades visuais e funcionais originais
- Transparência, AppIndicator, Drag & Drop
- Estilos CSS idênticos

**Próximo passo:**
- Fase 2: Implementar persistência de estado com `StateManager`

**Status:** ✅ FASE 1 CONCLUÍDA | ⏳ AGUARDANDO DIREÇÕES PARA FASE 2

---

**Gerado por:** Claude Opus 4.6
**Para revisão do:** Operador Colaborador
