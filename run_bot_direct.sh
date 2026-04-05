#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=.
python discord_bot.py 2>&1 | tee bot_output.txt
