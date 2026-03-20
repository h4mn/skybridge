@echo off
REM Sky Chat - Modo Original (Estável)
REM
REM Usa implementação original (sem @work, solução SOTA)

setlocal ENABLEEXTENSIONS
set USE_RAG_MEMORY=true
set USE_CLAUDE_CHAT=true
set USE_TEXTUAL_UI=true
set SKYBRIDGE_USE_NEW_CHAT_IMPL=0

REM Garante que src/ esta no PYTHONPATH
set PYTHONPATH=%~dp0src;%PYTHONPATH%

REM Mostra mensagem
echo ======================================================================
echo  Sky Chat - Modo Original (Estável)
echo ======================================================================
echo  Modo: Original (Solução SOTA sem @work)
echo  Env:   SKYBRIDGE_USE_NEW_CHAT_IMPL=0
echo  Bootstrap: Ativado
echo ======================================================================
echo.

REM Executa com bootstrap (barra de progresso)
python scripts\sky_bootstrap.py

endlocal
