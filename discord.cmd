@echo off

:: Inicia sessao Claude Code com canal Discord Skybridge auto-responsivo
:: e bypassando permissões (CUIDADO)
claude --debug --permission-mode bypassPermissions --dangerously-load-development-channels server:discord 