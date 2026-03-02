#!/bin/bash
# Teste Completo do Sistema Ralph Loop

echo "========================================="
echo "TESTE COMPLETO DO SISTEMA RALPH LOOP"
echo "========================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

# ==========================================
# TESTE 1: Verificar dependências
# ==========================================
echo "TESTE 1: Dependências"
echo "--------------------------------------"

if command -v jq &> /dev/null; then
    test_pass "jq instalado"
else
    test_fail "jq não encontrado (necessário para triggers JSON)"
fi

if command -v pgrep &> /dev/null; then
    test_pass "pgrep instalado"
else
    test_fail "pgrep não encontrado"
fi

if [ -f "/home/user/agent/ralph.yml" ]; then
    test_pass "ralph.yml existe"
else
    test_fail "ralph.yml não encontrado"
fi

if [ -f "/home/user/agent/PROMPT.md" ]; then
    test_pass "PROMPT.md existe"
else
    test_fail "PROMPT.md não encontrado"
fi

# ==========================================
# TESTE 2: Validar sintaxe dos scripts
# ==========================================
echo ""
echo "TESTE 2: Sintaxe dos Scripts"
echo "--------------------------------------"

if bash -n "/home/user/agent/lib/ralph-loop-wrapper.sh" 2>/dev/null; then
    test_pass "ralph-loop-wrapper.sh - sintaxe válida"
else
    test_fail "ralph-loop-wrapper.sh - erro de sintaxe"
fi

if bash -n "/home/user/agent/lib/ralph-trigger.sh" 2>/dev/null; then
    test_pass "ralph-trigger.sh - sintaxe válida"
else
    test_fail "ralph-trigger.sh - erro de sintaxe"
fi

# ==========================================
# TESTE 3: Verificar Widgets Rodando
# ==========================================
echo ""
echo "TESTE 3: Status dos Widgets"
echo "--------------------------------------"

if pgrep -f "brightness-widget.py" > /dev/null; then
    BRIGHTNESS_PID=$(pgrep -f "brightness-widget.py" | head -1)
    test_pass "brightness-widget.py rodando (PID: $BRIGHTNESS_PID)"
else
    test_fail "brightness-widget.py não está rodando"
fi

if pgrep -f "obsidian-widget.py" > /dev/null; then
    OBSIDIAN_PID=$(pgrep -f "obsidian-widget.py" | head -1)
    test_pass "obsidian-widget.py rodando (PID: $OBSIDIAN_PID)"
else
    test_fail "obsidian-widget.py não está rodando"
fi

if gnome-extensions list | grep -q "foldermenu"; then
    test_pass "foldermenu GNOME extension habilitada"
else
    test_fail "foldermenu GNOME extension não encontrada"
fi

# ==========================================
# TESTE 4: Testar Sistema de Triggers
# ==========================================
echo ""
echo "TESTE 4: Sistema de Triggers"
echo "--------------------------------------"

TRIGGER_FILE="/tmp/ralph-trigger-test.json"

# Testar brightness.set
jq -n '{"action":"brightness.set","params":{"brightness":0.8,"gamma":"0.8:0.8:0.8"}}' > "$TRIGGER_FILE" 2>/dev/null
if [ $? -eq 0 ] && [ -f "$TRIGGER_FILE" ]; then
    test_pass "Criar trigger brightness.set"
    rm "$TRIGGER_FILE"
else
    test_fail "Falha ao criar trigger brightness.set"
fi

# Testar obsidian.open
jq -n --arg vault "/home/user/Micologia" '{"action":"obsidian.open","params":{"vault":$vault}}' > "$TRIGGER_FILE" 2>/dev/null
if [ $? -eq 0 ] && [ -f "$TRIGGER_FILE" ]; then
    test_pass "Criar trigger obsidian.open"
    rm "$TRIGGER_FILE"
else
    test_fail "Falha ao criar trigger obsidian.open"
fi

# Testar widgets.restart
jq -n '{"action":"widgets.restart","params":{}}' > "$TRIGGER_FILE" 2>/dev/null
if [ $? -eq 0 ] && [ -f "$TRIGGER_FILE" ]; then
    test_pass "Criar trigger widgets.restart"
    rm "$TRIGGER_FILE"
else
    test_fail "Falha ao criar trigger widgets.restart"
fi

# ==========================================
# TESTE 5: Verificar Systemd Service
# ==========================================
echo ""
echo "TESTE 5: Systemd Service"
echo "--------------------------------------"

SERVICE_FILE="/home/user/.config/systemd/user/ralph-loop.service"

if [ -f "$SERVICE_FILE" ]; then
    test_pass "ralph-loop.service criado"

    # Verificar se está habilitado
    if systemctl --user is-enabled ralph-loop.service 2>/dev/null; then
        test_pass "ralph-loop.service habilitado"
    else
        echo -e "${YELLOW}⚠ INFO${NC}: ralph-loop.service não habilitado (ainda)"
    fi

    # Verificar se está rodando
    if systemctl --user is-active ralph-loop.service 2>/dev/null; then
        test_pass "ralph-loop.service ativo"
    else
        echo -e "${YELLOW}⚠ INFO${NC}: ralph-loop.service não está rodando (ainda)"
    fi
else
    test_fail "ralph-loop.service não encontrado"
fi

# ==========================================
# TESTE 6: Verificar Skills do Ralph
# ==========================================
echo ""
echo "TESTE 6: Skills do Ralph"
echo "--------------------------------------"

SKILLS_OUTPUT=$(ralph tools skill list 2>/dev/null)

if echo "$SKILLS_OUTPUT" | grep -q "brightness-control"; then
    test_pass "Skill brightness-control encontrada"
else
    test_fail "Skill brightness-control não encontrada"
fi

if echo "$SKILLS_OUTPUT" | grep -q "system-widget-manager"; then
    test_pass "Skill system-widget-manager encontrada"
else
    test_fail "Skill system-widget-manager não encontrada"
fi

if echo "$SKILLS_OUTPUT" | grep -q "obsidian-manager"; then
    test_pass "Skill obsidian-manager encontrada"
else
    test_fail "Skill obsidian-manager não encontrada"
fi

# ==========================================
# RESUMO
# ==========================================
echo ""
echo "========================================="
echo "RESUMO DOS TESTES"
echo "========================================="
echo -e "${GREEN}✓ PASSADOS: $TESTS_PASSED${NC}"
echo -e "${RED}✗ FALHADOS: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 TODOS OS TESTES PASSARAM!${NC}"
    echo ""
    echo "Próximos passos:"
    echo "  1. Habilitar e iniciar o serviço: systemctl --user enable --now ralph-loop.service"
    echo "  2. Verificar logs: journalctl --user -u ralph-loop -f"
    echo "  3. Enviar triggers: /home/user/agent/lib/ralph-trigger.sh <ação>"
    exit 0
else
    echo -e "${RED}⚠️  ALGUNS TESTES FALHARAM${NC}"
    echo ""
    echo "Por favor, revise os testes falhados acima."
    exit 1
fi
