# Proposal: Histórico de Títulos Animados

## Why

O título animado (`AnimatedTitle`) tem um problema de **coerência temporal**:

1. **Título base vs. verbo ativo**: O título é gerado via LLM a cada 3 turnos (`_gerar_titulo()`) e persiste entre turnos como "título base" da conversa. Mas a cada nova mensagem, um verbo é inferido da mensagem do usuário (`_inferir_estado()`) que pode **não combinar** com o título base persistente.

2. **Exemplo do problema**:
   - Título base (gerado turno 3): "debugando erro na API"
   - Usuário envia (turno 5): "cria uma função Python"
   - Verbo inferido: "codando nova funcionalidade"
   - **Resultado**: Título mostra "Sky está codando..." mas o contexto diz "debugando erro na API"

3. **Sem histórico de atividades**: Não há como rastrear o que foi feito durante a sessão além dos turnos individuais. Criar um histórico sequencial permitiria gerar resumos baratos de sessão.

## What Changes

- **Acumular histórico de títulos**: Implementar uma estrutura (lista/dicionário) que acumula todos os estados/títulos animados durante a sessão na ordem em que ocorrem

- **Painel de histórico com múltiplos gatilhos**:
  - **Click em qualquer parte do título**: Clicar no sujeito, verbo ou predicado abre o painel de histórico
  - **Hover no sujeito ou predicado**: Passar o mouse sobre o `TitleStatic` do sujeito ou predicado abre o painel de histórico
  - **Hover no verbo animado**: MANTÉM o comportamento atual — mostra o tooltip `_tooltip_estado` (estado interno: certeza, esforço, emoção, direção)

- **Posição tooltip-like**: O painel de histórico deve aparecer imediatamente abaixo do título, cobrindo toda a largura do `AnimatedTitle`, similar a um dropdown ou tooltip expandido

- **Resumo de sessão**: O histórico acumulado permite gerar resumos baratos de desempenho (quanto tempo gasto em cada tipo de atividade) ao final da sessão

## Capabilities

### New Capabilities
- `animated-title-history`: Histórico sequencial de títulos animados com painel reativo para visualização

### Modified Capabilities
- Nenhuma — as capacidades existentes (`chat-logger`, `chatlog-overlay`) não sofrem mudanças de requisitos

## Impact

**Componentes afetados:**
- `src/core/sky/chat/textual_ui/widgets/title.py` — `AnimatedTitle`
- `src/core/sky/chat/textual_ui/widgets/animated_verb.py` — `AnimatedVerb`, `EstadoModal`

**Novos componentes:**
- Widget de painel de histórico (tooltip-like)
- Estrutura de dados para acumular títulos (`TitleHistory`)

**Dependências:**
- Nenhuma dependência externa nova
- Usa infraestrutura Textual existente (tooltips, modals, reactive)

**Integração:**
- Evento `AnimatedVerb.Inspecionado` será estendido para incluir histórico
- O painel substituirá ou coexistirá com `EstadoModal` atual

> "A percepção em tempo real cria confiança" – made by Sky 🚀
