---
name: inbox
description: Capture rapid ideas and create Linear issues in the Inbox project
trigger:
  pattern: "/inbox"
  allowPartial: false
params:
  - name: action
    description: The action to perform (add is the only supported action)
    required: true
  - name: title
    description: The title of the idea (required for add action)
    required: false
---

# Inbox - Captura Rápida de Ideias

Skill para capturar ideias rapidamente e criar issues no projeto "Inbox" do Linear.

## Uso

```
/inbox add <título>
```

## Comportamento

1. **Validação**: O título é obrigatório
2. **Truncamento**: Títulos > 200 caracteres são truncados (título completo preservado na descrição)
3. **Labels automáticas**:
   - `fonte:claude-code`
   - `ação:implementar`
   - `domínio:geral` (padrão)
4. **Expires**: Calculado como hoje + 60 dias
5. **Projeto**: Inbox - Backlog de Ideias

## Descrição Estruturada

Cada issue criada contém:

```markdown
**Fonte:** Claude Code

---

**Ação sugerida:** Implementar | Pesquisar | Arquivar | Descartar
**Expires:** YYYY-MM-DD (60 dias)
```

## Feedback

Sucesso: Retorna link para a issue + emoji ✅
Erro: Mensagem amigável + sugestão de tentar novamente

> "A persistência é o caminho do êxito" – made by Sky 🚀
