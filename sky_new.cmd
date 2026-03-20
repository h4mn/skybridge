@echo off
REM Sky Chat com Nova Arquitetura Event-Driven
REM DOC: openspec/changes/refactor-chat-event-driven
REM
REM Usa ChatOrchestrator + EventBus em vez do @work decorator
REM para evitar "cancel scope in different task" error

setlocal enabledelayedexpansion

REM Define flag para usar nova implementação
set SKYBRIDGE_USE_NEW_CHAT_IMPL=1

REM Mostra mensagem
echo ======================================================================
echo  Sky Chat - Nova Arquitetura Event-Driven
echo ======================================================================
echo  Modo: Event-Driven (ChatOrchestrator + EventBus)
echo  Env:   SKYBRIDGE_USE_NEW_CHAT_IMPL=1
echo ======================================================================
echo.

REM Executa o app
python -c "from core.sky.chat.textual_ui import SkyApp; SkyApp().run()"

endlocal
