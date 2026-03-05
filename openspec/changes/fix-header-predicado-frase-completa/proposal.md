# Proposal: Fix Header Predicado Frase Completa

## Why

A implementação atual do header do Sky Chat está fixando o predicado como `"conversa"` em vez de usar frases completas fluidas conforme especificado na change `sky-chat-textual-ui`. A especificação define claramente o formato `"Sujeito | Verbo Gerúndio Animado | Predicado"` com exemplos como `"Sky debugando erro na API"` (onde o predicado tem 3 palavras), mas a implementação atual exibe apenas `"Sky verbo conversa"` (predicado de 1 palavra fixa).

O problema está na arquitetura: `EstadoLLM` é um DTO que armazena dados do título mas **não possui campo `predicado`**, forcing todos os chamadores a passar predicados separados que nunca são atualizados para valores significativos. Isso resultou em `_VERBOS_TESTE` com apenas verbos isolados e um valor padrão `"conversa"` que nunca muda.

## What Changes

- **ADICIONAR** campo `predicado: str = "conversa"` ao dataclass `EstadoLLM`
- **ATUALIZAR** `_VERBOS_TESTE` para incluir predicados completos em cada entrada
- **MODIFICAR** `ChatHeader.update_estado()` para usar `estado.predicado` quando `predicado=None`
- **MANTER** compatibilidade com API existente (parâmetro `predicado` continua opcional)

### Mudanças de Comportamento

- Títulos de teste agora exibirão frases completas: `"Sky analisando estrutura do projeto"` em vez de `"Sky analisando conversa"`
- `EstadoLLM` torna-se DTO completo para dados do título (texto + animação)
- `ChatHeader.update_estado(estado)` sem segundo parâmetro usa predicado do próprio estado

## Capabilities

### New Capabilities
- `titulo-completo-dinamico`: Título do chat com predicado dinâmico que forma frases completas fluentes conforme a especificação original (`"Sky debugando erro na API"` em vez de `"Sky debugando conversa"`)

### Modified Capabilities
- `textual-chat-ui`: O requirement **"Título de sessão dinâmico com verbo animado"** terá sua implementação corrigida para atender à especificação de frase completa. A delta spec corrigirá a implementação sem alterar os requisitos originais.

## Impact

- **Código afetado**: `src/core/sky/chat/textual_ui/widgets/animated_verb.py` (`EstadoLLM`), `src/core/sky/chat/textual_ui/widgets/header.py` (`ChatHeader`), `src/core/sky/chat/textual_ui/screens/chat.py` (`_VERBOS_TESTE`, `on_mount`, `action_ciclar_verbo`)
- **API pública**: `ChatHeader.update_estado()` mantém compatibilidade (parâmetro `predicado` continua opcional)
- **Novas dependências**: Nenhuma
- **Compatibilidade**: Backward compatible - código existente continua funcionando

---

> "O predicado preso em 'conversa' nunca virou a frase fluida que prometemos" – made by Sky 🚀
