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
    description: The title of the idea (optional if description is provided)
    required: false
  - name: description
    description: Additional context for the idea (no character limit, optional if title is provided)
    required: false
---

# Inbox - Captura Rápida de Ideias

Skill para capturar ideias rapidamente e criar issues no projeto "Inbox" do Linear.

## Uso

```
/inbox add <título>
```

## Comportamento

1. **Validação**: Pelo menos título OU descrição é obrigatório (ambos opcionais individualmente)
2. **Truncamento**: Títulos > 200 caracteres são truncados (título completo preservado na descrição)
3. **Descrição opcional**: Texto adicional sem limite de caracteres
4. **Labels automáticas**:
   - `fonte:claude-code`
   - `ação:implementar`
   - `domínio:geral` (padrão)
5. **Expires**: Calculado como hoje + 60 dias
6. **Projeto**: Inbox - Backlog de Ideias

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
