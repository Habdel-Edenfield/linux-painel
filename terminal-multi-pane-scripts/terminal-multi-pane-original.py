#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal Multi-Pane Manager
Aplicação GTK3 com indicador na barra para gerenciar múltiplos terminais
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
gi.require_version('Vte', '2.91')

from gi.repository import Gtk, AyatanaAppIndicator3, Vte, GLib, Gdk, Pango
import sys
import os
import signal

# Detectar shell padrão
SHELL = os.environ.get('SHELL', '/bin/bash')


class TerminalWrapper(Gtk.Box):
    """Wrapper para um terminal VTE com header e controles"""

    def __init__(self, column):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.column = column
        self.terminal = None

        # Header do terminal
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.get_style_context().add_class('terminal-header')

        # Drag handle
        drag_handle = Gtk.Label(label="⋮⋮")
        drag_handle.get_style_context().add_class('drag-handle')
        header.pack_start(drag_handle, False, False, 4)

        # Título
        title = Gtk.Label(label=os.path.basename(SHELL))
        title.get_style_context().add_class('terminal-title')
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header.pack_start(title, True, True, 0)

        # Botão fechar
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class('close-term-button')
        close_btn.set_tooltip_text("Fechar terminal")
        close_btn.connect('clicked', self.on_close)
        header.pack_end(close_btn, False, False, 0)

        self.pack_start(header, False, False, 0)

        # Container para o terminal VTE
        self.terminal_container = Gtk.Box()
        self.terminal_container.set_vexpand(True)
        self.terminal_container.set_hexpand(True)
        self.pack_start(self.terminal_container, True, True, 0)

        self.get_style_context().add_class('terminal-wrapper')

        # Menu de contexto (botão direito)
        self.connect('button-press-event', self._on_button_press)

        # Iniciar o terminal
        self._start_terminal()

    def _start_terminal(self):
        """Inicia o terminal VTE"""
        self.terminal = Vte.Terminal()
        self.terminal.set_scrollback_lines(-1)
        self.terminal.set_audible_bell(False)

        # Fonte
        font_desc = Pango.FontDescription.from_string("Monospace 11")
        self.terminal.set_font(font_desc)

        # Cores (GNOME Terminal Native)
        fg = Gdk.RGBA()
        fg.parse("#d3d7cf") # Cinza claro nativo (Texto)
        bg = Gdk.RGBA()
        # O Fundo transparente exato que define a estética do terminal GNOME:
        bg.parse("rgba(30, 30, 30, 0.85)") 
        self.terminal.set_color_foreground(fg)
        self.terminal.set_color_background(bg)

        # Spawnar shell
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            None,       # working directory
            [SHELL],    # command
            None,       # environment
            GLib.SpawnFlags.SEARCH_PATH,
            None, None
        )

        self.terminal.set_vexpand(True)
        self.terminal.set_hexpand(True)
        self.terminal_container.pack_start(self.terminal, True, True, 0)

        # Atalho Ctrl+Shift+W para fechar
        self.terminal.connect('key-press-event', self._on_key_press)

    def _on_key_press(self, widget, event):
        """Atalhos de teclado"""
        state = event.state & Gtk.accelerator_get_default_mod_mask()
        ctrl_shift = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK

        if state == ctrl_shift and event.keyval == Gdk.KEY_w:
            self.on_close(None)
            return True
        return False

    def _on_button_press(self, widget, event):
        """Menu de contexto com botão direito"""
        if event.button == 3:  # Botão direito
            menu = Gtk.Menu()

            items = [
                ("Copiar", self._on_copy),
                ("Colar", self._on_paste),
                ("Limpar", self._on_clear),
                None,  # Separador
                ("Fechar terminal", self.on_close),
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

    def _on_copy(self, widget):
        if self.terminal and self.terminal.get_has_selection():
            self.terminal.copy_clipboard_format(Vte.Format.TEXT)

    def _on_paste(self, widget):
        if self.terminal:
            self.terminal.paste_clipboard()

    def _on_clear(self, widget):
        if self.terminal:
            self.terminal.reset(True, True)

    def on_close(self, button):
        """Fecha e remove este terminal"""
        parent = self.get_parent()
        if parent:
            parent.remove(self)
        if self.terminal:
            self.terminal = None
        self.destroy()


class TerminalColumn(Gtk.Box):
    """Uma coluna que contém múltiplos terminais"""

    def __init__(self, name):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_hexpand(True)

        # Header da coluna
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class('column-header')

        label = Gtk.Label(label=name)
        label.get_style_context().add_class('column-label')
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        header.pack_start(label, True, True, 8)

        # Botão +
        add_btn = Gtk.Button(label="+")
        add_btn.get_style_context().add_class('add-button')
        add_btn.set_tooltip_text("Adicionar terminal")
        add_btn.connect('clicked', lambda b: self.add_terminal())
        header.pack_end(add_btn, False, False, 4)

        self.pack_start(header, False, False, 0)

        # Scroll container para os terminais
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.pack_start(scroll, True, True, 0)

        self.terminal_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.terminal_box.set_margin_start(2)
        self.terminal_box.set_margin_end(2)
        self.terminal_box.set_margin_bottom(2)
        scroll.add(self.terminal_box)

        self.get_style_context().add_class('terminal-column')

        # Setup drag-and-drop (GTK3 proper API)
        self._setup_dnd()

    def _setup_dnd(self):
        """Configura drag-and-drop usando GTK3 APIs"""
        # Este widget é um drop target
        target_entry = Gtk.TargetEntry.new("terminal-wrapper", Gtk.TargetFlags.SAME_APP, 0)
        self.terminal_box.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [target_entry],
            Gdk.DragAction.MOVE
        )
        self.terminal_box.connect('drag-data-received', self._on_drag_data_received)
        self.terminal_box.connect('drag-motion', self._on_drag_motion)
        self.terminal_box.connect('drag-leave', self._on_drag_leave)

    def _on_drag_motion(self, widget, context, x, y, time):
        """Highlight visual ao arrastar por cima"""
        self.get_style_context().add_class('drop-hover')
        Gdk.drag_status(context, Gdk.DragAction.MOVE, time)
        return True

    def _on_drag_leave(self, widget, context, time):
        """Remove highlight"""
        self.get_style_context().remove_class('drop-hover')

    def _on_drag_data_received(self, widget, context, x, y, data, info, time):
        """Recebe um terminal arrastado"""
        self.get_style_context().remove_class('drop-hover')
        # O terminal foi movido via DnD - dados contém o ID
        terminal_id = data.get_text()
        if terminal_id and hasattr(self.get_toplevel(), '_dnd_terminal'):
            term = self.get_toplevel()._dnd_terminal
            if term:
                old_parent = term.get_parent()
                if old_parent:
                    old_parent.remove(term)
                self.terminal_box.pack_start(term, True, True, 0)
                term.show_all()
            context.finish(True, False, time)
        else:
            context.finish(False, False, time)

    def add_terminal(self):
        """Adiciona um terminal à coluna"""
        wrapper = TerminalWrapper(self)
        self.terminal_box.pack_start(wrapper, True, True, 0)

        # Configurar drag source no header do wrapper
        header = wrapper.get_children()[0]  # Primeiro child é o header
        target_entry = Gtk.TargetEntry.new("terminal-wrapper", Gtk.TargetFlags.SAME_APP, 0)
        header.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK,
            [target_entry],
            Gdk.DragAction.MOVE
        )
        header.drag_source_set_icon_name('utilities-terminal')
        header.connect('drag-begin', self._on_drag_begin, wrapper)
        header.connect('drag-data-get', self._on_drag_data_get, wrapper)

        wrapper.show_all()
        return wrapper

    def _on_drag_begin(self, widget, context, wrapper):
        """Quando começa a arrastar um terminal"""
        wrapper.get_style_context().add_class('dragging')
        # Armazenar referência no toplevel para o drop target encontrar
        self.get_toplevel()._dnd_terminal = wrapper

    def _on_drag_data_get(self, widget, context, data, info, time, wrapper):
        """Fornece dados do drag"""
        data.set_text(str(id(wrapper)), -1)


class TerminalMultiPaneWindow(Gtk.ApplicationWindow):
    """Janela principal com 3 colunas de terminais"""

    def __init__(self, app):
        super().__init__(application=app, title="Terminal Multi-Pane")
        self.set_default_size(1600, 900)
        self.maximize()
        self._dnd_terminal = None  # Para drag-and-drop

        # Transparência Global GTK (Permite renderizar RGBA/Vidro na raiz)
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Não destruir ao fechar, apenas esconder
        self.connect('delete-event', self._on_delete)

        # Atalhos globais
        self.connect('key-press-event', self._on_key_press)

        # Layout
        self._build_ui()

    def _build_ui(self):
        """Constrói a interface"""
        overlay = Gtk.Overlay()
        self.add(overlay)

        # 3 colunas horizontais
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_box.set_homogeneous(True)
        main_box.get_style_context().add_class('main-container')
        overlay.add(main_box)

        self.col1 = TerminalColumn("Painel 1")
        self.col2 = TerminalColumn("Painel 2")
        self.col3 = TerminalColumn("Painel 3")

        main_box.pack_start(self.col1, True, True, 0)
        main_box.pack_start(self.col2, True, True, 0)
        main_box.pack_start(self.col3, True, True, 0)

        # Botão fechar flutuante (Removido por que conflita com os ícones de janela nativos do GNOME)
        pass

        # Adicionar um terminal em cada coluna (com delay para estabilidade)
        # É ESSENCIAL retornar 'False' nas callbacks do GLib.timeout_add, 
        # caso contrário o GLib entrará num loop infinito reagendando a função eternamente.
        GLib.timeout_add(100, lambda: self.col1.add_terminal() and False)
        GLib.timeout_add(200, lambda: self.col2.add_terminal() and False)
        GLib.timeout_add(300, lambda: self.col3.add_terminal() and False)

    def _on_key_press(self, window, event):
        """Teclas globais"""
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

    def _on_delete(self, window, event):
        """Esconder em vez de destruir"""
        self.hide()
        return True  # Impede destruição


class TerminalMultiPaneApp(Gtk.Application):
    """Aplicação principal"""

    def __init__(self):
        super().__init__(application_id='com.user.terminal-multi-pane')
        self.window = None

    def do_startup(self):
        """Chamado uma vez quando a aplicação inicia"""
        Gtk.Application.do_startup(self)
        self._apply_css()

    def do_activate(self):
        """Chamado quando a aplicação é ativada (abrir janela)"""
        if self.window:
            self.window.present()
            self.window.show_all()
            return

        self.window = TerminalMultiPaneWindow(self)
        self.window.show_all()

    def _apply_css(self):
        """Aplica estilos CSS"""
        css = """
            /* Reset Global de Fundo de Cima a Baixo com Alpha. 
               Aqui matamos a caixa preta e ativamos a transparencia global */
            window {
                background-color: transparent;
            }

            .main-container {
                background-color: rgba(30, 30, 30, 0.85);
            }

            .terminal-column {
                background-color: transparent;
                border-right: 1px solid rgba(255, 255, 255, 0.05); /* Separador de paineis invisivel */
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
                /* Cabecalho fundido com o resto (estetica Native Frameless) */
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
                /* Sem bordas engessadas, fluindo com o fundo central */
                background-color: transparent;
                border: none;
                margin: 4px 8px;
            }

            .terminal-header {
                /* Abas do wrapper imitando a discricao do GNOME Console */
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


# ─── App Indicator ──────────────────────────────────────────────

def create_indicator(app_instance):
    """Cria o ícone na barra superior usando AyatanaAppIndicator3"""
    try:
        indicator = AyatanaAppIndicator3.Indicator.new(
            'terminal-multi-pane',
            'utilities-terminal',
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        indicator.set_title("Terminal Multi-Pane")

        # Menu do indicador
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

        # Ação ao clicar no ícone (secondary activate = clique esquerdo)
        indicator.set_secondary_activate_target(open_item)

        print("AppIndicator criado com sucesso!", file=sys.stderr)
        return indicator

    except Exception as e:
        print(f"Erro ao criar AppIndicator: {e}", file=sys.stderr)
        return None


# ─── Main ──────────────────────────────────────────────────────

def main():
    # Permitir Ctrl+C para fechar
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = TerminalMultiPaneApp()

    # O indicador precisa ser criado DEPOIS do app existir
    # mas ANTES de app.run() pois o GTK main loop começa em run()
    # Solução: criar no do_startup via idle_add
    indicator_holder = [None]

    original_startup = app.do_startup

    def on_startup_with_indicator(self_app):
        original_startup()
        # Criar indicador dentro do loop GTK
        indicator_holder[0] = create_indicator(app)

    # Override via connect
    def on_app_startup(application):
        indicator_holder[0] = create_indicator(application)

    app.connect('startup', on_app_startup)

    print("Iniciando Terminal Multi-Pane...", file=sys.stderr)
    app.run(None)

    # Cleanup
    if indicator_holder[0]:
        indicator_holder[0].set_status(AyatanaAppIndicator3.IndicatorStatus.PASSIVE)


if __name__ == '__main__':
    main()
