# Plugin Template

## Estrutura de Plugin Skybridge

Use este template como ponto de partida para criar novos plugins.

## Arquivos Obrigatórios

### `manifest.yaml` (ou .json / .toml)

```yaml
name: "my-plugin"
version: "0.1.0"
description: "Descrição breve do plugin"
author: "Seu Nome"
skybridge_kernel_min: "1.0.0"
permissions:
  - fileops:read
  - fileops:write
  - tasks:read
dependencies: []
```

## Estrutura de Diretórios

```
my-plugin/
├─ manifest.yaml
└─ src/my_plugin/
   ├─ __init__.py
   ├─ domain/              # (opcional) domínio específico do plugin
   ├─ application/         # casos de uso
   ├─ adapters/            # integrações externas
   └─ infra/               # implementações específicas
```

## Desenvolvimento

1. Copie este template para `plugins/<nome-do-plugin>/`
2. Edite o `manifest.yaml` com seus dados
3. Implemente a lógica do plugin
4. Teste localmente antes de distribuir

---

> "Comece pequeno, evolua com intenção." – made by Sky ✨
