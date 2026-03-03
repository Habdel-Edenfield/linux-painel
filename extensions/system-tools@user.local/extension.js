import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';

import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

import {Extension, gettext as _} from 'resource:///org/gnome/shell/extensions/extension.js';

let systemToolsMenu;

/**
 * BrightnessModule - Handles brightness control via xrandr
 */
var BrightnessModule = GObject.registerClass({
    GTypeName: 'BrightnessModule',
    Signals: {
        'brightness-changed': { param_types: [GObject.TYPE_DOUBLE] },
    },
}, class BrightnessModule extends GObject.Object {
    _init(settings, extensionObject) {
        super._init();

        this._settings = settings;
        this._extensionObject = extensionObject;
        this._currentBrightness = 100;
        this._monitorOutput = 'DP-2'; // Default monitor, will be detected
        this._pollTimeout = null;
        this._pollInterval = 5;

        // Detect primary monitor
        this._detectMonitor();

        // Get current brightness
        this._currentBrightness = this._getCurrentBrightness();
    }

    /**
     * Detect primary monitor output name
     */
    _detectMonitor() {
        try {
            let [success, stdout, stderr] = GLib.spawn_command_line_sync(
                'xrandr --query | grep " connected primary" | cut -d" " -f1'
            );
            if (success && stdout) {
                let output = stdout.toString().trim();
                if (output) {
                    this._monitorOutput = output;
                    log('[System Tools] Detected monitor: ' + this._monitorOutput);
                }
            }
        } catch (e) {
            log('[System Tools] Error detecting monitor: ' + e.message);
        }
    }

    /**
     * Get current brightness from xrandr
     */
    _getCurrentBrightness() {
        try {
            let [success, stdout, stderr] = GLib.spawn_command_line_sync(
                `xrandr --verbose | grep -i brightness | head -n 1 | cut -d':' -f2 | awk '{print $1}'`
            );

            if (success && stdout) {
                let brightnessStr = stdout.toString().trim();
                let brightness = parseFloat(brightnessStr);
                if (!isNaN(brightness)) {
                    // Convert to percentage (0-100)
                    this._currentBrightness = Math.round(brightness * 100);
                    log('[System Tools] Current brightness: ' + this._currentBrightness + '%');
                    return this._currentBrightness;
                }
            }
        } catch (e) {
            log('[System Tools] Error getting brightness: ' + e.message);
        }

        return this._currentBrightness;
    }

    /**
     * Set brightness using xrandr
     */
    setBrightness(value, gamma = null) {
        try {
            // Clamp value between 10 and 100
            value = Math.max(10, Math.min(100, value));

            // Convert to decimal (0.1 - 1.0)
            let brightnessValue = value / 100;

            let args = ['xrandr', '--output', this._monitorOutput, '--brightness', brightnessValue.toString()];

            // Add gamma if specified
            if (gamma) {
                args.push('--gamma', gamma);
            }

            GLib.spawn_async(null, args, null, GLib.SpawnFlags.SEARCH_PATH, null);

            this._currentBrightness = value;
            log('[System Tools] Set brightness to ' + value + '%');

            // Emit signal
            this.emit('brightness-changed', value);

            return true;
        } catch (e) {
            log('[System Tools] Error setting brightness: ' + e.message);
            return false;
        }
    }

    /**
     * Get brightness profiles from settings
     */
    getProfiles() {
        try {
            return this._settings.get_value('brightness-profiles').deep_unpack();
        } catch (e) {
            log('[System Tools] Error getting profiles: ' + e.message);
            return { 'normal': 100, 'comfort': 80, 'dark': 70 };
        }
    }

    /**
     * Apply a brightness profile
     */
    applyProfile(profileName) {
        let profiles = this.getProfiles();

        if (profileName in profiles) {
            let profile = profiles[profileName];
            let brightness = profile.brightness || 100;
            let gamma = profile.gamma || null;

            if (typeof profile === 'number') {
                // Legacy format: just brightness value
                brightness = profile;
            } else if (typeof profile === 'string') {
                // String format: parse brightness value
                brightness = parseInt(profile);
            }

            log('[System Tools] Applying profile: ' + profileName + ' (brightness: ' + brightness + '%)');
            return this.setBrightness(brightness, gamma);
        }

        return false;
    }

    /**
     * Start polling for brightness changes
     */
    startPolling() {
        if (this._pollTimeout) {
            return; // Already polling
        }

        this._pollInterval = this._settings.get_int('update-time');

        log('[System Tools] Starting brightness polling (interval: ' + this._pollInterval + 's)');

        this._pollTimeout = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            this._pollInterval,
            this._pollBrightness.bind(this)
        );
    }

    /**
     * Stop polling for brightness changes
     */
    stopPolling() {
        if (this._pollTimeout) {
            GLib.source_remove(this._pollTimeout);
            this._pollTimeout = null;
            log('[System Tools] Stopped brightness polling');
        }
    }

    /**
     * Poll brightness (called by timeout)
     */
    _pollBrightness() {
        let oldBrightness = this._currentBrightness;
        let newBrightness = this._getCurrentBrightness();

        if (oldBrightness !== newBrightness) {
            log('[System Tools] Brightness changed: ' + oldBrightness + '% -> ' + newBrightness + '%');
            this.emit('brightness-changed', newBrightness);
        }

        return GLib.SOURCE_CONTINUE;
    }

    /**
     * Get current brightness value
     */
    getCurrentBrightness() {
        return this._currentBrightness;
    }

    /**
     * Cleanup resources
     */
    destroy() {
        this.stopPolling();
    }
});

/**
 * SystemToolsMenuButton - Main widget for System Tools extension
 * Vitals-inspired design with unified brightness and obsidian controls
 */
var SystemToolsMenuButton = GObject.registerClass({
    GTypeName: 'SystemToolsMenuButton',
}, class SystemToolsMenuButton extends PanelMenu.Button {
    _init(extensionObject) {
        super._init(Clutter.ActorAlign.FILL);

        this._extensionObject = extensionObject;
        this._settings = extensionObject.getSettings();

        // Icon paths for different themes
        this._sensorsIconPathPrefix = ['/icons/original/', '/icons/gnome/'];

        // Module containers
        this._brightnessButton = null;
        this._obsidianButton = null;
        this._menuLayout = null;

        // Hot sensor labels
        this._brightnessHotLabel = null;

        // Create horizontal layout for panel widgets
        this._menuLayout = new St.BoxLayout({
            vertical: false,
            clip_to_allocation: true,
            x_align: Clutter.ActorAlign.START,
            y_align: Clutter.ActorAlign.CENTER,
            reactive: true,
            x_expand: true
        });

        // Initialize modules
        this._brightnessModule = new BrightnessModule(this._settings, this._extensionObject);

        this._buildPanel();
        this.add_child(this._menuLayout);

        // Settings change signals
        this._settingChangedSignals = [];
        this._addSettingChangedSignal('show-brightness', this._updateVisibility.bind(this));
        this._addSettingChangedSignal('show-obsidian', this._updateVisibility.bind(this));
        this._addSettingChangedSignal('icon-style', this._iconStyleChanged.bind(this));
        this._addSettingChangedSignal('update-time', this._updatePollInterval.bind(this));

        // Connect brightness change signal
        this._brightnessModule.connect('brightness-changed', this._updateBrightnessHotSensor.bind(this));

        // Build menu
        this._buildMenu();

        // Start brightness polling
        this._brightnessModule.startPolling();

        // Initial updates
        this._updateVisibility();
        this._updateBrightnessHotSensor();
    }

    /**
     * Build panel widgets
     */
    _buildPanel() {
        // Brightness widget with hot sensor
        this._brightnessButton = new St.Button({
            style_class: 'vitals-panel-icon',
            reactive: true,
            can_focus: false,
            track_hover: false,
        });

        let brightnessIcon = this._createIcon('brightness-symbolic.svg');
        this._brightnessButton.set_child(brightnessIcon);
        this._brightnessButton.connect('clicked', () => {
            this.menu.toggle();
        });

        this._menuLayout.add_child(this._brightnessButton);

        // Hot sensor label for brightness
        this._brightnessHotLabel = new St.Label({
            style_class: 'vitals-panel-label hot-sensor-value',
            text: '\u2026', // ... loading indicator
            y_expand: true,
            y_align: Clutter.ActorAlign.CENTER
        });

        this._menuLayout.add_child(this._brightnessHotLabel);

        // Obsidian widget placeholder
        this._obsidianButton = new St.Button({
            style_class: 'vitals-panel-icon',
            reactive: true,
            can_focus: false,
            track_hover: false,
        });

        let obsidianIcon = this._createIcon('obsidian-symbolic.svg');
        this._obsidianButton.set_child(obsidianIcon);
        this._obsidianButton.connect('clicked', () => {
            this.menu.toggle();
        });

        this._menuLayout.add_child(this._obsidianButton);

        // Add spacing between widgets
        let spacer = new St.Bin({
            style_class: 'popup-menu-item',
            x_align: St.Align.START,
            y_align: St.Align.CENTER,
            reactive: false,
            can_focus: false,
            track_hover: false
        });

        this._menuLayout.add_child(spacer);
    }

    /**
     * Build menu structure
     */
    _buildMenu() {
        // Brightness section
        if (this._settings.get_boolean('show-brightness')) {
            this._buildBrightnessSection();
        }

        // Obsidian section
        if (this._settings.get_boolean('show-obsidian')) {
            this._buildObsidianSection();
        }

        // Add separator
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Preferences button
        let prefsButton = new PopupMenu.PopupMenuItem(_('Preferences'));
        prefsButton.connect('activate', () => {
            this._extensionObject.openPreferences();
        });
        this.menu.addMenuItem(prefsButton);

        // About button
        let aboutButton = new PopupMenu.PopupMenuItem(_('About System Tools'));
        aboutButton.connect('activate', () => {
            this._showAbout();
        });
        this.menu.addMenuItem(aboutButton);

        // Connect menu open state for instant refresh
        this.menu.connect('open-state-changed', (menu, isOpen) => {
            if (isOpen) {
                log('[System Tools] Menu opened - refreshing data');
                this._brightnessModule._getCurrentBrightness();
                this._updateBrightnessHotSensor();
            }
        });
    }

    /**
     * Build brightness control section
     */
    _buildBrightnessSection() {
        let brightnessSection = new PopupMenu.PopupSubMenuMenuItem(_('Brightness'), true);

        // Add current brightness indicator
        let currentBrightnessItem = new PopupMenu.PopupMenuItem(
            _('Current: ') + this._brightnessModule.getCurrentBrightness() + '%'
        );
        currentBrightnessItem.reactive = false;
        currentBrightnessItem.can_focus = false;
        brightnessSection.menu.addMenuItem(currentBrightnessItem);

        brightnessSection.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        // Get brightness profiles from settings
        let profiles = this._settings.get_value('brightness-profiles').deep_unpack();

        // Add profile options
        for (let profileName in profiles) {
            let profileValue = profiles[profileName];
            let displayValue = typeof profileValue === 'number' ? profileValue : parseInt(profileValue);
            let profileItem = new PopupMenu.PopupMenuItem(`${profileName} (${displayValue}%)`);

            // Mark active profile
            if (this._brightnessModule.getCurrentBrightness() === displayValue) {
                profileItem.setOrnament(PopupMenu.Ornament.CHECK);
            }

            profileItem.connect('activate', () => {
                this._brightnessModule.applyProfile(profileName);
                // Refresh menu to show active profile
                this._rebuildBrightnessSection();
            });
            brightnessSection.menu.addMenuItem(profileItem);
        }

        this.menu.addMenuItem(brightnessSection);
    }

    /**
     * Rebuild brightness section (e.g., after profile change)
     */
    _rebuildBrightnessSection() {
        // Remove existing brightness section
        // Note: This is a simplified approach - in a production extension,
        // you'd want to track menu items more carefully
        // For now, we'll just close and rebuild the menu
        this.menu.removeAll();
        this._buildMenu();
    }

    /**
     * Build obsidian vault section
     */
    _buildObsidianSection() {
        let obsidianSection = new PopupMenu.PopupSubMenuMenuItem(_('Obsidian Vaults'), true);

        // Get vault search paths from settings
        let searchPaths = this._settings.get_value('vault-search-paths').deep_unpack();

        // Scan for vaults (placeholder implementation)
        for (let path of searchPaths) {
            let vaultItem = new PopupMenu.PopupMenuItem(path);
            vaultItem.connect('activate', () => {
                this._openObsidianVault(path);
            });
            obsidianSection.menu.addMenuItem(vaultItem);
        }

        this.menu.addMenuItem(obsidianSection);
    }

    /**
     * Update brightness hot sensor in panel
     */
    _updateBrightnessHotSensor() {
        if (this._brightnessHotLabel) {
            let brightness = this._brightnessModule.getCurrentBrightness();
            this._brightnessHotLabel.text = brightness + '%';
        }
    }

    /**
     * Update poll interval
     */
    _updatePollInterval() {
        let newInterval = this._settings.get_int('update-time');
        if (newInterval !== this._brightnessModule._pollInterval) {
            this._brightnessModule.stopPolling();
            this._brightnessModule._pollInterval = newInterval;
            this._brightnessModule.startPolling();
        }
    }

    /**
     * Open Obsidian vault
     */
    _openObsidianVault(path) {
        // This will be implemented in Phase 4
        GLib.spawn_async(null, ['obsidian', path], null, GLib.SpawnFlags.SEARCH_PATH, null);
    }

    /**
     * Create icon based on theme
     */
    _createIcon(iconName) {
        let iconStyle = this._settings.get_string('icon-style');
        let themeIndex = iconStyle === 'original' ? 0 : 1;
        let iconPath = this._sensorsIconPathPrefix[themeIndex] + iconName;

        let gicon = Gio.icon_new_for_string(iconPath);
        let icon = new St.Icon({
            gicon: gicon,
            icon_size: 16
        });

        return icon;
    }

    /**
     * Update visibility based on settings
     */
    _updateVisibility() {
        if (this._brightnessButton) {
            this._brightnessButton.visible = this._settings.get_boolean('show-brightness');
        }

        if (this._obsidianButton) {
            this._obsidianButton.visible = this._settings.get_boolean('show-obsidian');
        }
    }

    /**
     * Update icons when theme changes
     */
    _iconStyleChanged() {
        if (this._brightnessButton && this._brightnessButton.child) {
            let brightnessIcon = this._createIcon('brightness-symbolic.svg');
            this._brightnessButton.set_child(brightnessIcon);
        }

        if (this._obsidianButton && this._obsidianButton.child) {
            let obsidianIcon = this._createIcon('obsidian-symbolic.svg');
            this._obsidianButton.set_child(obsidianIcon);
        }
    }

    /**
     * Add settings change signal
     */
    _addSettingChangedSignal(key, callback) {
        let signalId = this._settings.connect('changed::' + key, callback);
        this._settingChangedSignals.push(signalId);
    }

    /**
     * Show about dialog
     */
    _showAbout() {
        // About dialog - TODO: implement proper modal dialog
        log('[System Tools] About: Version 0.1.0 - Unified system tools for brightness control and Obsidian vault management.');
    }

    /**
     * Clean up resources
     */
    destroy() {
        // Disconnect all settings signals
        for (let signalId of this._settingChangedSignals) {
            this._settings.disconnect(signalId);
        }
        this._settingChangedSignals = [];

        // Stop brightness module polling
        if (this._brightnessModule) {
            this._brightnessModule.destroy();
            this._brightnessModule = null;
        }

        // Remove children
        if (this._menuLayout) {
            this._menuLayout.destroy();
        }

        super.destroy();
    }
});

/**
 * System Tools Extension - Main extension class
 */
export default class SystemToolsExtension extends Extension {
    enable() {
        log('[System Tools] Enabling extension...');

        systemToolsMenu = new SystemToolsMenuButton(this);
        Main.panel.addToStatusArea(this.uuid, systemToolsMenu);

        log('[System Tools] Extension enabled successfully');
    }

    disable() {
        log('[System Tools] Disabling extension...');

        if (systemToolsMenu) {
            systemToolsMenu.destroy();
            systemToolsMenu = null;
        }

        log('[System Tools] Extension disabled successfully');
    }
}
