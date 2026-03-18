@echo off
REM ============================================================================
REM SKY CHAT CLAUDE - Chat com Claude SDK
REM ============================================================================
REM Script para iniciar o chat da Sky com inferência via Claude Agent SDK.
REM
REM Uso:
REM   sky_claude.bat           - Inicia chat com modelo do .env
REM   sky_claude.bat sonnet    - Inicia chat forçando Sonnet
REM
REM Variáveis de ambiente:
REM   - USE_CLAUDE_CHAT=true   (ativa chat Claude)
REM   - ANTHROPIC_DEFAULT_HAIKU_MODEL (modelo a usar, definido no .env)
REM   - VERBOSE=true           (exibe métricas)
REM ============================================================================

setlocal

REM Inicia Sky com Memoria Semântica RAG habilitada
set USE_RAG_MEMORY=true

REM Ativa chat Claude
set USE_CLAUDE_CHAT=true

REM Modelo padrão (do .env via ANTHROPIC_DEFAULT_HAIKU_MODEL)
REM Pode ser sobrescrito pelo argumento de linha de comando
if "%1"=="sonnet" (
    set CLAUDE_MODEL=claude-3-5-sonnet-20241022
) else if "%1"=="opus" (
    set CLAUDE_MODEL=claude-3-opus-20240229
)

REM Ativa verbose se solicitado
if "%2"=="verbose" (
    set VERBOSE=true
)

echo ============================================================================
echo  SKY CHAT CLAUDE
echo ============================================================================
echo  Chat com inferência via Claude Agent SDK
echo  Pressione Ctrl+C para encerrar
echo ============================================================================

python scripts/sky_rag.py

endlocal
