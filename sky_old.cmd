@echo off
REM Sky Chat - Modo Original (Estável)
REM
REM Usa implementação original com @work decorator

setlocal enabledelayedexpansion

REM Garante que nova implementação está DESATIVADA
set SKYBRIDGE_USE_NEW_CHAT_IMPL=0

REM Mostra mensagem
echo ======================================================================
echo  Sky Chat - Modo Original (Estável)
echo ======================================================================
echo  Modo: Original (@work decorator)
echo  Env:   SKYBRIDGE_USE_NEW_CHAT_IMPL=0
echo ======================================================================
echo.

REM Executa o app
python -c "from core.sky.chat.textual_ui import SkyApp; SkyApp().run()"

endlocal
