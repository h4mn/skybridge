@echo off
REM Inicia sessao Claude Code com canal oficial Discord auto-responsivo
:: claude --channels plugin:discord@claude-plugins-official --enable-auto-mode

REM Inicia sessao Claude Code com canal Discord Skybridge auto-responsivo e bypassando permissões (CUIDADO)
:: claude --debug --permission-mode bypassPermissions --dangerously-load-development-channels server:discord

REM Inicia sessão Claude Code com canal Discord Skybridge auto-responsivo e bypassando permissões apontando os MCPs
:: claude  --debug --permission-mode bypassPermissions --dangerously-load-development-channels server:discord --mcp-config B:/_repositorios/skybridge/.mcp.json

REM Inicia sessão Claude Code com canal Planet Crafter auto-responsivo e bypassando permissões apontando os MCPs
claude  --debug --permission-mode bypassPermissions --dangerously-load-development-channels server:planet-crafter --mcp-config B:/_repositorios/skybridge/.mcp.json