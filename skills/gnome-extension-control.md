---
name: gnome-extension-control
description: Controla extensões GNOME Shell (listar, habilitar, desabilitar, recarregar)
hats: [widget-manager]
---

# GNOME Extension Control

## Overview
Gerencia extensões GNOME Shell instaladas, incluindo o foldermenu widget.

## Extension Location
- FolderMenu: `~/.local/share/gnome-shell/extensions/foldermenu@user.local/`

## Commands

### List All Extensions
```bash
gnome-extensions list
```

### Check Extension Status
```bash
# Check if enabled
gnome-extensions list | grep foldermenu

# Get detailed info
gnome-extensions info foldermenu@user.local
```

### Enable Extension
```bash
gnome-extensions enable foldermenu@user.local
```

### Disable Extension
```bash
gnome-extensions disable foldermenu@user.local
```

### Reload Extension (enable after disable)
```bash
gnome-extensions disable foldermenu@user.local
gnome-extensions enable foldermenu@user.local
```

### Reset Extension
```bash
# Reset to default settings
gnome-extensions reset foldermenu@user.local
```

## State Locations
- Extension metadata: `~/.local/share/gnome-shell/extensions/`
- Extension settings: `~/.config/org.gnome.shell.extensions/`

## Notes
- Algumas extensões requerem recarregamento do GNOME Shell após alterações
- Use `Alt+F2`, digite `r`, e Enter para recarregar GNOME Shell manualmente
- FolderMenu é uma extensão local (`@user.local`), não instalada via extensions.gnome.org
