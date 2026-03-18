---
name: resolve-issue
description: Resolução automática de issues via GitHub webhooks
version: 1.0.0
---

Você tem acesso ao sistema de automação de **Resolução de Issues GitHub**.

## GATILHOS

- Usuário invoca `/resolve-issue #<numero_issue>`
- GitHub webhook envia evento `issues.opened` ou `issues.reopened`
- Issue tem labels: `automated`, `bug`, `enhancement`
- Issue é atribuída ao bot/automação

## BASE DE CONHECIMENTO

### Tipos de Issue
| Tipo | Critério de Detecção | Ação |
|------|---------------------|------|
| `hello-world` | Palavras-chave: "hello", "simple", "example" | Criar hello_world.py |
| `bug-simple` | Palavras-chave: "fix", "bug", "error" + complexidade "simple" | Correção de bug simples |
| `bug-complex` | Palavras-chave: "fix", "bug", "error" + complexidade "complex" | Correção de bug complexo |
| `refactor` | Palavras-chave: "refactor", "cleanup", "optimize" | Refatoração de código |
| `generic` | Padrão fallback | Resolução genérica de issue |

### Configuração de Timeout
| Skill | Timeout | Justificativa |
|-------|---------|---------------|
| hello-world | 60s | Simples, deve ser rápido |
| bug-simple | 300s (5min) | Correção de bug simples |
| bug-complex | 600s (10min) | Correção de bug complexo |
| refactor | 900s (15min) | Tarefa de refatoração |
| resolve-issue | 600s (10min) | Padrão para issues |

### Fluxo de Trabalho
1. **Analisar Issue**
   - Ler título, corpo e labels da issue
   - Detectar tipo de issue por palavras-chave
   - Identificar arquivos/componentes afetados

2. **Criar Worktree**
   - Criar worktree isolado: `skybridge-fix-<numero_issue>`
   - Fazer checkout da branch alvo (main ou especificada)

3. **Executar Solução**
   - Ler arquivos relevantes
   - Implementar correção baseada no tipo de issue
   - Criar novos arquivos se necessário
   - Deletar arquivos desnecessários

4. **Commitar Mudanças**
   - Criar mensagem de commit telegráfica
   - Formato: `fix(<componente>): <descrição>`
   - Incluir referência à issue no corpo

5. **Criar PR**
   - Gerar descrição da PR com resumo da issue
   - Referenciar issue original (#<numero>)
   - Definir labels apropriadas

6. **Limpeza**
   - Remover worktree após push bem-sucedido
   - Registrar métricas de execução

### Estrutura do AgentResult
```json
{
  "success": true,
  "changes_made": true,
  "files_created": ["hello_world.py"],
  "files_modified": ["__init__.py"],
  "files_deleted": [],
  "commit_hash": "abc123",
  "pr_url": "https://github.com/h4mn/skybridge/pull/123",
  "message": "Issue resolvida",
  "issue_title": "Corrigir alinhamento de versão",
  "output_message": "Versões alinhadas para 0.2.5",
  "thinkings": [
    {"step": 1, "thought": "Analisando issue...", "timestamp": "...", "duration_ms": 1500},
    {"step": 2, "thought": "Lendo __init__.py...", "timestamp": "...", "duration_ms": 300}
  ]
}
```

### Protocolo XML de Streaming
Ao comunicar com Skybridge via XML:

```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Analisando issue #225...</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

### Tratamento de Erros
- **Timeout:** Retornar `AgentResult` com `success: false`, `AgentState.TIMED_OUT`
- **Conflito Git:** Retornar mensagem de erro, parar execução
- **Arquivos Ausentes:** Registrar aviso, continuar com arquivos disponíveis
- **Falha de Execução:** Retornar `AgentResult` com classificação de `error_type`

## AÇÕES

Quando `/resolve-issue` é acionado:

1. **Extrair Número da Issue**
   - Extrair do formato `#<numero>`
   - Buscar detalhes da issue via GitHub API

2. **Detectar Tipo de Issue**
   - Escanear título/corpo por palavras-chave
   - Verificar labels por hints
   - Padrão `generic` se incerto

3. **Criar Worktree**
   - Executar: `git worktree add ../skybridge-fix-<numero> -b fix-<numero>`
   - Verificar criação do worktree

4. **Spawnar Agente**
   - Usar `AgentFacade.spawn()` com tipo de skill
   - Passar contexto da issue, caminho do worktree
   - Monitorar execução com timeout

5. **Processar Resultado**
   - Em sucesso: Registrar métricas, limpar worktree
   - Em falha: Registrar erro, manter worktree para debug
   - Atualizar status da issue com link da PR

6. **Métricas**
   - Registrar duração da execução
   - Rastrear taxa de sucesso/falha por tipo de issue
   - Reportar incidentes de timeout

## BOAS PRÁTICAS

- **Sempre** verificar tipo de issue antes de agir
- **Nunca** modificar branches de produção diretamente
- **Sempre** criar worktrees isolados
- **Sempre** referenciar issue original na PR
- **Preferir** commits pequenos e focados
- **Sempre** limpar worktrees em sucesso
- **Nunca** ignorar erros silenciosamente

---

> "Resolução automatizada = maintainers felizes" – made by Sky 🤖
