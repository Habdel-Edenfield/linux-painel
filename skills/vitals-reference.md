---
name: vitals-reference
description: Vitals GNOME Shell Extension design reference - padrões arquiteturais e estilísticos para desenvolvimento de widgets
hats: [design-coordinator, gnome-dev-specialist, widget-manager]
---

# Vitals Design Reference Skill

## Overview

Esta skill fornece guia completo para desenvolver widgets seguindo os padrões de design da extensão **Vitals GNOME Shell**. Vitals é o **padrão de design** a seguir para todos os novos widgets do sistema.

**Fonte:** `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com/`
**Documentação completa:** `/home/user/agent/specs/VITALS-DESIGN-REFERENCE.md`

---

## Quick Reference Checklist

### ✅ Architecture (MUST)
- [ ] Use `PanelMenu.Button` como classe base
- [ ] Não use AppIndicator/AyatanaAppIndicator3
- [ ] Use JavaScript com GObject Introspection
- [ ] Não use Python para extensões GNOME Shell
- [ ] Use `St.BoxLayout` para layout do panel (horizontal)

### ✅ Icons (MUST)
- [ ] Crie ícones SVG symbolic (16px)
- [ ] Suporte múltiplos temas: `icons/original/` e `icons/gnome/`
- [ ] Carregue dinamicamente com `Gio.icon_new_for_string()`
- [ ] Use `style_class: 'vitals-panel-icon-*'` no CSS

### ✅ CSS (MUST)
- [ ] Crie `stylesheet.css` minimalista
- [ ] Siga padrão de nomes `vitals-*`
- [ ] Use `border-radius: 32px` para botões redondos
- [ ] Adicione hover effects com `border-color: #777`

### ✅ Settings (MUST)
- [ ] Crie schema GSettings com chaves descritivas
- [ ] Tipos: `b` (bool), `i` (int), `s` (string), `as` (string array)
- [ ] Conecte sinais `changed::key` para auto-updates

### ✅ Polling (MUST)
- [ ] Use `GLib.timeout_add_seconds()` (async, não-blocking)
- [ ] Retorne `GLib.SOURCE_CONTINUE` para manter timer rodando
- [ ] Query imediato ao abrir menu (open-state-changed)

### ✅ Menu (MUST)
- [ ] Use `PopupMenu.PopupSubMenuMenuItem` para categorias
- [ ] Adicione `PopupMenu.PopupSeparatorMenuItem` antes dos botões
- [ ] Crie botões redondos: min 22px, padding 10px, radius 32px
- [ ] Conecte `open-state-changed` para refresh instantâneo

---

## Code Templates

### Extension Base Template

```javascript
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

import {Extension, gettext as _} from 'resource:///org/gnome/shell/extensions/extension.js';

let myExtension;

var MyExtensionMenuButton = GObject.registerClass({
    GTypeName: 'MyExtensionMenuButton',
}, class MyExtensionMenuButton extends PanelMenu.Button {
    _init(extensionObject) {
        super._init(Clutter.ActorAlign.FILL);

        this._extensionObject = extensionObject;
        this._settings = extensionObject.getSettings();

        // Panel layout (horizontal)
        this._menuLayout = new St.BoxLayout({
            vertical: false,
            x_align: Clutter.ActorAlign.START,
            y_align: Clutter.ActorAlign.CENTER,
            reactive: true,
            x_expand: true
        });

        this._initializeMenu();
        this.add_child(this._menuLayout);

        // Initialize timer
        this._initializeTimer();
    }
});
```

### Icon Loading Template

```javascript
// Icon mapping
this._sensorIcons = {
    'my-sensor': { 'icon': 'my-sensor-symbolic.svg' }
};

// Icon path prefixes
this._sensorsIconPathPrefix = ['/icons/original/', '/icons/gnome/'];

// Dynamic icon path
_sensorIconPath(sensorName) {
    let iconStyle = this._settings.get_int('icon-style');
    return this._extensionObject.path +
           this._sensorsIconPathPrefix[iconStyle] +
           this._sensorIcons[sensorName]['icon'];
}

// Usage
let icon = Gio.icon_new_for_string(this._sensorIconPath('my-sensor'));
```

### Round Button Template

```javascript
_createRoundButton(iconName, tooltipText) {
    let button = new St.Button({
        style_class: 'message-list-clear-button button vitals-button-action'
    });

    button.child = new St.Icon({
        icon_name: iconName
    });

    // Optional: connect click handler
    button.connect('clicked', (self) => {
        // Your action here
    });

    return button;
}
```

### Submenu Template

```javascript
_initializeMenuGroup(groupName, label) {
    this._groups[groupName] = new PopupMenu.PopupSubMenuMenuItem(
        _(label),
        true  // Expandable
    );

    // Set icon
    this._groups[groupName].icon.gicon = Gio.icon_new_for_string(
        this._sensorIconPath(groupName)
    );

    // Show/hide based on settings
    if (!this._settings.get_boolean('show-' + groupName))
        this._groups[groupName].actor.hide();

    this.menu.addMenuItem(this._groups[groupName]);
}
```

### Async Polling Template

```javascript
_initializeTimer() {
    let update_time = this._settings.get_int('update-time');

    this._refreshTimeoutId = GLib.timeout_add_seconds(
        GLib.PRIORITY_DEFAULT,
        update_time,
        () => {
            this._queryData();  // Your data fetch
            return GLib.SOURCE_CONTINUE;  // Keep timer running
        }
    );
}

// Query immediately on menu open
this.menu.connect('open-state-changed', (self, isMenuOpen) => {
    if (isMenuOpen) {
        this._queryData();
    }
});
```

### Settings Signal Template

```javascript
_addSettingChangedSignal(key, callback) {
    this._settingChangedSignals.push(
        this._settings.connect('changed::' + key, callback)
    );
}

// Usage
this._addSettingChangedSignal('update-time', this._updateTimeChanged.bind(this));
this._addSettingChangedSignal('icon-style', this._iconStyleChanged.bind(this));
```

---

## CSS Template

```css
/* Icon size */
.my-extension-icon { icon-size: 16px; }

/* Panel icons */
.my-extension-panel-icon {
    margin: 0 3px 0 8px;
    padding: 0;
}

/* Panel label */
.my-extension-panel-label {
    margin: 0 3px 0 0;
    padding: 0;
}

/* Round action buttons */
.my-extension-button-action {
    -st-icon-style: symbolic;
    border-radius: 32px;
    margin: 0px;
    min-height: 22px;
    min-width: 22px;
    padding: 10px;
    border: 1px solid transparent;
}

/* Hover effect */
.my-extension-button-action:hover,
.my-extension-button-action:focus {
    border-color: #777;
}

/* Button icon */
.my-extension-button-action > StIcon {
    icon-size: 16px;
}

/* Button container */
.my-extension-button-box {
    padding: 0px;
    spacing: 22px;
}
```

---

## GSettings Schema Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<schemalist gettext-domain="gnome-shell-extensions">
  <schema id="org.gnome.shell.extensions.my-extension"
          path="/org/gnome/shell/extensions/my-extension/">

    <!-- Update frequency -->
    <key type="i" name="update-time">
      <default>5</default>
      <summary>Seconds between updates</summary>
      <description>Delay between data polling</description>
    </key>

    <!-- Position in panel -->
    <key type="i" name="position-in-panel">
      <default>2</default>
      <summary>Position in panel</summary>
    </key>

    <!-- Icon theme -->
    <key type="i" name="icon-style">
      <default>0</default>
      <summary>Icon style</summary>
      <description>0 = original, 1 = gnome</description>
    </key>

    <!-- Boolean toggle -->
    <key type="b" name="show-in-panel">
      <default>true</default>
      <summary>Show in panel</summary>
    </key>

    <!-- String preference -->
    <key type="s" name="custom-command">
      <default>""</default>
      <summary>Custom command</summary>
    </key>

    <!-- String array -->
    <key name="hot-items" type="as">
      <default>[]</default>
      <summary>Items to show in panel</summary>
    </key>
  </schema>
</schemalist>
```

---

## Commands

### Validate Design Against Vitals Patterns

Use este checklist para validar que um widget segue padrões Vitals:

```bash
# Check extension structure
ls -la /path/to/extension/
# Must have: extension.js, prefs.js, stylesheet.css, icons/

# Check icons
ls -la /path/to/extension/icons/
# Must have: original/, gnome/

# Check CSS
cat /path/to/extension/stylesheet.css
# Must use: vitals-* style classes, border-radius: 32px

# Check schema
cat /path/to/extension/schemas/*.gschema.xml
# Must have: proper types, defaults, summaries
```

### Compile GSettings Schema

```bash
# Install schema
sudo cp /path/to/extension/schemas/*.gschema.xml /usr/share/glib-2.0/schemas/
sudo glib-compile-schemas /usr/share/glib-2.0/schemas/

# Reload GNOME Shell
ALT+F2 -> type 'r' -> Enter
```

### Test Extension

```bash
# Enable extension
gnome-extensions enable my-extension@user.local

# View logs
journalctl -f -u gnome-shell

# Restart GNOME Shell
ALT+F2 -> type 'r' -> Enter
```

---

## Anti-Patterns

### ❌ AVOID: AppIndicator

```javascript
// DON'T DO THIS
import AyatanaAppIndicator3
// Use PanelMenu.Button instead
```

### ❌ AVOID: Python Extensions

```python
# DON'T DO THIS
# Python widgets don't integrate well with GNOME Shell
# Use JavaScript with GObject Introspection
```

### ❌ AVOID: Blocking Loops

```javascript
// DON'T DO THIS
while (true) {
    fetchData();  // Blocks UI
    sleep(1000);
}
// Use GLib.timeout_add_seconds()
```

### ❌ AVOID: Heavy CSS

```css
/* DON'T DO THIS */
.container-wrapper-inner-box { /* too much nesting */ }
/* Use minimal, targeted styles */
```

---

## References

- **Full Documentation:** `/home/user/agent/specs/VITALS-DESIGN-REFERENCE.md`
- **Vitals Source:** `~/.local/share/gnome-shell/extensions/Vitals@CoreCoding.com/`
- **Extension Tutorial:** https://gjs.guide/extensions/
- **GNOME Shell API:** https://gjs-docs.gnome.org/

---

## Usage for Ralph Agents

Quando desenvolvendo um widget novo:

1. **Inicie** lendo `/home/user/agent/specs/VITALS-DESIGN-REFERENCE.md`
2. **Use** os templates acima como ponto de partida
3. **Valide** usando o checklist de Quick Reference
4. **Teste** compilando schema e habilitando extensão
5. **Publique** `widget.design.approved` quando validado

Ao refatorar widget existente:

1. **Compare** arquitetura atual com padrões Vitals
2. **Identifique** diferenças (AppIndicator vs PanelMenu.Button, etc.)
3. **Planeje** migração incremental (mantendo funcionalidade)
4. **Valide** cada passo contra checklist
5. **Documente** mudanças e publish `gnome.modified`

---

**Lembrete:** Não copie código do Vitals. **Replicando padrões**, não implementação.
