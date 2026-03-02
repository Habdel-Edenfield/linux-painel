---
name: system-widget-manager
description: Gerencia o ciclo de vida de widgets do sistema (iniciar, parar, status, reiniciar)
hats: [widget-manager]
---

# System Widget Manager

## Overview
Esta skill fornece comandos para gerenciar widgets Python/GNOME que rodam como indicadores de sistema.

## Widget Locations
- Brightness: `~/.local/bin/brightness-widget.py`
- Obsidian: `~/.local/bin/obsidian-widget.py`
- FolderMenu: `~/.local/share/gnome-shell/extensions/foldermenu@user.local/`

## Commands

### Check Widget Status
```bash
# Brightness widget
ps aux | grep "[b]rightness-widget.py"

# Obsidian widget
ps aux | grep "[o]bsidian-widget.py"

# FolderMenu (GNOME extension)
gnome-extensions list | grep foldermenu
```

### Start Widget
```bash
python3 ~/.local/bin/brightness-widget.py &
python3 ~/.local/bin/obsidian-widget.py &
```

### Stop Widget
```bash
pkill -f brightness-widget.py
pkill -f obsidian-widget.py
```

### Reload GNOME Extension
```bash
gnome-extensions disable foldermenu@user.local
gnome-extensions enable foldermenu@user.local
```

## State Locations
- Brightness config: `~/.config/brightness-widget/profiles.json`
- Obsidian config: `~/.config/obsidian/obsidian.json`
- Extension metadata: `~/.local/share/gnome-shell/extensions/foldermenu@user.local/`
