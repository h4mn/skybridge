@echo off
cd /d "%~dp0"
python -c "import sys; sys.path.insert(0, '.'); from src.core.sky.console import main; main()"
