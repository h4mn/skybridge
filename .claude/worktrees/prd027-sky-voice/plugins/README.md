# Plugins — Extensões Opcionais

## O que são

**Plugins** são extensões opcionais para Skybridge: integrações, packs de automação e funcionalidades que podem ser instaladas/removidas independentemente do core.

## Regras Fundamentais

1. **Plugins são opcionais** — Skybridge funciona sem qualquer plugin instalado
2. **Nunca dependem de outros plugins** — cada plugin é autônomo
3. **Dependem do Core** — do Kernel (e, quando aplicável, de ports permitidos)
4. **PROIBIDO** importar `core/contexts/*/domain` diretamente

## Estrutura de Plugin

```
<plugin_name>/
├─ manifest.(json|toml|yaml)    # Metadados + versão mínima do kernel
└─ src/<plugin_name>/
   ├─ domain/                   # Domínio específico do plugin (se houver)
   ├─ application/              # Casos de uso do plugin
   ├─ adapters/                 # Integrações externas
   └─ infra/                    # Implementações específicas
```

## Manifest

O arquivo `manifest` deve conter:
- Nome do plugin
- Versão
- Versão mínima do kernel_api requerida
- Permissões solicitadas (fileops, tasks, network, etc.)
- Dependencies externas (se houver)
- Autor/descrição

## Permissões

Plugins devem declarar explicitamente o que precisam:
- `fileops:read` / `fileops:write`
- `tasks:read` / `tasks:write`
- `network:http`
- `integrations:discord`
- etc.

## Evolução

Plugins podem evoluir para:
- Packs de automação prontos
- Integrações compartilháveis
- Distribuição via catálogo/registry

---

> "Plugin é uma escolha, não uma obrigação." – made by Sky ✨
