#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_SRC="$ROOT_DIR/terminal-multi-pane-scripts/terminal-multi-pane.py"
BACKUP_SRC="$ROOT_DIR/terminal-multi-pane-scripts/backup.sh"
EXT_SRC="$ROOT_DIR/terminal-multi-pane-extension"
EXT_SCHEMA_SRC="$EXT_SRC/schemas/org.gnome.shell.extensions.terminal-multi-pane.gschema.xml"
VITALS_SRC="$ROOT_DIR/terminal-vitals"

APP_DIR="$HOME/.local/share/terminal-multi-pane"
BIN_DIR="$HOME/.local/bin"
APP_BIN="$BIN_DIR/terminal-multi-pane"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/terminal-multi-pane.desktop"

TERMINAL_UUID="terminal-multi-pane@habdel.local"
VITALS_UUID="Vitals@CoreCoding.com"
TERMINAL_EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$TERMINAL_UUID"
VITALS_EXT_DIR="$HOME/.local/share/gnome-shell/extensions/$VITALS_UUID"
BACKUP_ROOT="$APP_DIR/backups"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$APP_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$BACKUP_ROOT"

install -m 755 "$APP_SRC" "$APP_DIR/terminal-multi-pane.py"
install -m 755 "$BACKUP_SRC" "$APP_DIR/backup.sh"

cat > "$APP_BIN" <<EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/terminal-multi-pane.py" "\$@"
EOF
chmod 755 "$APP_BIN"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Terminal Multi-Pane
Name[pt_BR]=Terminal Multi-Pane
Comment=Minimal multi-pane terminal workspace
Comment[pt_BR]=Workspace minimalista de terminais com múltiplos painéis
Exec=$APP_BIN --show
Icon=utilities-terminal
Type=Application
Terminal=false
Categories=Utility;System;TerminalEmulator;
StartupNotify=true
EOF

update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
python3 -m py_compile "$APP_DIR/terminal-multi-pane.py"

if [[ -d "$TERMINAL_EXT_DIR" ]]; then
  cp -a "$TERMINAL_EXT_DIR" "$BACKUP_ROOT/$TERMINAL_UUID-$STAMP"
  rm -rf "$TERMINAL_EXT_DIR"
fi

mkdir -p "$TERMINAL_EXT_DIR/icons" "$TERMINAL_EXT_DIR/schemas"
install -m 644 "$EXT_SRC/extension.js" "$TERMINAL_EXT_DIR/extension.js"
install -m 644 "$EXT_SRC/stylesheet.css" "$TERMINAL_EXT_DIR/stylesheet.css"
install -m 644 "$EXT_SRC/icons/terminal-multi-pane-symbolic.svg" \
  "$TERMINAL_EXT_DIR/icons/terminal-multi-pane-symbolic.svg"
install -m 644 "$EXT_SCHEMA_SRC" \
  "$TERMINAL_EXT_DIR/schemas/org.gnome.shell.extensions.terminal-multi-pane.gschema.xml"

cat > "$TERMINAL_EXT_DIR/metadata.json" <<EOF
{
  "name": "Terminal Multi-Pane",
  "description": "Launcher minimalista de multi-pane para o GNOME Shell 46.",
  "uuid": "$TERMINAL_UUID",
  "shell-version": ["46"],
  "url": "",
  "version": 2,
  "settings-schema": "org.gnome.shell.extensions.terminal-multi-pane"
}
EOF

glib-compile-schemas "$TERMINAL_EXT_DIR/schemas"
gsettings --schemadir "$TERMINAL_EXT_DIR/schemas" set \
  org.gnome.shell.extensions.terminal-multi-pane \
  app-path \
  "$APP_DIR/terminal-multi-pane.py"

if [[ -d "$VITALS_EXT_DIR" ]]; then
  cp -a "$VITALS_EXT_DIR" "$BACKUP_ROOT/$VITALS_UUID-before-restore-$STAMP"
  rm -rf "$VITALS_EXT_DIR"
fi

mkdir -p "$VITALS_EXT_DIR"
cp -a "$VITALS_SRC"/. "$VITALS_EXT_DIR"/
if [[ -d "$VITALS_EXT_DIR/schemas" ]]; then
  glib-compile-schemas "$VITALS_EXT_DIR/schemas"
fi

python3 - <<PY
import ast
import subprocess

terminal_uuid = ${TERMINAL_UUID@Q}
vitals_uuid = ${VITALS_UUID@Q}

def get_list(key):
    value = subprocess.check_output(
        ['gsettings', 'get', 'org.gnome.shell', key],
        text=True,
    ).strip()
    if value.startswith('@as '):
        value = value[4:]
    return list(ast.literal_eval(value))

def set_list(key, values):
    serialized = '[' + ', '.join(repr(item) for item in values) + ']'
    subprocess.check_call(['gsettings', 'set', 'org.gnome.shell', key, serialized])

enabled = get_list('enabled-extensions')
for uuid in (vitals_uuid, terminal_uuid):
    if uuid not in enabled:
        enabled.append(uuid)

disabled = [item for item in get_list('disabled-extensions') if item not in {vitals_uuid, terminal_uuid}]

set_list('enabled-extensions', enabled)
set_list('disabled-extensions', disabled)
PY

gnome-extensions disable "$VITALS_UUID" >/dev/null 2>&1 || true
gnome-extensions disable "$TERMINAL_UUID" >/dev/null 2>&1 || true
gnome-extensions enable "$VITALS_UUID" >/dev/null 2>&1 || true
gnome-extensions enable "$TERMINAL_UUID" >/dev/null 2>&1 || true

printf 'App instalado em: %s\n' "$APP_DIR"
printf 'Launcher criado em: %s\n' "$APP_BIN"
printf 'Extensão Terminal Multi-Pane instalada em: %s\n' "$TERMINAL_EXT_DIR"
printf 'Vitals restaurado em: %s\n' "$VITALS_EXT_DIR"
printf 'Backups gerados em: %s\n' "$BACKUP_ROOT"
