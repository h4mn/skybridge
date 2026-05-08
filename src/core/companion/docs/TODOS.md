# Companion — TODOS

## Regras de Negócio

### TODO-001: Mensagens do companion no chat do jogo (supersede TODO original)

**Prioridade:** Alta
**Status:** Pendente
**Origem:** Feedback do jogador via skychat (2026-05-03)

**Regra:** As mensagens do companion devem ser escritas diretamente no chat do jogo (o mesmo box onde o jogador digita via `/skychat`), não no balão flutuante.

**Motivo:** O balão tem problemas de visibilidade (AFK, posição, state machine). O chat do jogo é persistente, scrollável, e nunca se perde.

**Análise de viabilidade:**
- O jogo já tem sistema de chat (`SkyChatHandler.cs` captura input do jogador)
- Precisa descobrir como escrever LINHAS no chat do jogo (não só capturar input)
- O balão pode ser mantido como feedback visual rápido (timeout curto), mas o texto definitivo vai pro chat
- Resolveria o problema de "state leak" — mensagem nunca se perde independente do estado

**Problemas com a abordagem anterior (bloquear por AFK/estado):**
- Perch != AFK (jogador pode estar craftando, no inventário, no mapa)
- State machine não tem sinal confiável de "AFK real"
- Bloquear mensagem por estado causa UX quebrada em cenários imprevisíveis

> "Chat do jogo é o canal que nunca falha" – made by Sky 🦉
