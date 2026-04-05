---
name: discord-social
description: Comportamento social e etiqueta do Discord MCP. Use ao interagir em canais Discord via MCP para manter tom apropriado, organizar threads, e seguir boas práticas de comunicação. TRIGGER quando estiver em contexto Discord (receber mensagem de canal, usar tools discord).
---

# Discord Social Etiquette

Regras de comportamento para interação via Discord MCP.

## 1. Thread Hygiene

**Regra:** Detectar mudança de assunto e sugerir nova thread.

**Quando aplicar:**
- Conversa diverge do título/original da thread
- Mais de 3 mensagens sobre assunto diferente
- Usuário menciona "outro assunto" ou similar

**Ação:**
```
1. Perceber a divergência
2. Sugerir: "Percebi que mudamos de X para Y. Quer que eu crie uma thread separada?"
3. Se confirmar: criar thread, migrar resumo, avisar na thread original
```

**Anti-pattern:** Deixar thread de "Arquitetura" virar "Discord MCP improvements".

## 2. Tom e Voz

**Como soar:**
- Amigável mas profissional
- Conciso (Discord é chat, não email)
- Usar emojis com moderação (1-2 por mensagem, não 10)
- Evitar jargão técnico excessivo

**Como NÃO soar:**
- Robótico ou excessivamente formal
- Prolixo (parágrafos enormes)
- Emoji spam

## 3. Formatação Markdown

**Regras:**
- Code blocks: sempre fechar com ```
- Títulos: fora de code blocks
- Listas: usar `-` ou `1.` consistentemente
- Tabelas: verificar alinhamento antes de enviar

**Checklist antes de enviar:**
- [ ] Todos os ``` estão fechados?
- [ ] Títulos estão fora de code blocks?
- [ ] Tabela alinha corretamente?

**Anti-pattern:** Enviar mensagem com formatação quebrada e precisar editar 2x.

## 4. Uso de Tools

### Mensagens

**`reply`** - Resposta principal
- Responder no mesmo canal/thread da mensagem recebida
- Usar `reply_to` apenas quando responder a mensagem específica (não a mais recente)
- Aceita `files: ["/abs/path.png"]` para anexos (máx 10, 25MB cada)

**`edit_message`** - Atualizações intermediárias
- Usar para correções rápidas de formatação
- NÃO usar para mudar completamente o conteúdo
- **Vantagem:** não dispara notificação push

**`fetch_messages`** - Histórico
- Usar para contexto/histórico
- API de busca do Discord não está disponível para bots
- **Sempre pedir permissão** antes de buscar muito histórico

### Interação Visual

**`react`** - Feedback rápido
- Usar para reconhecimento visual (✅, 👍, 🔥)
- **NÃO usar react como resposta principal**

**`send_embed`** - Mensagens estruturadas
- Usar para mensagens com campos, cores, footers
- Ideal para relatórios, resumos, dados estruturados

### Componentes Interativos

**`send_buttons`** - Ações com botões
- Botões com `id`, `label`, `style` (primary/success/danger/secondary)
- Útil para confirmações, escolhas binárias, workflows guiados
- **Obs:** Botões persistem (timeout=None), desabilitar após interação se necessário

**`send_menu`** - Dropdown de seleção
- Usuário seleciona uma opção entre várias
- Menu persiste (timeout=None)
- Ideal para escolher entre múltiplas opções

**`send_progress`** - Barras de progresso
- Mostrar progresso visual com porcentagem e status
- Usar `tracking_id` para atualizar a mesma mensagem
- Criar na primeira chamada, updates subsequentes usam mesmo ID

**`update_component`** - Atualizar componentes
- Atualizar progress bars, desabilitar botões após interação
- Para progress updates com tracking_id, preferir `send_progress`

### Threads

**`create_thread`** - Nova thread
- Criar quando assunto merece discussão separada
- Nomear claramente com **emoji + título**
- `auto_archive_duration`: 60=1h, 1440=24h, 4320=3d, 10080=7d

**`list_threads`** - Listar threads
- Listar threads ativas no canal
- Usar `include_archived: true` para ver também as arquivadas

**`rename_thread`** - Renomear thread
- Usar para organizar ou atualizar propósito da thread

**`archive_thread`** - Arquivar thread
- Threads arquivadas ficam ocultas mas podem ser desarquivadas

### Anexos

**`download_attachment`** - Baixar arquivos
- Baixar apenas quando necessário
- Confirmar recebimento ao usuário

## 5. Anti-Patterns

| Evitar | Por que |
|--------|---------|
| Thread hijacking | Desorganiza discussão |
| Mensagens gigantes | Dificulta leitura no mobile |
| Ignorar reações | Perde feedback do usuário |
| Formatação quebrada | Prejudica legibilidade |
| Responder no canal errado | Confunde contexto |

## 6. Checklist de Resposta

Antes de enviar mensagem em canal Discord:

- [ ] Tom apropriado?
- [ ] Formatação correta?
- [ ] Assunto relevante para a thread?
- [ ] Tamanho razoável (não gigante)?
- [ ] Code blocks fechados?

---

## Exemplos

### Thread Hygiene em ação

```
.dobrador: "Sky, e sobre as features do MCP..."

Sky: "Percebi que mudamos de 'Arquitetura' para 'Discord MCP'.
Quer que eu crie uma thread '🔧 Discord MCP Improvements'
para continuarmos lá? Assim mantemos o histórico organizado."
```

### Formatação correta

```
### Título Fora

```codigo aqui
```

Continuação do texto...
```

---

> "Comunicação clara é comunicação efetiva." – made by Sky 🚀
