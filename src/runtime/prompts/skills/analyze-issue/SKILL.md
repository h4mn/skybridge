---
name: Analyze Issue
description: Analisa issue sem fazer modificações de código. Use esta skill quando um card for movido para "💡 Brainstorm" no Trello, para análise exploratória sem implementação.
version: 1.0.0
---

# Analyze Issue

Esta skill analisa issue/card sem fazer modificações de código, focando em exploração e entendimento do problema.

## Objetivo

Analisar issue/card de forma exploratória, identificando arquivos relevantes, abordagens possíveis e documentando descobertas sem modificar código.

## Quando Usar

Use esta skill quando:
- Card foi movido para "💡 Brainstorm" no Trello
- Issue requer análise exploratória antes da implementação
- Precisa mapear arquivos e componentes afetados
- Requer entender o contexto antes de implementar

## Não Usar

Não use esta skill quando:
- Issue já está claramente definida para implementação
- Card está em "📋 A Fazer" ou "🚧 Em Andamento" (usar `resolve-issue`)
- Requer modificações de código (usar `resolve-issue`)

## Restrições Importantes

**NÃO fazer modificações de código:**
- NÃO criar, modificar ou deletar arquivos
- NÃO executar `git commit`, `git push`
- NÃO criar branches ou worktrees
- NÃO rodar testes que modifiquem o estado

**APENAS analisar e documentar:**
- Ler arquivos existentes
- Buscar por padrões no código
- Entender a arquitetura
- Documentar descobertas

## Processo de Análise

### 1. Entender o Requisito

```python
# Extrair do contexto
issue_number = metadata.get("issue_number")
card_name = metadata.get("trello_card_name")

print(f"Analisando Issue #{issue_number}: {card_name}")
print("Autonomy Level: ANALYSIS (sem modificações)")
```

### 2. Explorar Código Base

Use as ferramentas disponíveis para explorar:
- `Glob` para encontrar arquivos por padrão
- `Grep` para buscar por keywords
- `Read` para ler conteúdo de arquivos

### 3. Identificar Arquivos Relevantes

Mapear:
- **Arquivos de domínio:** Onde a lógica principal reside
- **Arquivos de infraestrutura:** Adaptadores, ports
- **Arquivos de configuração:** Configs, env
- **Testes:** Testes existentes relacionados

### 4. Documentar Descobertas

Criar comentário no card Trello com:

```markdown
## Análise: Issue #XXX

### Entendimento do Problema
[Breve descrição do problema em suas próprias palavras]

### Arquivos Relevantes
- `src/core/webhooks/domain/webhook_event.py` - Define WebhookJob
- `src/core/webhooks/application/handlers.py` - Processa webhooks
- ...

### Abordagem Sugerida
1. Passo 1
2. Passo 2
3. Passo 3

### Questões/Clarificações
- Questão 1?
- Questão 2?

### Riscos Considerados
- Risco 1
- Risco 2
```

### 5. Postar Comentário no Trello

Usar o `TrelloAdapter` para postar comentário:

```python
comment_text = """
## Análise Completa

[Análise detalhada aqui]
"""

trello_adapter.add_card_comment(card_id, comment_text)
```

## Comportamento Esperado

1. **Ler issue/card** - Entender o requisito
2. **Explorar código** - Mapear arquivos relevantes
3. **Analisar contexto** - Entender arquitetura e padrões
4. **Documentar descobertas** - Criar análise estruturada
5. **Postar no Trello** - Adicionar comentário ao card

## Critérios de Sucesso

- [ ] Issue/card foi analisada sem modificações de código
- [ ] Arquivos relevantes foram mapeados
- [ ] Abordagem sugerida foi documentada
- [ ] Comentário foi postado no card Trello
- [ ] Nenhum arquivo foi criado/modificado/deletado

## Exemplo de Uso

```
Contexto: Card movido para "💡 Brainstorm"
Issue: #123 - "Adicionar filtro de webhooks"

Análise:
1. Ler issue #123
2. Buscar por "webhook" no código (Grep)
3. Identificar handlers existentes
4. Mapear onde filtro seria inserido
5. Documentar abordagem
6. Postar no card
```

## Diferença para `resolve-issue`

| Aspecto | `analyze-issue` | `resolve-issue` |
|---------|----------------|-----------------|
| Modifica código? | ❌ Não | ✅ Sim |
| Cria worktree? | ❌ Não | ✅ Sim |
| Cria PR? | ❌ Não | ✅ Sim |
| Posta comentário | ✅ Sim | ❌ Não |
| Autonomy Level | ANALYSIS | DEVELOPMENT |

---

> "Simplicidade é o último grau de sofisticação" – made by Sky 🚀
