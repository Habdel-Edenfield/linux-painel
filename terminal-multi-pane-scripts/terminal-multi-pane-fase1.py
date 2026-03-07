#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal Multi-Pane Manager - Fase 1: Refatoração Modular
Arquitetura baseada em Factory Pattern + Layout Orientado a Dados
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, AyatanaAppIndicator3, Vte, GLib, Gdk, Pango
import sys
import os
import signal
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import uuid

# Detectar shell padrão
SHELL = os.environ.get('SHELL', '/bin/bash')


# ============================================================================
# CONFIGURAÇÃO INICIAL (Simulando JSON futuro)
# ============================================================================

DEFAULT_LAYOUT: Dict[str, Any] = {
    "version": 1,
    "columns": [
        {"id": "col-1", "name": "Painel 1", "widgets": ["term-1"]},
        {"id": "col-2", "name": "Painel 2", "widgets": ["term-2"]},
        {"id": "col-3", "name": "Painel 3", "widgets": ["term-3"]}
    ],
    "widgets": {
        "term-1": {"type": "terminal", "title": os.path.basename(SHELL)},
        "term-2": {"type": "terminal", "title": os.path.basename(SHELL)},
        "term-3": {"type": "terminal", "title": os.path.basename(SHELL)}
    }
}


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

    def create_widget(self) -> Gtk.Widget:
        """
        Cria o wrapper completo do terminal com header.

        Returns:
            Gtk.Box contendo header + terminal VTE
        """
        # Container principal
        self.wrapper_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.wrapper_box.get_style_context().add_class('terminal-wrapper')

        # Header do terminal
        header = self._create_header()
        self.wrapper_box.pack_start(header, False, False, 0)

        # Container para o terminal VTE
        self.terminal_container = Gtk.Box()
        self.terminal_container.set_vexpand(True)
        self.terminal_container.set_hexpand(True)
        self.wrapper_box.pack_start(self.terminal_container, True, True, 0)

        # Menu de contexto (botão direito)
        self.wrapper_box.connect('button-press-event', self._on_button_press)

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
        title = Gtk.Label(label=self.config.get('title', os.path.basename(SHELL)))
        title.get_style_context().add_class('terminal-title')
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header.pack_start(title, True, True, 0)

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
        working_dir = self.config.get('working_dir')
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            None if not working_dir else working_dir,
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

        self.wrapper_box.show_all()
        return False  # IMPORTANTE: Retorna False para evitar loop infinito

    def _on_key_press(self, widget, event) -> bool:
        """Atalhos de teclado."""
        state = event.state & Gtk.accelerator_get_default_mod_mask()
        ctrl_shift = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK

        if state == ctrl_shift and event.keyval == Gdk.KEY_w:
            self._on_close(None)
            return True
        return False

    def _on_button_press(self, widget, event) -> bool:
        """Menu de contexto com botão direito."""
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
                cwd = self.terminal.get_current_directory_uri()
                state['working_dir'] = cwd
            except Exception:
                pass
        return state

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restaura estado do terminal (working directory)."""
        if 'working_dir' in state:
            self.config['working_dir'] = state['working_dir']


# ============================================================================
# WIDGET COLUMN (Antiga TerminalColumn refatorada)
# ============================================================================

class WidgetColumn(Gtk.Box):
    """
    Uma coluna que contém múltiplos widgets configuráveis.

    Mantém toda funcionalidade do TerminalColumn original
    mas agora aceita qualquer tipo de Widget.
    """

    def __init__(self, column_id: str, name: str):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.column_id = column_id
        self.set_hexpand(True)

        # Widget instances tracking
        self.widgets: Dict[str, Widget] = {}

        # Header da coluna
        header = self._create_column_header(name)
        self.pack_start(header, False, False, 0)

        # Scroll container para os widgets
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.pack_start(scroll, True, True, 0)

        self.widget_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.widget_box.set_margin_start(2)
        self.widget_box.set_margin_end(2)
        self.widget_box.set_margin_bottom(2)
        scroll.add(self.widget_box)

        self.get_style_context().add_class('terminal-column')

        # Setup drag-and-drop
        self._setup_dnd()

    def _create_column_header(self, name: str) -> Gtk.Box:
        """Cria o header com nome e botão adicionar."""
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class('column-header')

        label = Gtk.Label(label=name)
        label.get_style_context().add_class('column-label')
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        header.pack_start(label, True, True, 8)

        # Botão + (por padrão adiciona terminal)
        add_btn = Gtk.Button(label="+")
        add_btn.get_style_context().add_class('add-button')
        add_btn.set_tooltip_text("Adicionar terminal")
        add_btn.connect('clicked', lambda b: self.add_widget('terminal'))
        header.pack_end(add_btn, False, False, 4)

        return header

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

        if widget_id and hasattr(self.get_toplevel(), '_dnd_widget'):
            widget_instance = self.get_toplevel()._dnd_widget
            if widget_instance and widget_instance.wrapper_box:
                old_parent = widget_instance.wrapper_box.get_parent()
                if old_parent:
                    old_parent.remove(widget_instance.wrapper_box)
                self.widget_box.pack_start(widget_instance.wrapper_box, True, True, 0)
                widget_instance.wrapper_box.show_all()
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)

    def add_widget(self, widget_type: str, config: Optional[Dict[str, Any]] = None) -> Widget:
        """
        Adiciona um widget à coluna via Factory.

        Args:
            widget_type: Tipo do widget ('terminal', 'notes', etc.)
            config: Configuração opcional

        Returns:
            A instância do Widget criada
        """
        # Gerar ID único se não fornecido
        widget_id = f"{widget_type}-{uuid.uuid4().hex[:8]}"

        # Config padrão se não fornecido
        if config is None:
            config = {
                'type': widget_type,
                'title': os.path.basename(SHELL)
            }

        # Criar via factory
        widget = WidgetFactory.create(widget_type, widget_id, config, self)
        self.widgets[widget_id] = widget

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

        self.widget_box.show_all()
        return widget

    def _on_drag_begin(self, widget, context, widget_instance: Widget) -> None:
        """Quando começa a arrastar um widget."""
        if widget_instance.wrapper_box:
            widget_instance.wrapper_box.get_style_context().add_class('dragging')
        self.get_toplevel()._dnd_widget = widget_instance

    def _on_drag_data_get(self, widget, context, data, info, time, widget_instance: Widget) -> None:
        """Fornece dados do drag."""
        data.set_text(widget_instance.widget_id, -1)

    def remove_widget(self, widget: Widget) -> None:
        """
        Remove um widget da coluna.

        Args:
            widget: A instância do Widget a remover
        """
        widget_id = widget.widget_id
        if widget_id in self.widgets:
            del self.widgets[widget_id]
        if widget.wrapper_box:
            parent = widget.wrapper_box.get_parent()
            if parent:
                parent.remove(widget.wrapper_box)


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

        column = WidgetColumn(col_id, name)
        self.columns[col_id] = column
        self.container.pack_start(column, True, True, 0)

        # Cria widgets dentro da coluna
        for widget_id in col_config.get('widgets', []):
            widget_data = widgets_config.get(widget_id, {})
            if widget_data:
                widget_type = widget_data.get('type', 'terminal')
                widget = column.add_widget(widget_type, widget_data)
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
        column = WidgetColumn(col_id, name)
        self.columns[col_id] = column
        self.container.pack_start(column, True, True, 0)
        column.show_all()
        return col_id

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
                'name': column.column_id,
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

    def __init__(self, app):
        super().__init__(application=app, title="Terminal Multi-Pane")
        self.set_default_size(1600, 900)
        self.maximize()
        self._dnd_widget = None  # Para drag-and-drop

        # Transparência Global GTK (mantida)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Não destruir ao fechar, apenas esconder
        self.connect('delete-event', self._on_delete)

        # Atalhos globais
        self.connect('key-press-event', self._on_key_press)

        # Layout Manager
        self._build_ui()

    def _build_ui(self) -> None:
        """Constrói a interface usando DynamicLayoutManager."""
        overlay = Gtk.Overlay()
        self.add(overlay)

        # Container principal (homogeneous para colunas iguais)
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_homogeneous(True)
        main_box.get_style_context().add_class('main-container')
        overlay.add(main_box)

        # Layout Manager para gerenciar colunas e widgets dinamicamente
        self.layout_manager = DynamicLayoutManager(main_box)

        # Carregar layout padrão (sem delays hardcodes!)
        self.layout_manager.load_layout(DEFAULT_LAYOUT)

    def _on_key_press(self, window, event) -> bool:
        """Teclas globais."""
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        if event.keyval == Gdk.KEY_F11:
            if self.is_maximized():
                self.fullscreen()
            else:
                self.unfullscreen()
                self.maximize()
            return True
        return False

    def _on_delete(self, window, event) -> bool:
        """Esconder em vez de destruir."""
        self.hide()
        return True  # Impede destruição


# ============================================================================
# APLICAÇÃO: TerminalMultiPaneApp (Mantida)
# ============================================================================

class TerminalMultiPaneApp(Gtk.Application):
    """Aplicação principal."""

    def __init__(self):
        super().__init__(application_id='com.user.terminal-multi-pane')
        self.window = None

    def do_startup(self):
        """Chamado uma vez quando a aplicação inicia."""
        Gtk.Application.do_startup(self)
        self._apply_css()

    def do_activate(self):
        """Chamado quando a aplicação é ativada (abrir janela)."""
        if self.window:
            self.window.present()
            self.window.show_all()
            return

        self.window = TerminalMultiPaneWindow(self)
        self.window.show_all()

    def _apply_css(self):
        """Aplica estilos CSS (mantidos idênticos ao original)."""
        css = """
            window {
                background-color: transparent;
            }

            .main-container {
                background-color: rgba(30, 30, 30, 0.85);
            }

            .terminal-column {
                background-color: transparent;
                border-right: 1px solid rgba(255, 255, 255, 0.05);
                margin: 0;
                transition: all 0.2s ease;
            }

            .terminal-column:last-child {
                border-right: none;
            }

            .terminal-column.drop-hover {
                background-color: rgba(60, 60, 60, 0.3);
            }

            .column-header {
                background-color: transparent;
                padding: 10px 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }

            .column-label {
                color: rgba(230, 230, 230, 0.9);
                font-weight: 600;
                font-size: 0.9em;
            }

            .add-button {
                min-width: 28px;
                min-height: 28px;
                padding: 0;
                border-radius: 4px;
                background-color: transparent;
                color: rgba(200, 200, 200, 0.7);
            }

            .add-button:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
            }

            .terminal-wrapper {
                background-color: transparent;
                border: none;
                margin: 4px 8px;
            }

            .terminal-header {
                background-color: transparent;
                padding: 6px 8px;
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
                border-radius: 4px;
            }

            .close-term-button:hover {
                color: rgba(255, 255, 255, 0.9);
                background-color: rgba(255, 255, 255, 0.15);
            }

            .close-button {
                min-width: 100px;
                min-height: 32px;
                padding: 0 14px;
                border-radius: 6px;
                background-color: rgba(50, 50, 50, 0.6);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .close-button:hover {
                background-color: rgba(70, 70, 70, 0.8);
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


# ============================================================================
# APP INDICATOR (Mantido)
# ============================================================================

def create_indicator(app_instance) -> Optional[AyatanaAppIndicator3.Indicator]:
    """Cria o ícone na barra superior usando AyatanaAppIndicator3."""
    try:
        indicator = AyatanaAppIndicator3.Indicator.new(
            'terminal-multi-pane',
            'utilities-terminal',
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        indicator.set_title("Terminal Multi-Pane")

        menu = Gtk.Menu()

        open_item = Gtk.MenuItem(label="Abrir Terminal Multi-Pane")
        open_item.connect('activate', lambda w: app_instance.activate())
        menu.append(open_item)

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
    indicator_holder = [None]

    def on_app_startup(application):
        indicator_holder[0] = create_indicator(application)

    app.connect('startup', on_app_startup)

    print("Iniciando Terminal Multi-Pane (Fase 1 Refatorado)...", file=sys.stderr)
    app.run(None)

    # Cleanup
    if indicator_holder[0]:
        indicator_holder[0].set_status(AyatanaAppIndicator3.IndicatorStatus.PASSIVE)


if __name__ == '__main__':
    main()
