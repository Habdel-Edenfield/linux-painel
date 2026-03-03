#!/bin/bash
# Handoff Commit & Push Script
# Uso: ./handoff-commit.sh "Mensagem do commit"
# Este script adiciona arquivos relevantes, faz commit e push

set -e

COMMIT_MSG="${1:-feat: handoff update}"
WORKSPACE="${WORKSPACE:-/home/user/agent}"
cd "$WORKSPACE"

echo "=== Handoff Commit Script ==="
echo "Mensagem: $COMMIT_MSG"
echo

# Adicionar arquivos principais do projeto
echo "Staging arquivos principais..."
git add ralph.yml README.md
git add specs/*.md
git add PHASE-*.md
git add extensions/

# Adicionar handoffs recentes
git add .ralph/agent/handoff.md 2>/dev/null || true

# Mostrar status
echo
echo "Status:"
git status --short

echo
echo "Criando commit..."
git commit -m "$COMMIT_MSG

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

echo
echo "Pushing to origin..."
git push origin $(git branch --show-current)

echo
echo "=== Commit & Push Completos ==="
git log --oneline -1
