# Plugin GitHub Issues

Automatiza resolução de issues do GitHub via agentes autônomos acionados por webhooks.

## Instalação

```bash
# Copiar para pasta de plugins do Claude
cp -r github-issues ~/.claude/plugins/

# Windows
xcopy /E /I github-issues C:\Users\SEU_USUARIO\.claude\plugins\github-issues
```

## Uso

### Resolver Issue
```
/resolve-issue #<numero_issue>

# Exemplos
/resolve-issue #225
/resolve-issue #123
```

## Tipos de Issue

| Tipo | Timeout | Descrição |
|------|---------|-------------|
| `hello-world` | 60s | Exemplo simples de hello world |
| `bug-simple` | 300s (5min) | Correção de bug simples |
| `bug-complex` | 600s (10min) | Correção de bug complexo |
| `refactor` | 900s (15min) | Refatoração de código |
| `generic` | 600s (10min) | Resolução genérica de issue |

## Fluxo de Trabalho

1. **Analisar Issue**
   - Ler título, corpo e labels da issue
   - Detectar tipo de issue por palavras-chave
   - Identificar arquivos/componentes afetados

2. **Criar Worktree**
   - Criar worktree isolado: `skybridge-fix-<numero_issue>`
   - Fazer checkout da branch alvo

3. **Executar Solução**
   - Ler arquivos relevantes
   - Implementar correção baseada no tipo de issue
   - Criar novos arquivos se necessário

4. **Commitar Mudanças**
   - Commit telegráfico: `fix(<componente>): <descrição>`
   - Incluir referência à issue

5. **Criar PR**
   - Gerar descrição da PR com resumo da issue
   - Referenciar issue original (#<numero>)

6. **Limpeza**
   - Remover worktree após push bem-sucedido

## Integração com Skybridge

Este plugin integra com o sistema de webhooks da Skybridge (PRD013):

```python
# GitHub webhook → Job → Agent Facade → skill resolve-issue
```

Referência: `docs/prd/PRD013-webhook-autonomous-agents.md`

---

> "Resolução automatizada = maintainers felizes" – made by Sky 🤖
