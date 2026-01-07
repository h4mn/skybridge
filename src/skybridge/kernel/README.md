# Kernel — Microkernel Skybridge

## O que é

O **Kernel** é o SDK estável que fornece contratos fundamentais para apps e plugins. É a única dependência permitida para plugins, garantindo compatibilidade e evolução controlada.

## Componentes

### `contracts/`
Tipos base: Result, Errors, IDs, envelopes de request/response.

### `envelope/`
Validação, serialização e envelope padrão para comunicação.

### `registry/`
Registry e discovery de handlers (command/query/event).

### `plugin_api/`
Protocolo de plugin + capabilities (o que um plugin pode fazer).

### `versioning/`
Política de compatibilidade (kernel_api v1, v2...).

## Política de Compatibilidade

- **kernel_api v1**: estável, backward-compatible dentro de minor versions.
- Mudanças breaking requerem bump de major version e período de deprecation.
- Plugins declaram versão mínima do kernel no manifest.

## Regras

- Apps podem depender do Kernel + Application layer do Core.
- Plugins dependem **apenas** do Kernel (e ports permitidos do Core).
- Nunca importar `core/contexts/*/domain` diretamente de fora do Core.

---

> "Fronteira explícita hoje é liberdade de refatorar amanhã." – made by Sky ✨
