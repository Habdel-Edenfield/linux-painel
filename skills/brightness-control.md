---
name: brightness-control
description: Controla brilho e gamma do monitor usando xrandr via brightness-widget
hats: [brightness-specialist, widget-manager]
---

# Brightness Control

## Overview
Controla brilho e gamma através do brightness-widget.py que usa xrandr.

## Direct Control (via xrandr)
```bash
# Detect monitor primary
xrandr | grep " connected primary" | awk '{print $1}'

# Set brightness
xrandr --output DP-2 --brightness 0.8

# Set gamma
xrandr --output DP-2 --gamma 0.8:0.8:0.8

# Combined
xrandr --output DP-2 --brightness 0.8 --gamma 0.8:0.8:0.8
```

## Profile-Based Control
O brightness-widget gerencia perfis em `~/.config/brightness-widget/profiles.json`:

```json
{
  "normal": {"label": "☀️ Brilho Normal (100%)", "brightness": 1.0, "gamma": "1.0:1.0:1.0"},
  "comfort": {"label": "🌤️ Modo Conforto (80%)", "brightness": 0.8, "gamma": "0.8:0.8:0.8"},
  "dark": {"label": "🌙 Modo Escuro (70%)", "brightness": 0.7, "gamma": "1.0:1.0:1.0"}
}
```

## Read Current Settings
```bash
# Read brightness widget state
cat ~/.config/brightness-widget/state  # Format: "brightness|gamma"
```

## Write Settings
Modifique diretamente o arquivo de estado e o widget aplicará automaticamente, ou use o widget GUI se estiver rodando.
