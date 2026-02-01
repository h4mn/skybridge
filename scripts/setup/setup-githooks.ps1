# setup-githooks.ps1 - Configura hooks do git para Skybridge (Windows)
#
# Uso: .\scripts\setup\setup-githooks.ps1
#
# Configura o repositório para usar os hooks versionados em .githooks/
# DOC: ADR024 - Hooks gerenciam limpeza de tmp_path e notificação de commits

$ErrorActionPreference = "Stop"

Write-Host "🔧 Configurando githooks do Skybridge..." -ForegroundColor Cyan

# Verifica se está em um repositório git
$gitDir = git rev-parse --git-dir 2>$null
if (-not $gitDir) {
    Write-Host "❌ Erro: Não está em um repositório git" -ForegroundColor Red
    exit 1
}

# Configura hooksPath
git config core.hooksPath .githooks

# Verifica configuração
$hooksPath = git config core.hooksPath

if ($hooksPath -eq ".githooks") {
    Write-Host "✅ Hooks configurados com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Hooks disponíveis:"
    Get-ChildItem .githooks\ -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  - $($_.Name)"
    }
    Write-Host ""
    Write-Host "Para desabilitar (usar hooks padrão):"
    Write-Host "  git config --unset core.hooksPath"
} else {
    Write-Host "❌ Erro ao configurar hooks" -ForegroundColor Red
    exit 1
}
