#!/bin/bash
# Ralph Trigger - Envia comandos para o loop contínuo

TRIGGER_FILE="/tmp/ralph-trigger.json"

show_help() {
    cat << EOF
Ralph Trigger - Envia comandos para o loop contínuo

Uso:
    ralph-trigger.sh <ação> [parâmetros]

Ações disponíveis:

    brightness.set    Ajusta brilho e gamma
        --brightness <valor>  (0.1-1.5)
        --gamma <R:G:B>       (ex: 0.8:0.8:0.8)

    obsidian.open    Abre um vault do Obsidian
        --vault <caminho>       (ex: /home/user/Documentos/MyVault)

    widgets.restart  Reinicia todos os widgets

    ralph.run       Executa uma tarefa com Ralph
        --prompt "tarefa"       (descrição da tarefa)

Exemplos:

    # Ajustar brilho para modo conforto
    ralph-trigger.sh brightness.set --brightness 0.8 --gamma 0.8:0.8:0.8

    # Abrir vault Micologia
    ralph-trigger.sh obsidian.open --vault /home/user/Micologia

    # Reiniciar widgets
    ralph-trigger.sh widgets.restart

    # Executar tarefa com Ralph
    ralph-trigger.sh ralph.run --prompt "Check status of all widgets"

Status do trigger:
    cat /tmp/ralph-trigger.json

Limpar trigger:
    rm /tmp/ralph-trigger.json
EOF
}

# Parse arguments
ACTION="${1:-}"
shift

case "$ACTION" in
    "brightness.set")
        BRIGHTNESS=""
        GAMMA=""

        while [[ $# -gt 0 ]]; do
            case "$1" in
                --brightness)
                    BRIGHTNESS="$2"
                    shift 2
                    ;;
                --gamma)
                    GAMMA="$2"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done

        if [ -z "$BRIGHTNESS" ] || [ -z "$GAMMA" ]; then
            echo "Erro: brightness.set requer --brightness e --gamma"
            exit 1
        fi

        jq -n \
            --arg action "brightness.set" \
            --argjson brightness "{\"value\":$BRIGHTNESS}" \
            --argjson gamma "{\"value\":\"$GAMMA\"}" \
            '{
                "action": $action,
                "params": {
                    "brightness": $brightness.value,
                    "gamma": $gamma.value
                },
                "timestamp": now | todateiso8601
            }' > "$TRIGGER_FILE"

        echo "✓ Trigger enviado: Brilho=$BRIGHTNESS, Gamma=$GAMMA"
        ;;

    "obsidian.open")
        VAULT=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --vault)
                    VAULT="$2"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done

        if [ -z "$VAULT" ]; then
            echo "Erro: obsidian.open requer --vault"
            exit 1
        fi

        jq -n \
            --arg action "obsidian.open" \
            --arg vault "$VAULT" \
            '{
                "action": $action,
                "params": {"vault": $vault},
                "timestamp": now | todateiso8601
            }' > "$TRIGGER_FILE"

        echo "✓ Trigger enviado: Abrir vault $VAULT"
        ;;

    "widgets.restart")
        jq -n \
            --arg action "widgets.restart" \
            '{
                "action": $action,
                "params": {},
                "timestamp": now | todateiso8601
            }' > "$TRIGGER_FILE"

        echo "✓ Trigger enviado: Reiniciar widgets"
        ;;

    "ralph.run")
        PROMPT=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --prompt)
                    PROMPT="$2"
                    shift 2
                    ;;
                *)
                    shift
                    ;;
            esac
        done

        if [ -z "$PROMPT" ]; then
            echo "Erro: ralph.run requer --prompt"
            exit 1
        fi

        jq -n \
            --arg action "ralph.run" \
            --arg prompt "$PROMPT" \
            '{
                "action": $action,
                "params": {"prompt": $prompt},
                "timestamp": now | todateiso8601
            }' > "$TRIGGER_FILE"

        echo "✓ Trigger enviado: Ralph run '$PROMPT'"
        ;;

    "help"|"-h"|"--help"|"")
        show_help
        ;;

    *)
        echo "Erro: Ação desconhecida '$ACTION'"
        echo ""
        show_help
        exit 1
        ;;
esac
