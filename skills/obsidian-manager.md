---
name: obsidian-manager
description: Gerencia vaults do Obsidian e acesso rápido via protocolo obsidian://
hats: [obsidian-specialist, widget-manager]
---

# Obsidian Manager

## Overview
Gerencia vaults do Obsidian e permite abrir vaults específicos usando protocolo URI.

## Widget Location
- Obsidian widget: `~/.local/bin/obsidian-widget.py`

## Vault Search Paths
O widget scaneia automaticamente os seguintes diretórios:
- `~/Documentos`
- `~/personal`
- `~/Micologia`

## Commands

### Scan for Vaults
```bash
# Find all .obsidian directories
find ~/Documentos ~/personal ~/Micologia -type d -name ".obsidian" 2>/dev/null
```

### Open Specific Vault (using protocol)
```bash
# Using obsidian:// URI
xdg-open "obsidian://open?path=/home/user/Documentos/MyVault"
```

### Read Obsidian Config
```bash
# Read configured vaults from Obsidian
cat ~/.config/obsidian/obsidian.json | jq '.vaults'
```

### Open Obsidian Application
```bash
# Launch Obsidian AppImage
~/Applications/Obsidian-1.11.5_*.AppImage
```

## State Locations
- Obsidian config: `~/.config/obsidian/obsidian.json`
- Vault metadata: Each vault has a `.obsidian/` folder

## Notes
- Protocolo `obsidian://` funciona se Obsidian estiver instalado
- Widget Python scaneia automaticamente vaults na inicialização
