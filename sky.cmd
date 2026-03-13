@echo off
cls

setlocal ENABLEEXTENSIONS
set USE_RAG_MEMORY=true
set USE_CLAUDE_CHAT=true
set USE_TEXTUAL_UI=true

if "%1"=="sonnet" set CLAUDE_MODEL=claude-3-5-sonnet-20241022
if "%1"=="opus" set CLAUDE_MODEL=claude-3-opus-20240229
if "%2"=="verbose" set VERBOSE=true

REM Garante que src/ esta no PYTHONPATH
set PYTHONPATH=%~dp0src;%PYTHONPATH%

REM Ponto de entrada com bootstrap de progresso
python scripts\sky_bootstrap.py %*

endlocal
