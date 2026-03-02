# Vitals Design Reference

**Source:** https://github.com/corecoding/Vitals
**Version Analyzed:** 73
**Install Location:** `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com/`

Este documento serve como referência de design para refatoração de widgets do sistema. **Vitals é o padrão de design a seguir**, não para copiar código, mas para replicar padrões arquiteturais e estilísticos.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Component Architecture](#component-architecture)
4. [Icon System](#icon-system)
5. [CSS Styling](#css-styling)
6. [Menu Structure](#menu-structure)
7. [GSettings Schema](#gsettings-schema)
8. [Async Polling Pattern](#async-polling-pattern)
9. [Design Patterns to Replicate](#design-patterns-to-replicate)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Architecture Overview

### Core Technology Stack

```javascript
// Imports principais
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
```

### Architecture Principles

1. **GNOME Native Extension** - Não usa AppIndicator, usa `PanelMenu.Button` nativo
2. **Modular Design** - Arquivos separados para responsabilidades distintas
3. **Asynchronous Polling** - GLib timeouts não-bloqueantes para updates
4. **GSettings Configuration** - Schema GNOME padrão para configurações persistentes
5. **Signal-Based Updates** - Settings changes trigger automatic redraws

---

## File Structure

```
Vitals@CoreCoding.com/
├── extension.js           # Main extension entry point (main class)
├── prefs.js              # Preferences dialog (GTK4/Adw)
├── prefs.ui              # GTK UI definition file
├── stylesheet.css        # Minimal CSS styling
├── menuItem.js           # Custom menu item component
├── values.js             # Value formatting utilities
├── sensors.js            # Sensor data collection
├── metadata.json         # Extension metadata
└── schemas/
    ├── org.gnome.shell.extensions.vitals.gschema.xml
    └── gschemas.compiled
└── icons/
    ├── original/         # Original theme icons
    │   ├── temperature-symbolic.svg
    │   ├── voltage-symbolic.svg
    │   ├── fan-symbolic.svg
    │   ├── memory-symbolic.svg
    │   ├── cpu-symbolic.svg
    │   ├── system-symbolic.svg
    │   ├── network-symbolic.svg
    │   ├── network-download-symbolic.svg
    │   ├── network-upload-symbolic.svg
    │   ├── storage-symbolic.svg
    │   ├── battery-symbolic.svg
    │   └── gpu-symbolic.svg
    └── gnome/           # GNOME theme icons (same files, different style)
```

---

## Component Architecture

### Main Class: VitalsMenuButton

```javascript
var VitalsMenuButton = GObject.registerClass({
    GTypeName: 'VitalsMenuButton',
}, class VitalsMenuButton extends PanelMenu.Button {
    _init(extensionObject) {
        super._init(Clutter.ActorAlign.FILL);

        // Settings from extension
        this._settings = extensionObject.getSettings();

        // Icon mapping
        this._sensorIcons = { /* 11 icon types */ };

        // Icon path prefixes for themes
        this._sensorsIconPathPrefix = ['/icons/original/', '/icons/gnome/'];

        // Sensor modules
        this._sensors = new Sensors.Sensors(this._settings, this._sensorIcons);
        this._values = new Values.Values(this._settings, this._sensorIcons);

        // Panel layout (horizontal)
        this._menuLayout = new St.BoxLayout({
            vertical: false,
            x_align: Clutter.ActorAlign.START,
            y_align: Clutter.ActorAlign.CENTER,
            reactive: true,
            x_expand: true
        });

        this._drawMenu();
        this.add_child(this._menuLayout);

        // Settings change signals
        this._addSettingChangedSignal('icon-style', this._iconStyleChanged.bind(this));
        // ... more signals

        this._initializeMenu();
        this._querySensors();
        this._initializeTimer();
    }
});
```

### Key Components

#### 1. Panel Layout (`_menuLayout`)
- **Type:** `St.BoxLayout`
- **Orientation:** Horizontal (vertical: false)
- **Purpose:** Holds hot sensors displayed in panel
- **Pattern:** Icon + Label for each hot sensor

#### 2. Menu Structure (`_initializeMenu()`)
- **Type:** `PopupMenu.PopupSubMenuMenuItem` per category
- **Pattern:** Accordion-style submenus
- **Categories:** temperature, voltage, fan, memory, processor, system, network, storage, battery, gpu

#### 3. Action Buttons (`_createRoundButton()`)
- **Type:** `St.Button` with CSS class `vitals-button-action`
- **Style:** Round (border-radius: 32px)
- **Buttons:** Refresh, System Monitor, Preferences

---

## Icon System

### Icon Mapping

```javascript
this._sensorIcons = {
    'temperature' : { 'icon': 'temperature-symbolic.svg' },
    'voltage'     : { 'icon': 'voltage-symbolic.svg' },
    'fan'          : { 'icon': 'fan-symbolic.svg' },
    'memory'       : { 'icon': 'memory-symbolic.svg' },
    'processor'     : { 'icon': 'cpu-symbolic.svg' },
    'system'        : { 'icon': 'system-symbolic.svg' },
    'network'       : { 'icon': 'network-symbolic.svg',
                      'icon-rx': 'network-download-symbolic.svg',
                      'icon-tx': 'network-upload-symbolic.svg' },
    'storage'      : { 'icon': 'storage-symbolic.svg' },
    'battery'       : { 'icon': 'battery-symbolic.svg' },
    'gpu'           : { 'icon': 'gpu-symbolic.svg' }
}
```

### Icon Loading Pattern

```javascript
// Icon path prefix based on theme setting
this._sensorsIconPathPrefix = ['/icons/original/', '/icons/gnome/'];

// Dynamic icon loading
_sensorIconPath(groupName) {
    let iconStyle = this._settings.get_int('icon-style');  // 0 = original, 1 = gnome
    return this._extensionObject.path + this._sensorsIconPathPrefix[iconStyle] + this._sensorIcons[groupName]['icon'];
}

// Usage in submenu
this._groups[groupName].icon.gicon = Gio.icon_new_for_string(this._sensorIconPath(groupName));
```

### Icon Specifications

| Property | Value |
|----------|-------|
| Format | SVG |
| Style | Symbolic |
| Size | 16px |
| Themes | 2 (Original, GNOME) |
| Path Prefix | Configurable via settings |

### Icon Loading for Hot Sensors

```javascript
_createHotItem(key, value) {
    let icon = this._defaultIcon(key);
    this._hotIcons[key] = icon;
    this._menuLayout.add_child(icon);

    // Don't add label for default icon
    if (key == '_default_icon_') return;

    let label = new St.Label({
        style_class: 'vitals-panel-label',
        text: (value)?value:'\u2026',  // ... loading indicator
        y_expand: true,
        y_align: Clutter.ActorAlign.CENTER
    });

    label.get_clutter_text().ellipsize = 0;  // Prevent ellipsization
    this._hotLabels[key] = label;
    this._menuLayout.add_child(label);
    this._widths[key] = label.width;  // Save for fixed widths
}
```

---

## CSS Styling

### Complete Stylesheet

```css
/* Icon size */
.vitals-icon { icon-size: 16px; }

/* Panel icons - specific margins per type */
.vitals-panel-icon-temperature { margin: 0 1px 0 8px; padding: 0; }
.vitals-panel-icon-voltage { margin: 0 0px 0 8px; padding: 0; }
.vitals-panel-icon-fan { margin: 0 4px 0 8px; padding: 0; }
.vitals-panel-icon-memory { margin: 0 2px 0 8px; padding: 0; }
.vitals-panel-icon-processor { margin: 0 3px 0 8px; padding: 0; }
.vitals-panel-icon-system { margin: 0 3px 0 8px; padding: 0; }
.vitals-panel-icon-network { margin: 0 3px 0 8px; padding: 0; }
.vitals-panel-icon-storage { margin: 0 2px 0 8px; padding: 0; }
.vitals-panel-icon-battery { margin: 0 4px 0 8px; padding: 0; }

/* Panel label */
.vitals-panel-label { margin: 0 3px 0 0; padding: 0; }

/* Action buttons - round style */
.vitals-button-action {
    -st-icon-style: symbolic;
    border-radius: 32px;
    margin: 0px;
    min-height: 22px;
    min-width: 22px;
    padding: 10px;
    font-size: 100%;
    border: 1px solid transparent;
}

/* Hover effect */
.vitals-button-action:hover, .vitals-button-action:focus {
    border-color: #777;
}

/* Button icon */
.vitals-button-action > StIcon { icon-size: 16px; }

/* Button container */
.vitals-button-box {
    padding: 0px;
    spacing: 22px;  /* Space between buttons */
}
```

### CSS Principles

1. **Minimal Overhead** - Only necessary styles, no bloat
2. **Consistent Spacing** - `margin: 0 Xpx 0 8px` pattern for icons
3. **Round Buttons** - `border-radius: 32px` for action buttons
4. **Symbolic Style** - `-st-icon-style: symbolic` for icons
5. **Hover Feedback** - Border color change on hover

---

## Menu Structure

### Menu Layout

```
┌─────────────────────────────────────┐
│  Temperature ▼          [icon]    │  <-- PopupSubMenuMenuItem
│    CPU: 45°C                       │
│    GPU: 60°C                       │
│                                    │
│  Memory ▼              [icon]       │  <-- PopupSubMenuMenuItem
│    Used: 8.2 GB                    │
│    Free: 15.8 GB                   │
│                                    │
│  ────────────────────               │  <-- PopupMenu.PopupSeparatorMenuItem
│                                    │
│  [Refresh]  [Monitor]  [Prefs]     │  <-- Round action buttons
└─────────────────────────────────────┘
```

### Menu Initialization Code

```javascript
_initializeMenu() {
    // Create submenu for each sensor category
    for (let sensor in this._sensorIcons) {
        if (sensor in this._groups) continue;  // Skip existing
        if (sensor === 'gpu') continue;         // Handle GPUs separately

        this._initializeMenuGroup(sensor, sensor);
    }

    // Handle multiple GPUs
    for (let i = 1; i <= this._numGpus; i++)
        this._initializeMenuGroup('gpu#' + i, 'gpu', (this._numGpus > 1 ? ' ' + i : ''));

    // Add separator
    this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

    // Create action button container
    let item = new PopupMenu.PopupBaseMenuItem({
        reactive: false,
        style_class: 'vitals-menu-button-container'
    });

    let customButtonBox = new St.BoxLayout({
        style_class: 'vitals-button-box',
        vertical: false,
        clip_to_allocation: true,
        x_align: Clutter.ActorAlign.CENTER,
        y_align: Clutter.ActorAlign.CENTER,
        reactive: true,
        x_expand: true
    });

    // Create 3 round buttons
    let refreshButton = this._createRoundButton('view-refresh-symbolic', _('Refresh'));
    let monitorButton = this._createRoundButton('org.gnome.SystemMonitor-symbolic', _('System Monitor'));
    let prefsButton = this._createRoundButton('preferences-system-symbolic', _('Preferences'));

    // Connect button handlers
    refreshButton.connect('clicked', (self) => {
        this._sensors.resetHistory();
        this._values.resetHistory(this._numGpus);
        this._updateTimeChanged();
        this._querySensors();
    });

    monitorButton.connect('clicked', (self) => {
        this.menu._getTopMenu().close();
        Util.spawn(this._settings.get_string('monitor-cmd').split(" "));
    });

    prefsButton.connect('clicked', (self) => {
        this.menu._getTopMenu().close();
        this._extensionObject.openPreferences();
    });

    customButtonBox.add_child(refreshButton);
    customButtonBox.add_child(monitorButton);
    customButtonBox.add_child(prefsButton);

    item.actor.add_child(customButtonBox);
    this.menu.addMenuItem(item);

    // Query sensors on menu open
    this._menuStateChangeId = this.menu.connect('open-state-changed', (self, isMenuOpen) => {
        if (isMenuOpen) {
            this._updateTimeChanged();
            this._querySensors();
        }
    });
}
```

### Menu Item Component

```javascript
// menuItem.js - Custom menu item with check/toggle support
export const MenuItem = GObject.registerClass({
    Signals: {
        'toggle': { param_types: [Clutter.Event.$gtype] },
    },
}, class MenuItem extends PopupMenu.PopupBaseMenuItem {
    _init(icon, key, label, value, checked) {
        super._init({ reactive: true });

        this._checked = checked;
        this._updateOrnament();
        this._key = key;
        this._gIcon = icon;

        // Icon
        this.add_child(new St.Icon({ style_class: 'popup-menu-icon', gicon : this._gIcon }));

        // Label
        this._labelActor = new St.Label({ text: label });
        this.add_child(this._labelActor);

        // Value (right-aligned)
        this._valueLabel = new St.Label({ text: value });
        this._valueLabel.set_x_align(Clutter.ActorAlign.END);
        this._valueLabel.set_x_expand(true);
        this._valueLabel.set_y_expand(true);
        this.add_child(this._valueLabel);
    }
});
```

---

## GSettings Schema

### Schema Structure

```xml
<schemalist gettext-domain="gnome-shell-extensions">
  <schema id="org.gnome.shell.extensions.vitals" path="/org/gnome/shell/extensions/vitals/">

    <!-- Hot Sensors (shown in panel) -->
    <key name="hot-sensors" type="as">
      <default>['_memory_usage_', '_system_load_1m_', '__network-rx_max__']</default>
      <summary>Sensors to show in panel</summary>
      <description>List of sensors to be shown in panel</description>
    </key>

    <!-- Update frequency -->
    <key type="i" name="update-time">
      <default>5</default>
      <summary>Seconds between updates</summary>
      <description>Delay between sensor polling</description>
    </key>

    <!-- Position in panel -->
    <key type="i" name="position-in-panel">
      <default>2</default>
      <summary>Position in panel</summary>
      <description>Position in Panel ('left', 'center', 'right')</description>
    </key>

    <!-- Icon theme -->
    <key type="i" name="icon-style">
      <default>0</default>
      <summary>Icon style</summary>
      <description>The icon style (0 = original, 1 = gnome)</description>
    </key>

    <!-- Boolean toggles for each category -->
    <key type="b" name="show-temperature">
      <default>true</default>
      <summary>Monitor temperature</summary>
    </key>
    <!-- ... show-voltage, show-fan, show-memory, show-processor, etc. -->

    <!-- Precision settings -->
    <key type="b" name="use-higher-precision">
      <default>false</default>
      <summary>Use higher precision</summary>
    </key>

    <!-- Display options -->
    <key type="b" name="alphabetize">
      <default>true</default>
      <summary>Alphabetize sensors</summary>
    </key>
    <key type="b" name="hide-zeros">
      <default>false</default>
      <summary>Hide zero values</summary>
    </key>
    <key type="b" name="fixed-widths">
      <default>true</default>
      <summary>Use fixed widths in top bar</summary>
    </key>
    <key type="b" name="hide-icons">
      <default>false</default>
      <summary>Hide icons in top bar</summary>
    </key>

    <!-- String preferences -->
    <key type="s" name="storage-path">
      <default>"/"</default>
      <summary>Storage path</summary>
    </key>
    <key type="s" name="monitor-cmd">
      <default>"gnome-system-monitor"</default>
      <summary>System Monitor command</summary>
    </key>

    <!-- Unit preferences -->
    <key type="i" name="unit">
      <default>0</default>
      <summary>Temperature unit</summary>
    </key>
    <key type="i" name="network-speed-format">
      <default>0</default>
      <summary>Network speed format</summary>
    </key>
    <key type="i" name="memory-measurement">
      <default>1</default>
      <summary>Memory measurement</summary>
    </key>

    <!-- More settings... -->
  </schema>
</schemalist>
```

### Schema Design Principles

1. **Descriptive Keys** - Clear, self-documenting names
2. **Type Safety** - Explicit types (as, i, b, s)
3. **Defaults Provided** - All keys have sensible defaults
4. **Summaries** - Human-readable descriptions
5. **Grouping** - Related settings grouped together

### Settings Signal Pattern

```javascript
_addSettingChangedSignal(key, callback) {
    this._settingChangedSignals.push(
        this._settings.connect('changed::' + key, callback)
    );
}

// Usage
this._addSettingChangedSignal('update-time', this._updateTimeChanged.bind(this));
this._addSettingChangedSignal('icon-style', this._iconStyleChanged.bind(this));

// Trigger redraw on settings change
this._addSettingChangedSignal('fixed-widths', this._redrawMenu.bind(this));
```

---

## Async Polling Pattern

### Timer Implementation

```javascript
_initializeTimer() {
    let update_time = this._settings.get_int('update-time');
    this._refreshTimeoutId = GLib.timeout_add_seconds(
        GLib.PRIORITY_DEFAULT,
        update_time,
        (self) => {
            // Only update if we have hot sensors
            if (Object.values(this._hotLabels).length > 0)
                this._querySensors();
            // Keep timer running
            return GLib.SOURCE_CONTINUE;
        }
    );
}
```

### Key Points

1. **Non-blocking** - Uses `GLib.timeout_add_seconds()` (async)
2. **Priority** - `GLib.PRIORITY_DEFAULT`
3. **Conditional Update** - Only queries if hot sensors exist
4. **Return Value** - `GLib.SOURCE_CONTINUE` to keep timer running

### Menu Open Refresh Pattern

```javascript
// Query immediately when menu opens
this._menuStateChangeId = this.menu.connect('open-state-changed', (self, isMenuOpen) => {
    if (isMenuOpen) {
        // Make sure timer fires at next full interval
        this._updateTimeChanged();
        // Refresh sensors now
        this._querySensors();
    }
});
```

---

## Design Patterns to Replicate

### Pattern 1: Hot Sensors in Panel

```javascript
// Create icon + label pair in panel
_createHotItem(key, value) {
    let icon = this._defaultIcon(key);
    this._hotIcons[key] = icon;
    this._menuLayout.add_child(icon);

    let label = new St.Label({
        style_class: 'vitals-panel-label',
        text: value,
        y_align: Clutter.ActorAlign.CENTER
    });
    this._hotLabels[key] = label;
    this._menuLayout.add_child(label);
}
```

### Pattern 2: Submenu Categories

```javascript
// Create accordion-style submenu
this._groups[groupName] = new PopupMenu.PopupSubMenuMenuItem(
    _(this._ucFirst(groupName) + menuSuffix),
    true  // Expandable
);
this._groups[groupName].icon.gicon = Gio.icon_new_for_string(this._sensorIconPath(groupName));
this.menu.addMenuItem(this._groups[groupName]);
```

### Pattern 3: Round Action Buttons

```javascript
_createRoundButton(iconName) {
    let button = new St.Button({
        style_class: 'message-list-clear-button button vitals-button-action'
    });
    button.child = new St.Icon({ icon_name: iconName });
    return button;
}
```

### Pattern 4: Settings Change Signals

```javascript
// Connect settings changes to callbacks
this._addSettingChangedSignal(key, callback);

_addSettingChangedSignal(key, callback) {
    this._settingChangedSignals.push(
        this._settings.connect('changed::' + key, callback)
    );
}
```

### Pattern 5: Icon Theme Switching

```javascript
// Dynamic icon path based on theme preference
this._sensorsIconPathPrefix = ['/icons/original/', '/icons/gnome/'];

_sensorIconPath(groupName) {
    let iconStyle = this._settings.get_int('icon-style');
    return this._extensionObject.path +
           this._sensorsIconPathPrefix[iconStyle] +
           this._sensorIcons[groupName]['icon'];
}
```

---

## Anti-Patterns to Avoid

### ❌ Don't Use: AppIndicator/AyatanaAppIndicator3

```javascript
// WRONG - Python GTK with AppIndicator
import gi
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import AyatanaAppIndicator3

indicator = AyatanaAppIndicator3.Indicator.new(...)
```

### ✅ Use: GNOME PanelMenu.Button

```javascript
// CORRECT - GNOME Shell native
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';

class VitalsMenuButton extends PanelMenu.Button {
    _init(extensionObject) {
        super._init(Clutter.ActorAlign.FILL);
        // ...
    }
}
```

### ❌ Don't Use: Python for Extensions

```python
# WRONG - Python doesn't integrate well with GNOME Shell
# Cannot use native PanelMenu.Button
```

### ✅ Use: JavaScript/GObject Introspection

```javascript
// CORRECT - Native GNOME Shell extension
import GObject from 'gi://GObject';
import St from 'gi://St';
```

### ❌ Don't Use: Blocking Polling

```javascript
// WRONG - Blocks UI
while (true) {
    querySensors();  // Blocks!
    sleep(1000);
}
```

### ✅ Use: Async GLib Timeout

```javascript
// CORRECT - Non-blocking
GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 5, () => {
    this._querySensors();
    return GLib.SOURCE_CONTINUE;
});
```

### ❌ Don't Use: Custom CSS Frameworks

```css
/* WRONG - Too much overhead */
.vitals-container-wrapper-inner {
    /* 20 lines of nesting */
}
```

### ✅ Use: Minimal Targeted CSS

```css
/* CORRECT - Only what's needed */
.vitals-panel-label { margin: 0 3px 0 0; }
.vitals-button-action { border-radius: 32px; }
```

### ❌ Don't Use: Hardcoded Icon Paths

```javascript
// WRONG - Not theme-switchable
let iconPath = '/path/to/icons/original/temperature.svg';
```

### ✅ Use: Dynamic Theme-Based Paths

```javascript
// CORRECT - Theme-configurable
this._sensorsIconPathPrefix = ['/icons/original/', '/icons/gnome/'];
let iconPath = this._extensionObject.path +
    this._sensorsIconPathPrefix[this._settings.get_int('icon-style')] +
    this._sensorIcons[groupName]['icon'];
```

---

## Applying Vitals Patterns to New Widgets

### Checklist for New Widget Development

#### Architecture
- [ ] Use `PanelMenu.Button` as base class
- [ ] Extend `GObject.registerClass()` for proper GObject
- [ ] Use `St.BoxLayout` for panel layout
- [ ] Use `PopupMenu.PopupSubMenuMenuItem` for categories

#### Icons
- [ ] Create SVG symbolic icons (16px)
- [ ] Support multiple icon themes (original, gnome)
- [ ] Store icons in `icons/original/` and `icons/gnome/`
- [ ] Load icons dynamically with `Gio.icon_new_for_string()`
- [ ] Use `style_class: 'vitals-panel-icon-*'` for panel icons

#### CSS
- [ ] Create minimal stylesheet.css
- [ ] Follow Vitals naming pattern (`vitals-*` prefixes)
- [ ] Use `border-radius: 32px` for round buttons
- [ ] Add hover effects with border-color change
- [ ] Use consistent spacing pattern

#### Settings
- [ ] Create GSettings schema with descriptive keys
- [ ] Use types: `b` (bool), `i` (int), `s` (string), `as` (string array)
- [ ] Provide sensible defaults
- [ ] Add summaries for all keys
- [ ] Connect `changed::key` signals for auto-updates

#### Polling
- [ ] Use `GLib.timeout_add_seconds()` for async updates
- [ ] Return `GLib.SOURCE_CONTINUE` to keep timer running
- [ ] Query immediately on menu open
- [ ] Use conditional updates (only if needed)

#### Menu
- [ ] Create submenus for categories
- [ ] Add separator before action buttons
- [ ] Create round action buttons (22px min, 10px padding, 32px radius)
- [ ] Connect open-state-changed for instant refresh

---

## Summary

Vitals provides an excellent reference for GNOME Shell extension development:

1. **Native Integration** - PanelMenu.Button, not AppIndicator
2. **Minimal CSS** - Only necessary styles, consistent naming
3. **Async Architecture** - GLib timeouts, not blocking loops
4. **Modular Design** - Separate files for concerns
5. **Dynamic Icons** - Theme-switchable SVG symbolic icons
6. **Comprehensive Settings** - GSettings with full configurability
7. **UX Best Practices** - Instant refresh on menu open, hot sensors

When refactoring existing widgets, replicate these patterns, not the code itself.
