import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';
import GObject from 'gi://GObject';

import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as Slider from 'resource:///org/gnome/shell/ui/slider.js';

// Importar BrightnessModule
import { BrightnessModule } from './BrightnessModule.js';


const SystemToolsButton = GObject.registerClass(
    class SystemToolsButton extends PanelMenu.Button {
        _init(settings) {
            super._init(0.5, 'System Tools');

            // Armazenar settings
            this._settings = settings;

            // Instanciar BrightnessModule
            try {
                this._brightnessModule = new BrightnessModule();
                console.log('[SystemTools] BrightnessModule initialized');
            } catch (e) {
                console.error('[SystemTools] Failed to initialize BrightnessModule:', e.message);
                this._brightnessModule = null;
            }

            // Timer para polling do brilho
            this._pollTimerId = null;

            // Container para o conteúdo
            this._box = new St.BoxLayout({
                style_class: 'panel-status-menu-box',
            });

            // Label principal (mostra brilho atual)
            this._label = new St.Label({
                text: '🔆',
                y_align: Clutter.ActorAlign.CENTER
            });

            this._box.add_child(this._label);
            this.add_child(this._box);

            // Atualizar label com brilho atual
            this._updateBrightnessLabel();

            // Construir menu
            this._buildMenu();

            // Iniciar polling do brilho (para atualização em tempo real)
            this._startBrightnessPolling();

            console.log('[SystemTools] Extension loaded - FASE 6 (Slider + Profiles + Polling) complete');
        }

        // Método para ler settings com fallback
        _getSetting(key, type, defaultValue) {
            if (!this._settings) {
                console.log(`[SystemTools] Settings not available, using fallback for ${key}: ${defaultValue}`);
                return defaultValue;
            }

            try {
                switch (type) {
                    case 'boolean':
                        return this._settings.get_boolean(key);
                    case 'string':
                        return this._settings.get_string(key);
                    case 'int':
                        return this._settings.get_int(key);
                    case 'double':
                        return this._settings.get_double(key);
                    case 'variant':
                        return this._settings.get_value(key).deep_unpack();
                    default:
                        console.log(`[SystemTools] Unknown type ${type} for key ${key}, using fallback`);
                        return defaultValue;
                }
            } catch (e) {
                console.error(`[SystemTools] Error reading setting ${key}: ${e.message}`);
                return defaultValue;
            }
        }

        // Atualizar label principal com brilho atual
        _updateBrightnessLabel() {
            if (!this._brightnessModule) {
                this._label.text = '🔆';
                return;
            }

            const showBrightnessInPanel = this._getSetting('show-brightness-in-panel', 'boolean', true);

            if (!showBrightnessInPanel) {
                this._label.text = '🔆';
                return;
            }

            const percent = this._brightnessModule.getBrightnessPercent();
            if (percent !== null) {
                this._label.text = `🔆 ${percent}%`;
            } else {
                this._label.text = '🔆 ???';
            }
        }

        // Iniciar polling do brilho (para atualização em tempo real)
        _startBrightnessPolling() {
            const pollInterval = this._getSetting('brightness-poll-interval', 'int', 5) * 1000;

            if (this._pollTimerId) {
                GLib.source_remove(this._pollTimerId);
            }

            this._pollTimerId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, pollInterval, () => {
                this._updateBrightnessLabel();
                this._updateSliderValue();
                return GLib.SOURCE_CONTINUE;
            });

            console.log(`[SystemTools] Polling started (interval: ${pollInterval}ms)`);
        }

        // Parar polling
        _stopBrightnessPolling() {
            if (this._pollTimerId) {
                GLib.source_remove(this._pollTimerId);
                this._pollTimerId = null;
                console.log('[SystemTools] Polling stopped');
            }
        }

        // Construir slider de brilho
        _buildBrightnessSlider() {
            // Criar slider (0 a 1)
            this._brightnessSlider = new Slider.Slider(0);
            this._brightnessSlider.x_expand = true;
            this._brightnessSlider.y_align = Clutter.ActorAlign.CENTER;

            // Definir valor atual do slider
            const currentPercent = this._brightnessModule ? this._brightnessModule.getBrightnessPercent() : 80;
            if (currentPercent !== null) {
                this._brightnessSlider.value = currentPercent / 100;
            }

            // Quando slider mudar, atualizar brilho
            this._brightnessSlider.connect('notify::value', () => {
                if (this._brightnessModule) {
                    const percent = Math.round(this._brightnessSlider.value * 100);
                    this._brightnessModule.setBrightnessPercent(percent);
                    this._updateBrightnessLabel();
                }
            });

            // Criar item de menu para o slider
            const sliderItem = new PopupMenu.PopupBaseMenuItem({
                activate: false,
                can_focus: false,
            });
            sliderItem.add_child(this._brightnessSlider);

            return sliderItem;
        }

        // Atualizar valor do slider
        _updateSliderValue() {
            if (!this._brightnessSlider || !this._brightnessModule) {
                return;
            }

            const percent = this._brightnessModule.getBrightnessPercent();
            if (percent !== null) {
                // Evitar loop: só atualizar se a diferença for significativa
                const currentValue = this._brightnessSlider.value;
                const newValue = percent / 100;

                if (Math.abs(currentValue - newValue) > 0.01) {
                    this._brightnessSlider.value = newValue;
                }
            }
        }

        // Construir seção de profiles
        _buildProfilesSection() {
            // Header da seção de profiles
            const profilesHeader = new PopupMenu.PopupMenuItem('⚙️ Perfis');
            profilesHeader.setSensitive(false);
            this.menu.addMenuItem(profilesHeader);

            // Obter profiles do schema
            const profiles = this._getSetting('brightness-profiles', 'variant', {
                'normal': '100',
                'comfort': '80',
                'dark': '70'
            });

            // Definir ícones para cada profile
            const profileIcons = {
                'normal': '☀️',
                'comfort': '🌗',
                'dark': '🌑'
            };

            // Criar botões para cada profile
            for (const [name, value] of Object.entries(profiles)) {
                const icon = profileIcons[name] || '💡';
                const percent = parseInt(value);
                const label = `${icon} ${name.charAt(0).toUpperCase() + name.slice(1)} (${percent}%)`;

                const profileItem = new PopupMenu.PopupMenuItem(label);
                profileItem.connect('activate', () => {
                    if (this._brightnessModule) {
                        this._brightnessModule.setBrightnessPercent(percent);
                        this._updateBrightnessLabel();
                        this._updateSliderValue();
                    }
                });
                this.menu.addMenuItem(profileItem);
            }
        }

        _buildMenu() {
            const showBrightness = this._getSetting('show-brightness', 'boolean', true);

            if (!showBrightness) {
                console.log('[SystemTools] Brightness section hidden by setting');
                return;
            }

            // Header da seção de brilho
            const brightnessHeader = new PopupMenu.PopupMenuItem('🔆 Controle de Brilho');
            brightnessHeader.setSensitive(false);
            this.menu.addMenuItem(brightnessHeader);

            // Mostrar brilho atual
            const currentPercent = this._brightnessModule ? this._brightnessModule.getBrightnessPercent() : null;
            const currentBrightnessItem = new PopupMenu.PopupMenuItem(
                `Atual: ${currentPercent !== null ? currentPercent + '%' : 'Desconhecido'}`
            );
            currentBrightnessItem.setSensitive(false);
            this.menu.addMenuItem(currentBrightnessItem);

            // Adicionar slider (ajuste fino)
            const sliderItem = this._buildBrightnessSlider();
            this.menu.addMenuItem(sliderItem);

            // Separador
            this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

            // Seção de profiles
            this._buildProfilesSection();
        }

        destroy() {
            this._stopBrightnessPolling();
            super.destroy();
        }
    });


export default class SystemToolsExtension extends Extension {
    enable() {
        try {
            console.log('[SystemTools] Enabling extension...');

            // Carregar settings com tratamento de erros
            let settings = null;
            try {
                settings = this.getSettings();
                console.log('[SystemTools] Settings loaded successfully');
            } catch (e) {
                console.warn(`[SystemTools] Could not load settings: ${e.message}`);
            }

            this._indicator = new SystemToolsButton(settings);
            Main.panel.addToStatusArea(this.uuid, this._indicator, 0, 'right');
            console.log('[SystemTools] Extension enabled successfully');
        } catch (e) {
            console.error(`[SystemTools] Error enabling extension: ${e}`);
            console.error(`[SystemTools] Stack trace: ${e.stack}`);
        }
    }

    disable() {
        try {
            console.log('[SystemTools] Disabling extension...');
            if (this._indicator) {
                this._indicator.destroy();
                this._indicator = null;
            }
            console.log('[SystemTools] Extension disabled successfully');
        } catch (e) {
            console.error(`[SystemTools] Error disabling extension: ${e}`);
        }
    }
}
