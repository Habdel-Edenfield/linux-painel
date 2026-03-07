#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal Multi-Pane Manager - Fase 1: Refatoração Modular
Arquitetura baseada em Factory Pattern + Layout Orientado a Dados
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, Vte, GLib, Gdk, Gio, Pango
import sys
import os
import signal
import json
import copy
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
import logging
import uuid
import cairo

try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3
except (ImportError, ValueError):
    AyatanaAppIndicator3 = None

# Detectar shell padrão
SHELL = os.environ.get('SHELL', '/bin/bash')
APPLICATION_ID = 'com.habdel.TerminalMultiPane'
APPLICATION_TITLE = 'Terminal Multi-Pane'
DEFAULT_WORKING_DIR = str(Path.home())


def _path_from_vte_uri(uri: Optional[str]) -> Optional[str]:
    """Converte `file://` do VTE para caminho de filesystem."""
    if not uri:
        return None

    if uri.startswith('file://'):
        try:
            path, _ = GLib.filename_from_uri(uri)
            return path
        except GLib.Error:
            return None

    return uri


def _normalize_working_dir(value: Optional[str]) -> Optional[str]:
    """Aceita URI ou caminho simples e retorna um diretório local válido."""
    path = _path_from_vte_uri(value)
    if not path:
        return None

    expanded = os.path.expanduser(path)
    return expanded if os.path.isdir(expanded) else None


# ============================================================================
# STATE MANAGER: Persistência de Estado
# ============================================================================

class StateManager:
    """
    Gerencia persistência de estado com auto-save e fallback graceful.

    Responsável por salvar/carregar estado da aplicação em JSON
    com debounce para evitar travamentos na UI.
    """

    STATE_VERSION = 1
    DEFAULT_STATE_FILE = Path.home() / ".config" / "terminal-multi-pane" / "state.json"
    DEBOUNCE_MS = 2000

    def __init__(self, state_file: Path = None):
        """
        Inicializa o gerenciador de estado.

        Args:
            state_file: Caminho para o arquivo de estado (opcional)
        """
        self.state_file = state_file or self.DEFAULT_STATE_FILE
        self.state: Dict[str, Any] = {}
        self._dirty = False
        self._auto_save_timer: Optional[int] = None
        self._logger = logging.getLogger(__name__)

        # Garantir diretório existe
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Carregar estado salvo
        self._load()

    def _get_default_state(self) -> Dict[str, Any]:
        """Retorna o estado padrão quando não há estado salvo."""
        return {
            'version': self.STATE_VERSION,
            'window': {
                'width': 1600,
                'height': 900,
                'is_maximized': True
            },
            'layout': copy.deepcopy(DEFAULT_LAYOUT)
        }

    def _load(self) -> None:
        """
        Carrega estado do arquivo JSON.

        Se o arquivo não existir ou estiver corrompido,
        usa o estado padrão sem quebrar a aplicação.
        """
        if not self.state_file.exists():
            self.state = self._get_default_state()
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)

            # Validação básica de versão
            if loaded.get('version') != self.STATE_VERSION:
                self._logger.warning(
                    f"Versão de estado incompatível: {loaded.get('version')}. "
                    "Usando estado padrão."
                )
                self.state = self._get_default_state()
                return

            self.state = loaded
            self._logger.info(f"Estado carregado de {self.state_file}")

        except json.JSONDecodeError as e:
            self._logger.error(f"Arquivo de estado corrompido: {e}. Usando padrão.")
            self.state = self._get_default_state()

        except (IOError, OSError) as e:
            self._logger.error(f"Erro ao ler estado: {e}. Usando padrão.")
            self.state = self._get_default_state()

    def save(self, force: bool = False) -> None:
        """
        Salva estado no arquivo JSON.

        Args:
            force: Força salvamento imediato (ignora dirty flag)

        Nota: Operação é síncrona mas rápida; considerada segura
        para este caso de uso.
        """
        if not force and not self._dirty:
            return

        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)

            self._dirty = False
            self._logger.debug(f"Estado salvo em {self.state_file}")

        except (IOError, OSError) as e:
            self._logger.error(f"Erro ao salvar estado: {e}")

    def set(self, path: str, value: Any) -> None:
        """
        Define valor usando notação de ponto.

        Args:
            path: Caminho aninhado (ex: 'window.width', 'layout.widgets.term-1')
            value: Valor a definir

        Exemplo:
            set('window.width', 1920)
            set('layout.widgets.term-1.working_dir', '/home/user')
        """
        keys = path.split('.')
        current = self.state

        for raw_key in keys[:-1]:
            key = int(raw_key) if raw_key.isdigit() else raw_key
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        final_key = keys[-1]
        if final_key.isdigit():
            final_key = int(final_key)
        current[final_key] = value

        self._dirty = True
        self._schedule_auto_save()

    def get(self, path: str, default: Any = None) -> Any:
        """
        Obtém valor usando notação de ponto.

        Args:
            path: Caminho aninhado
            default: Valor padrão se caminho não existir

        Returns:
            Valor ou default se não encontrado
        """
        keys = path.split('.')
        current = self.state

        for key in keys:
            if key.isdigit():
                key = int(key)
            if key not in current:
                return default
            current = current[key]

        return current

    def set_layout_state(self, layout_state: Dict[str, Any]) -> None:
        """
        Define todo o estado do layout.

        Args:
            layout_state: Dicionário com estrutura de colunas e widgets
        """
        self.state['layout'] = layout_state
        self._dirty = True
        self._schedule_auto_save()

    def get_layout_state(self) -> Dict[str, Any]:
        """Retorna o estado atual do layout."""
        return self.state.get('layout', {})

    def _schedule_auto_save(self) -> None:
        """
        Agenda auto-save com debounce.

        Cancela timer anterior se existir e cria novo.
        """
        if self._auto_save_timer:
            GLib.source_remove(self._auto_save_timer)

        self._auto_save_timer = GLib.timeout_add(
            self.DEBOUNCE_MS,
            self._auto_save_callback
        )

    def _auto_save_callback(self) -> bool:
        """
        Callback do timer de auto-save.

        Returns:
            False para não reagendar (executa apenas uma vez)
        """
        self.save()
        self._auto_save_timer = None
        return False  # IMPORTANTE: Retorna False para evitar loop infinito

    def shutdown(self) -> None:
        """
        Salva estado antes de encerrar a aplicação.

        Deve ser chamado no cleanup do app.
        """
        if self._auto_save_timer:
            GLib.source_remove(self._auto_save_timer)
        self.save(force=True)


# ============================================================================
# CONFIGURAÇÃO INICIAL (Simulando JSON futuro)
# ============================================================================

DEFAULT_LAYOUT: Dict[str, Any] = {
    "version": 1,
    "columns": [
        {
            "id": "col-1",
            "name": "Painel 1",
            "default_working_dir": DEFAULT_WORKING_DIR,
            "widgets": []
        },
        {
            "id": "col-2",
            "name": "Painel 2",
            "default_working_dir": DEFAULT_WORKING_DIR,
            "widgets": ["term-center"]
        },
        {
            "id": "col-3",
            "name": "Painel 3",
            "default_working_dir": DEFAULT_WORKING_DIR,
            "widgets": []
        }
    ],
    "widgets": {
        "term-center": {
            "type": "terminal",
            "title": os.path.basename(SHELL),
            "working_dir": DEFAULT_WORKING_DIR
        }
    }
}


def _default_layout() -> Dict[str, Any]:
    """Retorna uma cópia fresca do layout padrão."""
    return copy.deepcopy(DEFAULT_LAYOUT)


def _is_empty_layout(layout: Dict[str, Any]) -> bool:
    """Detecta layouts sem widgets ativos."""
    columns = layout.get('columns', [])
    return not any(column.get('widgets') for column in columns)


def _is_legacy_seed_layout(layout: Dict[str, Any]) -> bool:
    """Detecta o layout inicial antigo que abria um terminal em cada coluna."""
    columns = layout.get('columns', [])
    widgets = layout.get('widgets', {})
    if len(columns) != 3 or not isinstance(widgets, dict):
        return False

    expected = [('term-1',), ('term-2',), ('term-3',)]
    references = [tuple(column.get('widgets', [])) for column in columns]
    return references == expected and set(widgets.keys()) == {'term-1', 'term-2', 'term-3'}


def _normalize_layout_state(layout: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normaliza layouts inválidos, vazios ou herdados do seed antigo.

    Isso garante que a primeira abertura sempre comece com o painel central
    populado e laterais vazias, sem quebrar sessões customizadas válidas.
    """
    if not isinstance(layout, dict):
        return _default_layout()

    columns = layout.get('columns')
    widgets = layout.get('widgets')
    if not isinstance(columns, list) or not isinstance(widgets, dict):
        return _default_layout()

    if _is_empty_layout(layout) or _is_legacy_seed_layout(layout):
        return _default_layout()

    normalized = copy.deepcopy(layout)
    normalized_widgets: Dict[str, Dict[str, Any]] = {}

    for column in normalized.get('columns', []):
        valid_widget_ids = []
        for widget_id in column.get('widgets', []):
            widget_state = normalized['widgets'].get(widget_id)
            if isinstance(widget_state, dict):
                valid_widget_ids.append(widget_id)
                normalized_widgets[widget_id] = widget_state
        column['widgets'] = valid_widget_ids

    normalized['widgets'] = normalized_widgets
    normalized['version'] = 1

    if _is_empty_layout(normalized):
        return _default_layout()

    return normalized


# ============================================================================
# CLASSE ABSTRATA: Widget
# ============================================================================

class Widget(ABC):
    """
    Interface base para qualquer widget carregável no layout.

    Todo widget deve implementar estes métodos para ser compatível
    com o sistema de gerenciamento de layout dinâmico.
    """

    def __init__(self, widget_id: str, config: Dict[str, Any]):
        """
        Inicializa o widget com configuração.

        Args:
            widget_id: Identificador único do widget
            config: Dicionário de configuração específico do tipo
        """
        self.widget_id = widget_id
        self.config = config
        self._gtk_widget: Optional[Gtk.Widget] = None

    @abstractmethod
    def create_widget(self) -> Gtk.Widget:
        """
        Cria e retorna o widget GTK correspondente.

        Returns:
            Gtk.Widget: O widget pronto para ser adicionado ao layout
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Captura o estado atual do widget para persistência.

        Returns:
            Dict contendo o estado serializável do widget
        """
        pass

    @abstractmethod
    def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restaura o widget a partir de um estado salvo.

        Args:
            state: Dicionário contendo o estado anterior
        """
        pass

    def get_widget(self) -> Gtk.Widget:
        """
        Retorna o widget GTK (lazy initialization).

        Returns:
            O widget GTK criado por create_widget()
        """
        if self._gtk_widget is None:
            self._gtk_widget = self.create_widget()
        return self._gtk_widget

    def destroy(self) -> None:
        """Limpa recursos do widget."""
        if self._gtk_widget:
            self._gtk_widget.destroy()
            self._gtk_widget = None


# ============================================================================
# IMPLEMENTAÇÃO: TerminalWidget
# ============================================================================

class TerminalWidget(Widget):
    """
    Widget encapsulando um terminal VTE com header e controles.

    Mantém toda a funcionalidade original do TerminalWrapper
    mas agora através da interface Widget.
    """

    def __init__(self, widget_id: str, config: Dict[str, Any], column: 'WidgetColumn'):
        super().__init__(widget_id, config)
        self.column = column
        self.terminal: Optional[Vte.Terminal] = None
        self.wrapper_box: Optional[Gtk.Box] = None
        self.terminal_container: Optional[Gtk.Box] = None
        self.title_label: Optional[Gtk.Label] = None

    def create_widget(self) -> Gtk.Widget:
        """
        Cria o wrapper completo do terminal com header.

        Returns:
            Gtk.Box contendo header + terminal VTE
        """
        # Container principal
        self.wrapper_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.wrapper_box.get_style_context().add_class('terminal-wrapper')
        self.wrapper_box.connect('button-press-event', self._on_button_press)

        # Header do terminal
        header = self._create_header()
        self.wrapper_box.pack_start(header, False, False, 0)

        # Container para o terminal VTE
        self.terminal_container = Gtk.Box()
        self.terminal_container.set_vexpand(True)
        self.terminal_container.set_hexpand(True)
        self.wrapper_box.pack_start(self.terminal_container, True, True, 0)

        # Iniciar o terminal de forma assíncrona (sem delays)
        self._start_terminal_async()

        return self.wrapper_box

    def _create_header(self) -> Gtk.Box:
        """Cria o header com drag handle, título e botão fechar."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.get_style_context().add_class('terminal-header')

        # Drag handle
        drag_handle = Gtk.Label(label="⋮⋮")
        drag_handle.get_style_context().add_class('drag-handle')
        header.pack_start(drag_handle, False, False, 4)

        # Título
        self.title_label = Gtk.Label(
            label=self.config.get('title', os.path.basename(SHELL))
        )
        self.title_label.get_style_context().add_class('terminal-title')
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_hexpand(True)
        header.pack_start(self.title_label, True, True, 0)

        # Botão fechar
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class('close-term-button')
        close_btn.set_tooltip_text("Fechar terminal")
        close_btn.connect('clicked', self._on_close)
        header.pack_end(close_btn, False, False, 0)

        return header

    def _start_terminal_async(self) -> None:
        """
        Inicia o terminal VTE de forma assíncrona usando GLib.idle_add.

        Isso garante que o terminal seja criado quando o GTK main loop
        está pronto, eliminando a necessidade de delays arbitrários.
        """
        GLib.idle_add(self._initialize_terminal)

    def _initialize_terminal(self) -> bool:
        """
        Inicializa o terminal VTE quando o main loop está pronto.

        Returns:
            False para não reagendar (executa apenas uma vez)
        """
        if self.terminal is not None:
            return False  # Já inicializado

        self.terminal = Vte.Terminal()
        self.terminal.set_scrollback_lines(-1)
        self.terminal.set_audible_bell(False)

        # Fonte
        font_desc = Pango.FontDescription.from_string("Monospace 11")
        self.terminal.set_font(font_desc)

        # Cores (mantidas idênticas ao original)
        fg = Gdk.RGBA()
        fg.parse("#d3d7cf")
        bg = Gdk.RGBA()
        bg.parse("rgba(30, 30, 30, 0.85)")
        self.terminal.set_color_foreground(fg)
        self.terminal.set_color_background(bg)

        # Spawnar shell
        working_dir = _normalize_working_dir(self.config.get('working_dir'))
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            working_dir,
            [SHELL],
            None,
            GLib.SpawnFlags.SEARCH_PATH,
            None, None
        )

        self.terminal.set_vexpand(True)
        self.terminal.set_hexpand(True)
        self.terminal_container.pack_start(self.terminal, True, True, 0)

        # Atalho Ctrl+Shift+W para fechar
        self.terminal.connect('key-press-event', self._on_key_press)
        self.terminal.connect('focus-in-event', self._on_focus_in)

        # Hook para salvar working directory quando mudar
        self.terminal.connect('current-directory-uri-changed', self._on_cwd_changed)

        self.wrapper_box.show_all()
        return False  # IMPORTANTE: Retorna False para evitar loop infinito

    def _on_cwd_changed(self, terminal: Vte.Terminal) -> None:
        """
        Salva working directory quando o terminal muda de diretório.

        Conectado ao sinal 'current-directory-uri-changed' do VTE.
        """
        try:
            cwd = _path_from_vte_uri(terminal.get_current_directory_uri())
            if cwd:
                # Notifica StateManager (se disponível na janela)
                toplevel = self.wrapper_box.get_toplevel()
                if hasattr(toplevel, 'state_manager'):
                    toplevel.state_manager.set(
                        f'layout.widgets.{self.widget_id}.working_dir',
                        cwd
                    )
        except Exception as e:
            logging.getLogger(__name__).debug(f"Erro ao salvar cwd: {e}")

    def _on_focus_in(self, *_args) -> bool:
        self.column.mark_active()
        return False

    def _on_key_press(self, widget, event) -> bool:
        """Atalhos de teclado."""
        state = event.state & Gtk.accelerator_get_default_mod_mask()
        ctrl_shift = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK

        if state == ctrl_shift and event.keyval == Gdk.KEY_w:
            self._on_close(None)
            return True
        if state == ctrl_shift and event.keyval == Gdk.KEY_t:
            self.column.add_widget('terminal')
            return True
        return False

    def _on_button_press(self, widget, event) -> bool:
        """Menu de contexto com botão direito."""
        self.column.mark_active()
        if event.button == 3:
            menu = Gtk.Menu()

            items = [
                ("Copiar", self._on_copy),
                ("Colar", self._on_paste),
                ("Limpar", self._on_clear),
                None,
                ("Fechar terminal", self._on_close),
            ]

            for item in items:
                if item is None:
                    menu.append(Gtk.SeparatorMenuItem())
                else:
                    label, callback = item
                    mi = Gtk.MenuItem(label=label)
                    mi.connect('activate', callback)
                    menu.append(mi)

            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        return False

    def _on_copy(self, widget) -> None:
        if self.terminal and self.terminal.get_has_selection():
            self.terminal.copy_clipboard_format(Vte.Format.TEXT)

    def _on_paste(self, widget) -> None:
        if self.terminal:
            self.terminal.paste_clipboard()

    def _on_clear(self, widget) -> None:
        if self.terminal:
            self.terminal.reset(True, True)

    def _on_close(self, button) -> None:
        """Fecha e remove este terminal."""
        # Notifica a coluna para remover este widget
        if hasattr(self.column, 'remove_widget'):
            self.column.remove_widget(self)
        self.destroy()

    def get_state(self) -> Dict[str, Any]:
        """Captura estado do terminal para persistência."""
        state = {
            'type': 'terminal',
            'title': self.config.get('title', os.path.basename(SHELL))
        }
        if self.terminal:
            try:
                cwd = _path_from_vte_uri(self.terminal.get_current_directory_uri())
                state['working_dir'] = cwd
            except Exception:
                pass
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restaura estado do terminal (working directory)."""
        if 'working_dir' in state:
            self.config['working_dir'] = _normalize_working_dir(state['working_dir'])


# ============================================================================
# WIDGET COLUMN (Antiga TerminalColumn refatorada)
# ============================================================================

class WidgetColumn(Gtk.Box):
    """
    Uma coluna que contém múltiplos widgets configuráveis.

    Mantém toda funcionalidade do TerminalColumn original
    mas agora aceita qualquer tipo de Widget.
    """

    def __init__(self, column_id: str, name: str,
                 default_working_dir: Optional[str] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.column_id = column_id
        self.display_name = name
        self.default_working_dir = (
            _normalize_working_dir(default_working_dir) or DEFAULT_WORKING_DIR
        )
        self.title_label: Optional[Gtk.Label] = None
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Widget instances tracking
        self.widgets: Dict[str, Widget] = {}

        # Header da coluna
        header = self._create_column_header()
        self.pack_start(header, False, False, 0)

        # Scroll container para os widgets
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.pack_start(scroll, True, True, 0)

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.widget_box.set_margin_start(4)
        self.widget_box.set_margin_end(4)
        self.widget_box.set_margin_bottom(4)
        scroll.add(self.widget_box)

        self.get_style_context().add_class('terminal-column')

        # Setup drag-and-drop
        self._setup_dnd()

    def _create_column_header(self) -> Gtk.Box:
        """Cria o header com nome e ações mínimas."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.get_style_context().add_class('column-header')
        header.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        header.connect('button-press-event', self._on_header_button_press)

        self.title_label = Gtk.Label(label=self.display_name)
        self.title_label.get_style_context().add_class('column-label')
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_hexpand(True)
        header.pack_start(self.title_label, True, True, 8)

        add_btn = Gtk.Button(label="+")
        add_btn.get_style_context().add_class('add-button')
        add_btn.set_tooltip_text("Adicionar terminal ao painel ativo")
        add_btn.connect('clicked', lambda _button: self.add_widget('terminal'))
        header.pack_end(add_btn, False, False, 0)

        menu_btn = Gtk.Button(label="⋯")
        menu_btn.get_style_context().add_class('column-menu-button')
        menu_btn.set_tooltip_text("Opções do painel")
        menu_btn.connect('clicked', self._show_column_menu)
        header.pack_end(menu_btn, False, False, 0)

        return header

    def _on_header_button_press(self, _widget, event) -> bool:
        self.mark_active()
        if event.button == 3:
            self._show_column_menu(None)
            return True
        return False

    def _setup_dnd(self) -> None:
        """Configura drag-and-drop usando GTK3 APIs."""
        target_entry = Gtk.TargetEntry.new("widget-wrapper", Gtk.TargetFlags.SAME_APP, 0)
        self.widget_box.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [target_entry],
            Gdk.DragAction.MOVE
        )
        self.widget_box.connect('drag-data-received', self._on_drag_data_received)
        self.widget_box.connect('drag-motion', self._on_drag_motion)
        self.widget_box.connect('drag-leave', self._on_drag_leave)

    def _on_drag_motion(self, widget, context, x, y, time) -> bool:
        """Highlight visual ao arrastar por cima."""
        self.mark_active()
        self.get_style_context().add_class('drop-hover')
        Gdk.drag_status(context, Gdk.DragAction.MOVE, time)
        return True

    def _on_drag_leave(self, widget, context, time) -> None:
        """Remove highlight."""
        self.get_style_context().remove_class('drop-hover')

    def _on_drag_data_received(self, widget, context, x, y, data, info, time) -> None:
        """Recebe um widget arrastado."""
        self.get_style_context().remove_class('drop-hover')
        widget_id = data.get_text()
        toplevel = self.get_toplevel()
        widget_instance = getattr(toplevel, '_dnd_widget', None)

        if widget_id and widget_instance and widget_instance.wrapper_box:
            source_column = widget_instance.column
            old_parent = widget_instance.wrapper_box.get_parent()
            if old_parent:
                old_parent.remove(widget_instance.wrapper_box)

            if source_column is not self:
                source_column.widgets.pop(widget_id, None)
                self.widgets[widget_id] = widget_instance
                widget_instance.column = self

            self.widget_box.pack_start(widget_instance.wrapper_box, True, True, 0)
            widget_instance.wrapper_box.get_style_context().remove_class('dragging')
            widget_instance.wrapper_box.show_all()
            self.mark_active()
            self._notify_layout_changed()
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)

        if hasattr(toplevel, '_dnd_widget'):
            toplevel._dnd_widget = None

    def add_widget(self, widget_type: str, config: Optional[Dict[str, Any]] = None,
                   widget_id: Optional[str] = None) -> Widget:
        """
        Adiciona um widget à coluna via Factory.

        Args:
            widget_type: Tipo do widget ('terminal', 'notes', etc.)
            config: Configuração opcional
            widget_id: ID explícito para restauração de sessão

        Returns:
            A instância do Widget criada
        """
        self.mark_active()
        if widget_id is None:
            widget_id = f"{widget_type}-{uuid.uuid4().hex[:8]}"

        # Config padrão se não fornecido
        if config is None:
            config = {
                'type': widget_type,
                'title': os.path.basename(SHELL),
                'working_dir': self.default_working_dir,
            }
        else:
            config = dict(config)

        if widget_type == 'terminal':
            config.setdefault('title', os.path.basename(SHELL))
            config['working_dir'] = _normalize_working_dir(
                config.get('working_dir') or self.default_working_dir
            ) or self.default_working_dir

        # Criar via factory
        widget = WidgetFactory.create(widget_type, widget_id, config, self)
        self.widgets[widget_id] = widget
        toplevel = self.get_toplevel()
        if hasattr(toplevel, 'layout_manager'):
            toplevel.layout_manager.widgets[widget_id] = widget

        # Obter widget GTK e adicionar
        gtk_widget = widget.get_widget()
        self.widget_box.pack_start(gtk_widget, True, True, 0)

        # Configurar drag source no header (se for TerminalWidget)
        if hasattr(widget, 'wrapper_box') and widget.wrapper_box:
            header = widget.wrapper_box.get_children()[0]
            target_entry = Gtk.TargetEntry.new("widget-wrapper", Gtk.TargetFlags.SAME_APP, 0)
            header.drag_source_set(
                Gdk.ModifierType.BUTTON1_MASK,
                [target_entry],
                Gdk.DragAction.MOVE
            )
            header.drag_source_set_icon_name('utilities-terminal')
            header.connect('drag-begin', self._on_drag_begin, widget)
            header.connect('drag-data-get', self._on_drag_data_get, widget)
            header.connect('drag-end', self._on_drag_end, widget)

        self.widget_box.show_all()
        self._notify_layout_changed()

        return widget

    def _on_drag_begin(self, widget, context, widget_instance: Widget) -> None:
        """Quando começa a arrastar um widget."""
        self.mark_active()
        if widget_instance.wrapper_box:
            widget_instance.wrapper_box.get_style_context().add_class('dragging')
        self.get_toplevel()._dnd_widget = widget_instance

    def _on_drag_data_get(self, widget, context, data, info, time, widget_instance: Widget) -> None:
        """Fornece dados do drag."""
        data.set_text(widget_instance.widget_id, -1)

    def _on_drag_end(self, widget, context, widget_instance: Widget) -> None:
        if widget_instance.wrapper_box:
            widget_instance.wrapper_box.get_style_context().remove_class('dragging')
        toplevel = self.get_toplevel()
        if hasattr(toplevel, '_dnd_widget'):
            toplevel._dnd_widget = None

    def _show_column_menu(self, button) -> None:
        self.mark_active()
        menu = Gtk.Menu()

        items = [
            ("Novo terminal", lambda *_args: self.add_widget('terminal')),
            ("Renomear painel", lambda *_args: self._prompt_rename()),
            ("Diretório padrão", lambda *_args: self._prompt_default_directory()),
            None,
            ("Limpar painel", lambda *_args: self.clear_widgets()),
        ]

        for item in items:
            if item is None:
                menu.append(Gtk.SeparatorMenuItem())
                continue

            label, callback = item
            menu_item = Gtk.MenuItem(label=label)
            menu_item.connect('activate', callback)
            menu.append(menu_item)

        menu.show_all()
        if button is not None:
            menu.popup_at_widget(
                button,
                Gdk.Gravity.SOUTH_EAST,
                Gdk.Gravity.NORTH_EAST,
                None
            )
        else:
            menu.popup(
                None,
                None,
                None,
                None,
                0,
                Gtk.get_current_event_time()
            )

    def _prompt_rename(self) -> None:
        dialog = Gtk.Dialog(
            title="Renomear painel",
            transient_for=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK,
        )
        dialog.set_default_response(Gtk.ResponseType.OK)

        entry = Gtk.Entry()
        entry.set_text(self.display_name)
        entry.set_activates_default(True)
        entry.set_margin_top(12)
        entry.set_margin_bottom(12)
        entry.set_margin_start(12)
        entry.set_margin_end(12)

        box = dialog.get_content_area()
        box.add(entry)
        dialog.show_all()

        if dialog.run() == Gtk.ResponseType.OK:
            new_name = entry.get_text().strip()
            if new_name:
                self.display_name = new_name
                self.title_label.set_text(new_name)
                self._notify_layout_changed()

        dialog.destroy()

    def _prompt_default_directory(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Diretório padrão do painel",
            transient_for=self.get_toplevel(),
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            "Selecionar", Gtk.ResponseType.OK,
        )
        dialog.set_current_folder(self.default_working_dir)

        if dialog.run() == Gtk.ResponseType.OK:
            selected = dialog.get_filename()
            normalized = _normalize_working_dir(selected)
            if normalized:
                self.default_working_dir = normalized
                self._notify_layout_changed()

        dialog.destroy()

    def clear_widgets(self) -> None:
        for widget in list(self.widgets.values()):
            self.remove_widget(widget)
            widget.destroy()

    def mark_active(self) -> None:
        toplevel = self.get_toplevel()
        if hasattr(toplevel, 'set_active_column'):
            toplevel.set_active_column(self.column_id)

    def set_active(self, is_active: bool) -> None:
        context = self.get_style_context()
        if is_active:
            context.add_class('column-active')
        else:
            context.remove_class('column-active')

    def _notify_layout_changed(self) -> None:
        toplevel = self.get_toplevel()
        if hasattr(toplevel, 'state_manager'):
            toplevel.state_manager.set_layout_state(
                toplevel.layout_manager.get_state()
            )

    def remove_widget(self, widget: Widget) -> None:
        """
        Remove um widget da coluna.

        Args:
            widget: A instância do Widget a remover
        """
        widget_id = widget.widget_id
        if widget_id in self.widgets:
            del self.widgets[widget_id]

        toplevel = self.get_toplevel()
        if hasattr(toplevel, 'layout_manager'):
            toplevel.layout_manager.widgets.pop(widget_id, None)

        if widget.wrapper_box:
            parent = widget.wrapper_box.get_parent()
            if parent:
                parent.remove(widget.wrapper_box)
        self._notify_layout_changed()


# ============================================================================
# FACTORY: WidgetFactory
# ============================================================================

class WidgetFactory:
    """
    Factory para criar widgets dinamicamente baseados em configuração.

    Novos tipos de widgets podem ser adicionados registrando na
    classe _widget_types sem modificar código existente.
    """

    _widget_types: Dict[str, type] = {
        'terminal': TerminalWidget,
        # Futuros widgets:
        # 'notes': NotesWidget,
        # 'monitor': ResourceMonitorWidget,
        # 'calculator': CalculatorWidget,
    }

    @classmethod
    def register(cls, widget_type: str, widget_class: type) -> None:
        """
        Registra um novo tipo de widget.

        Args:
            widget_type: Nome do tipo (ex: 'notes')
            widget_class: Classe que implementa Widget
        """
        cls._widget_types[widget_type] = widget_class

    @classmethod
    def create(cls, widget_type: str, widget_id: str, config: Dict[str, Any],
               column: WidgetColumn) -> Widget:
        """
        Cria uma instância de widget.

        Args:
            widget_type: Tipo do widget a criar
            widget_id: Identificador único
            config: Dicionário de configuração
            column: Coluna onde o widget será adicionado

        Returns:
            Instância de Widget

        Raises:
            ValueError: Se o tipo de widget não for registrado
        """
        widget_class = cls._widget_types.get(widget_type)
        if not widget_class:
            raise ValueError(f"Tipo de widget desconhecido: {widget_type}")

        return widget_class(widget_id, config, column)

    @classmethod
    def get_available_types(cls) -> List[str]:
        """Retorna lista de tipos de widgets disponíveis."""
        return list(cls._widget_types.keys())


# ============================================================================
# LAYOUT MANAGER: DynamicLayoutManager
# ============================================================================

class DynamicLayoutManager:
    """
    Gerenciador de layout baseado em configuração.

    Responsável por interpretar a configuração de layout
    e criar as colunas e widgets dinamicamente.
    """

    def __init__(self, container: Gtk.Box):
        """
        Inicializa o gerenciador.

        Args:
            container: Container GTK onde as colunas serão adicionadas
        """
        self.container = container
        self.columns: Dict[str, WidgetColumn] = {}
        self.widgets: Dict[str, Widget] = {}

    def load_layout(self, layout_config: Dict[str, Any]) -> None:
        """
        Carrega layout a partir de configuração.

        Args:
            layout_config: Dicionário com estrutura de colunas e widgets
        """
        self.columns = {}
        self.widgets = {}

        # Limpa layout atual
        for child in self.container.get_children():
            self.container.remove(child)

        # Cria colunas dinamicamente
        for col_config in layout_config.get('columns', []):
            self._create_column(col_config, layout_config.get('widgets', {}))

        self.container.show_all()

    def _create_column(self, col_config: Dict[str, Any], widgets_config: Dict[str, Any]) -> None:
        """Cria uma coluna e seus widgets."""
        col_id = col_config['id']
        name = col_config.get('name', 'Painel')
        default_working_dir = col_config.get('default_working_dir')

        column = WidgetColumn(col_id, name, default_working_dir)
        self.columns[col_id] = column
        self.container.pack_start(column, True, True, 0)

        # Cria widgets dentro da coluna
        for widget_id in col_config.get('widgets', []):
            widget_data = widgets_config.get(widget_id, {})
            if widget_data:
                widget_type = widget_data.get('type', 'terminal')
                widget = column.add_widget(widget_type, widget_data, widget_id=widget_id)
                self.widgets[widget_id] = widget

    def add_column(self, name: str) -> str:
        """
        Adiciona uma nova coluna dinamicamente.

        Args:
            name: Nome da coluna

        Returns:
            ID da coluna criada
        """
        col_id = f"col-{len(self.columns) + 1}"
        column = WidgetColumn(col_id, name, DEFAULT_WORKING_DIR)
        self.columns[col_id] = column
        self.container.pack_start(column, True, True, 0)
        column.show_all()
        return col_id

    def get_first_column(self) -> Optional[WidgetColumn]:
        return next(iter(self.columns.values()), None)

    def get_column(self, column_id: Optional[str]) -> Optional[WidgetColumn]:
        if not column_id:
            return None
        return self.columns.get(column_id)

    def add_terminal_to_column(self, column_id: Optional[str]) -> Optional[Widget]:
        column = self.get_column(column_id) or self.get_first_column()
        if not column:
            return None
        return column.add_widget('terminal')

    def get_state(self) -> Dict[str, Any]:
        """
        Captura estado atual de todo o layout.

        Returns:
            Dicionário com colunas e widgets serializados
        """
        columns_data = []
        widgets_data = {}

        for col_id, column in self.columns.items():
            col_widgets = []
            for widget_id, widget in column.widgets.items():
                col_widgets.append(widget_id)
                widgets_data[widget_id] = widget.get_state()

            columns_data.append({
                'id': col_id,
                'name': column.display_name,
                'default_working_dir': column.default_working_dir,
                'widgets': col_widgets
            })

        return {
            'version': 1,
            'columns': columns_data,
            'widgets': widgets_data
        }


# ============================================================================
# JANELA PRINCIPAL: TerminalMultiPaneWindow (Refatorada)
# ============================================================================

class TerminalMultiPaneWindow(Gtk.ApplicationWindow):
    """
    Janela principal com layout dinâmico orientado a configuração.

    Não mais cria "Painel 1", "Painel 2" hardcoded.
    O layout é carregado a partir de configuração.
    """

    def __init__(self, app, state_manager: StateManager):
        super().__init__(application=app, title=APPLICATION_TITLE)
        self.state_manager = state_manager
        self._dnd_widget = None  # Para drag-and-drop
        self.active_column_id: Optional[str] = None
        self._is_fullscreen = False
        self._is_maximized = self.state_manager.get('window.is_maximized', True)

        # Restaurar tamanho da janela do estado salvo
        width = self.state_manager.get('window.width', 1600)
        height = self.state_manager.get('window.height', 900)
        self.set_default_size(width, height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_keep_above(False)
        self.set_skip_taskbar_hint(False)
        self.set_skip_pager_hint(False)
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)

        # Restaurar estado maximizado
        if self.state_manager.get('window.is_maximized', True):
            GLib.idle_add(self.maximize)

        # Transparência Global GTK (mantida)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Conectar sinais da janela para persistência
        self.connect('configure-event', self._on_configure)
        self.connect('window-state-event', self._on_window_state)
        self.connect('delete-event', self._on_delete)

        # Atalhos globais
        self.connect('key-press-event', self._on_key_press)

        # Layout Manager
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói a interface usando DynamicLayoutManager com estado salvo."""
        self._frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame = self._frame
        frame.get_style_context().add_class('modal-shell')
        self._update_frame_margins()
        self.add(frame)

        titlebar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        titlebar.get_style_context().add_class('modal-titlebar')
        titlebar.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        titlebar.connect('button-press-event', self._on_titlebar_button_press)
        frame.pack_start(titlebar, False, False, 0)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        controls.get_style_context().add_class('window-controls')
        titlebar.pack_end(controls, False, False, 0)

        minimize_button = self._create_window_control_button(
            "−",
            "Ocultar workspace",
            lambda _button: self.hide_workspace(),
        )
        controls.pack_start(minimize_button, False, False, 0)

        maximize_button = self._create_window_control_button(
            "□",
            "Expandir ou restaurar workspace",
            lambda _button: self._toggle_maximize(),
        )
        controls.pack_start(maximize_button, False, False, 0)

        close_button = self._create_window_control_button(
            "✕",
            "Fechar workspace",
            lambda _button: self.hide_workspace(),
        )
        controls.pack_start(close_button, False, False, 0)

        divider = Gtk.Box()
        divider.get_style_context().add_class('modal-divider')
        frame.pack_start(divider, False, False, 0)

        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_homogeneous(True)
        main_box.get_style_context().add_class('main-container')
        frame.pack_start(main_box, True, True, 0)

        # Layout Manager para gerenciar colunas e widgets dinamicamente
        self.layout_manager = DynamicLayoutManager(main_box)

        # Bootstrapping: Carregar layout do estado salvo ou usar padrão
        initial_layout = _normalize_layout_state(self.state_manager.get_layout_state())
        self.state_manager.set_layout_state(initial_layout)
        self.layout_manager.load_layout(initial_layout)
        self._set_initial_active_column(initial_layout)

    def _create_window_control_button(
        self,
        label: str,
        tooltip: str,
        callback: Callable[[Gtk.Button], None],
    ) -> Gtk.Button:
        """Cria um botão mínimo de controle da janela."""
        button = Gtk.Button(label=label)
        button.get_style_context().add_class('control-button')
        button.set_tooltip_text(tooltip)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.connect('clicked', callback)
        return button

    def _set_initial_active_column(self, layout_state: Dict[str, Any]) -> None:
        """Prioriza o painel com widgets; se vazio, foca o painel central."""
        preferred_column_id = next(
            (
                column.get('id')
                for column in layout_state.get('columns', [])
                if column.get('widgets')
            ),
            None,
        )

        if preferred_column_id is None and 'col-2' in self.layout_manager.columns:
            preferred_column_id = 'col-2'

        if preferred_column_id is None:
            first_column = self.layout_manager.get_first_column()
            preferred_column_id = first_column.column_id if first_column else None

        if preferred_column_id:
            self.set_active_column(preferred_column_id)

    def _toggle_maximize(self) -> None:
        """Alterna entre expandido e restaurado sem usar decoração do sistema."""
        if self._is_fullscreen:
            self.unfullscreen()
            self._is_fullscreen = False

        if self._is_maximized:
            self.unmaximize()
        else:
            self.maximize()

    def _update_frame_margins(self) -> None:
        """Ajusta margens do frame baseado no estado de maximizacao."""
        margin = 0 if self._is_maximized else 24
        self._frame.set_margin_top(margin)
        self._frame.set_margin_bottom(margin)
        self._frame.set_margin_start(margin)
        self._frame.set_margin_end(margin)

    def _update_input_region(self) -> None:
        """Define a regiao de input para excluir margens transparentes."""
        if self._is_maximized:
            self.input_shape_combine_region(None)
        else:
            alloc = self.get_allocation()
            if alloc.width > 48 and alloc.height > 48:
                region = cairo.Region(cairo.RectangleInt(
                    24, 24, alloc.width - 48, alloc.height - 48
                ))
                self.input_shape_combine_region(region)

    def set_active_column(self, column_id: Optional[str]) -> None:
        self.active_column_id = column_id
        for current_id, column in self.layout_manager.columns.items():
            column.set_active(current_id == column_id)

    def show_workspace(self) -> None:
        self.show_all()
        self.deiconify()
        self.present()

    def hide_workspace(self) -> None:
        self.hide()

    def toggle_workspace(self) -> None:
        if self.get_visible():
            self.hide_workspace()
        else:
            self.show_workspace()

    def add_terminal_to_active_column(self) -> None:
        self.show_workspace()
        widget = self.layout_manager.add_terminal_to_column(self.active_column_id)
        if widget and widget.column:
            self.set_active_column(widget.column.column_id)

    def reset_session(self) -> None:
        default_layout = _default_layout()
        self.state_manager.set_layout_state(default_layout)
        self.layout_manager.load_layout(default_layout)
        self._set_initial_active_column(default_layout)
        self.show_workspace()

    def _on_titlebar_button_press(self, _widget, event) -> bool:
        """Permite arrastar a janela pelo header customizado."""
        if event.button != Gdk.BUTTON_PRIMARY:
            return False

        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self._toggle_maximize()
            return True

        self.begin_move_drag(
            int(event.button),
            int(event.x_root),
            int(event.y_root),
            event.time,
        )
        return True

    def _on_configure(self, widget, event) -> bool:
        """
        Hook para salvar dimensões da janela quando redimensionada.

        Conectado ao sinal 'configure-event' do GTK.
        Debounce evita salvamento excessivo.
        """
        # Ignorar configurações de tela cheia (retorna tamanho 0,0)
        if event.width > 0 and event.height > 0:
            self.state_manager.set('window.width', event.width)
            self.state_manager.set('window.height', event.height)
        if not self._is_maximized:
            self._update_input_region()
        return False

    def _on_window_state(self, widget, event) -> bool:
        """
        Hook para salvar estado maximizado/minimizado da janela.

        Conectado ao sinal 'window-state-event' do GTK.
        """
        is_maximized = bool(
            event.new_window_state & Gdk.WindowState.MAXIMIZED
        )
        self._is_maximized = is_maximized
        self.state_manager.set('window.is_maximized', is_maximized)
        self._update_frame_margins()
        self._update_input_region()
        return False

    def _on_key_press(self, window, event) -> bool:
        """Teclas globais."""
        if event.keyval == Gdk.KEY_Escape:
            self.hide_workspace()
            return True

        state = event.state & Gtk.accelerator_get_default_mod_mask()
        ctrl_shift = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK
        if state == ctrl_shift and event.keyval == Gdk.KEY_t:
            self.add_terminal_to_active_column()
            return True

        if event.keyval == Gdk.KEY_F11:
            if self._is_fullscreen:
                self.unfullscreen()
            else:
                self.fullscreen()
            self._is_fullscreen = not self._is_fullscreen
            return True
        return False

    def _on_delete(self, window, event) -> bool:
        """Esconder em vez de destruir."""
        self.hide_workspace()
        return True  # Impede destruição


# ============================================================================
# APLICAÇÃO: TerminalMultiPaneApp (Mantida)
# ============================================================================

class TerminalMultiPaneApp(Gtk.Application):
    """Aplicação principal."""

    def __init__(self):
        super().__init__(
            application_id=APPLICATION_ID,
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        self.window = None
        self.state_manager = None
        self._pending_command = 'show'
        self._use_indicator = False
        self._indicator = None

    def do_startup(self):
        """Chamado uma vez quando a aplicação inicia."""
        Gtk.Application.do_startup(self)

        # Inicializar StateManager
        self.state_manager = StateManager()

        self._apply_css()

    def do_activate(self):
        """Chamado quando a aplicação é ativada (abrir janela)."""
        if not self.window:
            self.window = TerminalMultiPaneWindow(self, self.state_manager)

        self._apply_pending_command()

    def do_command_line(self, command_line) -> int:
        args = list(command_line.get_arguments()[1:])
        self._pending_command = self._parse_command(args)
        self._use_indicator = self._use_indicator or '--tray-indicator' in args

        if self._use_indicator and self._indicator is None:
            self._indicator = create_indicator(self)

        self.activate()
        return 0

    def _parse_command(self, args: List[str]) -> str:
        if '--toggle' in args:
            return 'toggle'
        if '--new-terminal' in args:
            return 'new-terminal'
        if '--reopen' in args or '--reset' in args:
            return 'reopen'
        if '--hide' in args:
            return 'hide'
        return 'show'

    def _apply_pending_command(self) -> None:
        command = self._pending_command or 'show'

        if command == 'toggle':
            self.window.toggle_workspace()
        elif command == 'new-terminal':
            self.window.add_terminal_to_active_column()
        elif command == 'reopen':
            self.window.reset_session()
        elif command == 'hide':
            self.window.hide_workspace()
        else:
            self.window.show_workspace()

        self._pending_command = 'show'

    def _apply_css(self):
        """Aplica estilos minimalistas para um workspace modal discreto."""
        css = """
            window {
                background-color: transparent;
            }

            .modal-shell {
                background-color: rgba(12, 12, 13, 0.82);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 0;
            }

            .modal-titlebar {
                background-color: transparent;
                padding: 12px 14px 10px 14px;
            }

            .modal-divider {
                min-height: 1px;
                background-color: rgba(255, 255, 255, 0.06);
            }

            .main-container {
                background-color: transparent;
            }

            .terminal-column {
                background-color: transparent;
                border-right: 1px solid rgba(255, 255, 255, 0.04);
                margin: 0;
                transition: all 0.16s ease;
            }

            .terminal-column:last-child {
                border-right: none;
            }

            .terminal-column.column-active {
                background-color: rgba(255, 255, 255, 0.03);
            }

            .terminal-column.drop-hover {
                background-color: rgba(255, 255, 255, 0.05);
            }

            .column-header {
                background-color: transparent;
                padding: 14px 14px 10px 14px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }

            .column-label {
                color: rgba(244, 244, 245, 0.9);
                font-weight: 600;
                font-size: 0.92em;
            }

            .add-button, .column-menu-button, .control-button {
                min-width: 28px;
                min-height: 28px;
                padding: 0;
                border-radius: 0;
                background-color: transparent;
                color: rgba(214, 214, 217, 0.7);
            }

            .add-button:hover, .column-menu-button:hover, .control-button:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.95);
            }

            .terminal-wrapper {
                background-color: transparent;
                border: none;
                margin: 6px 10px;
            }

            .terminal-header {
                background-color: transparent;
                padding: 7px 8px;
            }

            .drag-handle {
                color: rgba(160, 160, 160, 0.3);
                font-size: 0.85em;
            }

            .terminal-title {
                color: rgba(210, 210, 210, 0.8);
                font-weight: 500;
                font-size: 0.85em;
            }

            .close-term-button {
                min-width: 24px;
                min-height: 24px;
                padding: 0;
                background-color: transparent;
                color: rgba(255, 255, 255, 0.5);
                border-radius: 0;
            }

            .close-term-button:hover {
                color: rgba(255, 255, 255, 0.9);
                background-color: rgba(255, 255, 255, 0.12);
            }

            .window-controls {
                background-color: transparent;
                padding: 0;
            }

            .window-controls .control-button {
                font-size: 0.92em;
            }

            scrollbar slider {
                background-color: rgba(255, 255, 255, 0.12);
                border-radius: 0;
                min-width: 6px;
                min-height: 32px;
            }

            button {
                background-image: none;
                box-shadow: none;
                border: none;
            }
        """

        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_shutdown(self):
        if self._indicator and AyatanaAppIndicator3 is not None:
            self._indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.PASSIVE)
        Gtk.Application.do_shutdown(self)


# ============================================================================
# APP INDICATOR (Mantido)
# ============================================================================

def _activate_command(app_instance, command: str) -> None:
    app_instance._pending_command = command
    app_instance.activate()


def create_indicator(app_instance) -> Optional[Any]:
    """Cria o ícone na barra superior usando AyatanaAppIndicator3."""
    if AyatanaAppIndicator3 is None:
        return None

    try:
        indicator = AyatanaAppIndicator3.Indicator.new(
            'terminal-multi-pane',
            'utilities-terminal',
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        indicator.set_title(APPLICATION_TITLE)

        menu = Gtk.Menu()

        open_item = Gtk.MenuItem(label="Abrir Terminal Multi-Pane")
        open_item.connect('activate', lambda _item: _activate_command(app_instance, 'show'))
        menu.append(open_item)

        new_item = Gtk.MenuItem(label="Novo terminal")
        new_item.connect('activate', lambda _item: _activate_command(app_instance, 'new-terminal'))
        menu.append(new_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Sair")
        quit_item.connect('activate', lambda w: app_instance.quit())
        menu.append(quit_item)

        menu.show_all()
        indicator.set_menu(menu)
        indicator.set_secondary_activate_target(open_item)

        print("AppIndicator criado com sucesso!", file=sys.stderr)
        return indicator

    except Exception as e:
        print(f"Erro ao criar AppIndicator: {e}", file=sys.stderr)
        return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Permitir Ctrl+C para fechar
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = TerminalMultiPaneApp()
    print("Iniciando Terminal Multi-Pane minimalista...", file=sys.stderr)

    try:
        app.run(sys.argv)
    finally:
        # Cleanup: salvar estado antes de encerrar
        if app.state_manager:
            app.state_manager.shutdown()


if __name__ == '__main__':
    main()
