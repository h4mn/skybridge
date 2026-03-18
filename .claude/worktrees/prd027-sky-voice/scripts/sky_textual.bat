@echo off
REM ============================================================================
REM SKY CHAT TEXTUAL - Interface Textual Moderna
REM ============================================================================
REM Script para iniciar o chat da Sky com interface Textual TUI.
REM
REM Uso:
REM   sky_textual.bat          - Inicia chat com UI Textual
REM   sky_textual.bat sonnet   - Inicia com modelo Sonnet
REM
REM Variáveis de ambiente:
REM   - USE_TEXTUAL_UI=true    (ativa UI Textual)
REM   - ANTHROPIC_AUTH_TOKEN   (chave de API Claude)
REM   - CLAUDE_MODEL           (modelo a usar, ex: glm-4.7)
REM ============================================================================

setlocal

REM Ativa UI Textual
set USE_TEXTUAL_UI=true

REM Ativa chat Claude
set USE_CLAUDE_CHAT=true

REM Modelo padrão
if "%1"=="sonnet" (
    set CLAUDE_MODEL=claude-3-5-sonnet-20241022
) else if "%1"=="opus" (
    set CLAUDE_MODEL=claude-3-opus-20240229
)

echo ============================================================================
echo  SKY CHAT TEXTUAL
echo ============================================================================
echo  Interface Textual Moderna
echo  Comandos: /help, /new, /config, /sair
echo  Pressione Ctrl+C para encerrar
echo ============================================================================

python scripts/sky_rag.py

endlocal
