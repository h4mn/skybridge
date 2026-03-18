#!/bin/bash
#
# setup-githooks.sh - Configura hooks do git para Skybridge
#
# Uso: ./scripts/setup/setup-githooks.sh
#
# Configura o repositório para usar os hooks versionados em .githooks/
# DOC: ADR024 - Hooks gerenciam limpeza de tmp_path e notificação de commits
#

set -e

echo "🔧 Configurando githooks do Skybridge..."

# Verifica se está em um repositório git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Erro: Não está em um repositório git"
    exit 1
fi

# Configura hooksPath
git config core.hooksPath .githooks

# Verifica configuração
HOOKS_PATH=$(git config core.hooksPath)

if [[ "$HOOKS_PATH" == ".githooks" ]]; then
    echo "✅ Hooks configurados com sucesso!"
    echo ""
    echo "Hooks disponíveis:"
    ls -1 .githooks/ 2>/dev/null | sed 's/^/  - /'
    echo ""
    echo "Para desabilitar (usar hooks padrão):"
    echo "  git config --unset core.hooksPath"
else
    echo "❌ Erro ao configurar hooks"
    exit 1
fi
