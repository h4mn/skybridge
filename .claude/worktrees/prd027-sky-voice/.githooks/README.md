# Git Hooks do Skybridge

Este diretório contém hooks do Git **versionados** para o projeto Skybridge.

## Configuração

Após clonar o repositório, execute:

```bash
# Linux/macOS
./scripts/setup/setup-githooks.sh

# Windows (PowerShell)
.\scripts\setup\setup-githooks.ps1

# Ou manualmente:
git config core.hooksPath .githooks
```

## Hooks Disponíveis

| Hook | Propósito | ADR |
|------|-----------|-----|
| `post-commit` | Limpa `workspace/core/tmp_path/` após commit | ADR024 |

## Verificação

Para verificar se os hooks estão ativos:

```bash
git config core.hooksPath
# Saída esperada: .githooks
```

## Desabilitar

Para voltar aos hooks padrão do Git:

```bash
git config --unset core.hooksPath
```
