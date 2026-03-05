# Proposal: ChatLogger e Correções do ChatLog

## Why

O sistema atual de logging (`SkybridgeLogger`) usa `stderr` para evitar poluir a UI Textual, mas bibliotecas externas (sentence-transformers, torch, huggingface_hub) continuam imprimindo diretamente no `stdout`/`stderr`, **estragando a UI** quando o RAG carrega modelos ou completa buscas. Além disso, o widget `ChatLog` tem dois problemas visuais: cores não aparecem corretamente e o painel empurra outros widgets para cima ao abrir (overlay não funciona).

**Por que agora?** A integração do RAG com memória semântica está ativa e os usuários reportam que a UI fica "quebrada" durante operações de embedding.

## What Changes

- **Criar `ChatLogger`**: Logger específico para o domínio `sky/chat`, **independente** do `SkybridgeLogger`, que:
  - Redireciona `stdout`/`stderr` permanentemente para si próprio
  - Filtra e silencia saídas de bibliotecas externas (sentence-transformers, torch, etc)
  - Salva logs em arquivo isolado (`.sky/chat.log`)
  - Integra-se com o widget `ChatLog` existente para exibição na UI
  - **NÃO depende de** `runtime/observability/logger.py`

- **Corrigir `ChatLog`** (widget Textual):
  - **BREAKING**: Mudar de `dock: bottom` para `position: absolute` para verdadeiro overlay
  - Cores mais visíveis (cyan em vez de blue, bold red para erros)
  - Adicionar `z-index` para garantir que fica por cima de outros widgets

- **Remover log do `runtime.observability.logger`** do domínio `sky/chat`:
  - `src/core/sky/chat/*` não deve mais importar de `runtime.observability.logger`

## Capabilities

### New Capabilities

- **chat-logger**: Logger específico para domínio de chat com redirecionamento de stdout/stderr e integração com ChatLog widget
  - Redirecionamento permanente de streams para capturar saídas de bibliotecas externas
  - Silenciamento de sentence-transformers, torch, transformers, huggingface_hub
  - Filtro de saídas baseado em verbosidade
  - Integração com ChatLog widget para exibição na UI
  - Log em arquivo isolado (`.sky/chat.log`)

- **chatlog-overlay**: Widget ChatLog com verdadeiro overlay que não empurra outros widgets
  - Posicionamento absoluto para sobreposição
  - Cores visíveis e contrastantes
  - Toggle de visibilidade sem afetar layout

### Modified Capabilities

Nenhuma - esta change adiciona novas capacidades sem modificar comportamentos existentes de outros domínios.

## Impact

**Código afetado**:
- `src/core/sky/chat/` - Novo módulo `logging.py`, remoção de imports do `runtime.observability.logger`
- `src/core/sky/chat/textual_ui/widgets/chat_log.py` - Correções de CSS e cores

**APIs afetadas**:
- Nova API: `ChatLogger` classe com métodos `debug()`, `info()`, `warning()`, `error()`, `evento()`, `structured()`
- Nova API: `get_chat_logger()` singleton
- Nova API: `restore_chat_logger()` para restaurar stdout/stderr

**Dependências**:
- Sem novas dependências externas
- Remove dependência de `runtime.observability.logger` do domínio `sky/chat`

**Sistemas afetados**:
- UI Textual do Chat (`ChatScreen`) - deve inicializar `ChatLogger` no mount
- RAG/Memory - saídas de sentence-transformers serão capturadas e filtradas
