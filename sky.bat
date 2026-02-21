@echo off

setlocal enabledelayedexpansion

:: Inicia Sky com Memoria Semântica RAG habilitada
set USE_RAG_MEMORY=true
echo.

python scripts\sky_rag.py

pause
