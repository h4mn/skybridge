@echo off
setlocal
set USE_RAG_MEMORY=true
set USE_CLAUDE_CHAT=true
if "%1"=="sonnet" set CLAUDE_MODEL=claude-3-5-sonnet-20241022
if "%1"=="opus" set CLAUDE_MODEL=claude-3-opus-20240229
if "%2"=="verbose" set VERBOSE=true
echo ========================================================================
echo  SKY CHAT CLAUDE
echo ========================================================================
python scripts/sky_rag.py
endlocal
