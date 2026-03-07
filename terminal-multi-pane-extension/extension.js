import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as Util from 'resource:///org/gnome/shell/misc/util.js';

const APPLICATION_NAME = 'Terminal Multi-Pane';
const DEFAULT_APP_PATH = ['.local', 'share', 'terminal-multi-pane', 'terminal-multi-pane.py'];

const TerminalMultiPaneButton = GObject.registerClass(
class TerminalMultiPaneButton extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, APPLICATION_NAME, false);

        this._extension = extension;
        this.add_style_class_name('terminal-multi-pane-panel-button');

        const box = new St.BoxLayout({
            style_class: 'panel-status-menu-box terminal-multi-pane-panel-box',
        });

        const icon = new St.Icon({
            gicon: extension.getPanelIcon(),
            style_class: 'system-status-icon terminal-multi-pane-icon',
        });

        box.add_child(icon);
        this.add_child(box);

        this._buildMenu();

        this.connect('button-press-event', (_actor, event) => {
            const button = event.get_button();

            if (button === Clutter.BUTTON_PRIMARY) {
                this._extension.runAppCommand('--toggle');
                return Clutter.EVENT_STOP;
            }

            if (button === Clutter.BUTTON_MIDDLE) {
                this._extension.runAppCommand('--new-terminal');
                return Clutter.EVENT_STOP;
            }

            if (button === Clutter.BUTTON_SECONDARY) {
                this.menu.toggle();
                return Clutter.EVENT_STOP;
            }

            return Clutter.EVENT_PROPAGATE;
        });
    }

    _buildMenu() {
        this.menu.removeAll();

        this._addMenuItem('Abrir multi-pane', 'utilities-terminal-symbolic', '--show');
        this._addMenuItem('Novo terminal', 'list-add-symbolic', '--new-terminal');
        this._addMenuItem('Reabrir zerado', 'view-refresh-symbolic', '--reopen');
        this._addMenuItem('Fechar workspace', 'window-close-symbolic', '--hide');
    }

    _addMenuItem(label, iconName, command) {
        const item = new PopupMenu.PopupImageMenuItem(label, iconName);
        item.add_style_class_name('terminal-multi-pane-menu-item');
        item.connect('activate', () => this._extension.runAppCommand(command));
        this.menu.addMenuItem(item);
    }
});

export default class TerminalMultiPaneExtension extends Extension {
    enable() {
        this._indicator = new TerminalMultiPaneButton(this);
        Main.panel.addToStatusArea(this.uuid, this._indicator, 0, 'right');
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }

    getPanelIcon() {
        const iconPath = GLib.build_filenamev([
            this.path,
            'icons',
            'terminal-multi-pane-symbolic.svg',
        ]);
        const file = Gio.File.new_for_path(iconPath);
        return new Gio.FileIcon({file});
    }

    runAppCommand(command) {
        const appPath = this._resolveAppPath();

        if (!GLib.file_test(appPath, GLib.FileTest.EXISTS)) {
            this._notifyError(`App não encontrado em ${appPath}`);
            return;
        }

        try {
            Util.spawn(['python3', appPath, command]);
        } catch (error) {
            this._notifyError(error.message ?? String(error));
        }
    }

    _resolveAppPath() {
        const settings = this.getSettings('org.gnome.shell.extensions.terminal-multi-pane');
        const configuredPath = settings.get_string('app-path').trim();

        if (configuredPath && GLib.file_test(configuredPath, GLib.FileTest.EXISTS))
            return configuredPath;

        return GLib.build_filenamev([GLib.get_home_dir(), ...DEFAULT_APP_PATH]);
    }

    _notifyError(message) {
        if (typeof Main.notifyError === 'function')
            Main.notifyError(APPLICATION_NAME, message);
        else
            Main.notify(APPLICATION_NAME, message);
    }
}
