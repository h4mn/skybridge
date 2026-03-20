@echo off
REM Sky Chat com Nova Arquitetura Event-Driven
REM DOC: openspec/changes/refactor-chat-event-driven
REM
REM Usa ChatOrchestrator + EventBus em vez do @work decorator
REM para evitar "cancel scope in different task" error

setlocal ENABLEEXTENSIONS
set USE_RAG_MEMORY=true
set USE_CLAUDE_CHAT=true
set USE_TEXTUAL_UI=true
set SKYBRIDGE_USE_NEW_CHAT_IMPL=1

REM Garante que src/ esta no PYTHONPATH
set PYTHONPATH=%~dp0src;%PYTHONPATH%

REM Mostra mensagem
echo ======================================================================
echo  Sky Chat - Nova Arquitetura Event-Driven
echo ======================================================================
echo  Modo: Event-Driven (ChatOrchestrator + EventBus)
echo  Env:   SKYBRIDGE_USE_NEW_CHAT_IMPL=1
echo  Bootstrap: Ativado
echo ======================================================================
echo.

REM Executa com bootstrap (barra de progresso)
python scripts\sky_bootstrap.py

endlocal
