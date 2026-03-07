#!/bin/bash
# Script de backup para Terminal Multi-Pane
# Cria um arquivo .tar.gz com timestamp

# Diretório da aplicação
APP_DIR="$HOME/.local/share/terminal-multi-pane"

# Diretório de destino (pode ser modificado)
BACKUP_DIR="$HOME/.local/share/terminal-multi-pane/backups"

# Timestamp no formato YYYYMMDD-HHMMSS
TIMESTAMP=$(date +"%Y%m%d-%H%MSS")

# Nome do arquivo de backup
BACKUP_FILE="terminal-multi-pane-backup-${TIMESTAMP}.tar.gz"

# Cria diretório de backups se não existir
mkdir -p "$BACKUP_DIR"

# Cria o backup (excluindo o diretório de backups e arquivos .pyc)
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    --exclude='backups' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    -C "$APP_DIR" .

# Verifica se o backup foi criado com sucesso
if [ $? -eq 0 ]; then
    echo "============================================"
    echo "BACKUP CRIADO COM SUCESSO!"
    echo "============================================"
    echo "Arquivo: ${BACKUP_DIR}/${BACKUP_FILE}"
    echo "Tamanho: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)"
    echo "Timestamp: $TIMESTAMP"
    echo "============================================"

    # Lista os backups existentes
    echo ""
    echo "Backups disponíveis em ${BACKUP_DIR}:"
    ls -lh "${BACKUP_DIR}" | grep -E "\.tar\.gz$"
else
    echo "ERRO: Falha ao criar o backup!"
    exit 1
fi
