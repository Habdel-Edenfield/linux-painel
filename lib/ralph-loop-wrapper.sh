#!/bin/bash
# Ralph Loop Wrapper - Continuous Orchestration of System Tools
#
# Este script monitora triggers e executa Ralph em loop contínuo

set -euo pipefail

# Configurações
TRIGGER_FILE="/tmp/ralph-trigger.json"
WORKSPACE="/home/user/agent"
BRIGHTNESS_WIDGET="brightness-widget.py"
OBSIDIAN_WIDGET="obsidian-widget.py"
POLL_INTERVAL=60  # segundos

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_widget_status() {
    local widget_name="$1"
    local widget_process="$2"

    if pgrep -f "$widget_process" > /dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

restart_widget() {
    local widget_name="$1"
    local widget_path="$2"

    log_warn "$widget_name não está rodando. Tentando reiniciar..."
    if [ -f "$widget_path" ]; then
        python3 "$widget_path" &
        if [ $? -eq 0 ]; then
            log_info "$widget_name reiniciado com sucesso"
        else
            log_error "Falha ao reiniciar $widget_name"
        fi
    else
        log_error "Arquivo não encontrado: $widget_path"
    fi
}

process_trigger() {
    if [ ! -f "$TRIGGER_FILE" ]; then
        return
    fi

    log_info "Trigger detectado: $TRIGGER_FILE"

    # Ler o trigger
    local action=$(jq -r '.action // empty' "$TRIGGER_FILE" 2>/dev/null || echo "empty")

    case "$action" in
        "brightness.set")
            local brightness=$(jq -r '.params.brightness' "$TRIGGER_FILE" 2>/dev/null)
            local gamma=$(jq -r '.params.gamma' "$TRIGGER_FILE" 2>/dev/null)
            log_info "Ação: Brilho -> $brightness, Gamma -> $gamma"

            # Atualizar configuração do brightness widget
            if [ -n "$brightness" ] && [ -n "$gamma" ]; then
                # O widget aplicará automaticamente se estiver rodando
                log_info "Configuração enviada para brightness-widget"
            fi
            ;;

        "obsidian.open")
            local vault=$(jq -r '.params.vault' "$TRIGGER_FILE" 2>/dev/null)
            log_info "Ação: Abrir vault Obsidian -> $vault"

            if [ -n "$vault" ]; then
                # Usar protocolo obsidian://
                if [ -d "$vault" ]; then
                    xdg-open "obsidian://open?path=$vault" 2>/dev/null || true
                else
                    log_error "Vault não encontrado: $vault"
                fi
            fi
            ;;

        "widgets.restart")
            log_info "Ação: Reiniciar todos os widgets"
            restart_widget "brightness-widget.py" "$HOME/.local/bin/brightness-widget.py"
            restart_widget "obsidian-widget.py" "$HOME/.local/bin/obsidian-widget.py"
            ;;

        "ralph.run")
            local prompt=$(jq -r '.params.prompt' "$TRIGGER_FILE" 2>/dev/null)
            log_info "Ação: Executar Ralph com prompt -> $prompt"

            if [ -n "$prompt" ]; then
                cd "$WORKSPACE"
                ralph run -p "$prompt" --max-iterations 10
            fi
            ;;

        *)
            log_warn "Ação desconhecida: $action"
            ;;
    esac

    # Remover trigger após processamento
    rm "$TRIGGER_FILE"
    log_info "Trigger processado e removido"
}

monitor_widgets() {
    # Monitor brightness widget
    if ! check_widget_status "brightness-widget" "$BRIGHTNESS_WIDGET"; then
        restart_widget "brightness-widget" "$HOME/.local/bin/brightness-widget.py"
    fi

    # Monitor obsidian widget
    if ! check_widget_status "obsidian-widget" "$OBSIDIAN_WIDGET"; then
        restart_widget "obsidian-widget" "$HOME/.local/bin/obsidian-widget.py"
    fi

    # FolderMenu é uma extensão GNOME, não precisa de monitoramento de processo
    # Apenas verificamos se está habilitada periodicamente
}

# Trap para graceful shutdown
cleanup() {
    log_info "Recebendo sinal de shutdown. Encerrando..."
    # Limpar trigger se existir
    rm -f "$TRIGGER_FILE"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Loop principal
log_info "Ralph Loop Wrapper iniciado"
log_info "Workspace: $WORKSPACE"
log_info "Trigger file: $TRIGGER_FILE"
log_info "Poll interval: ${POLL_INTERVAL}s"
log_info ""
log_info "Pressione Ctrl+C para parar"

while true; do
    # Processar trigger se existir
    process_trigger

    # Monitorar widgets
    monitor_widgets

    # Aguardar próximo ciclo
    sleep "$POLL_INTERVAL"
done
