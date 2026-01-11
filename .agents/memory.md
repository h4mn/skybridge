# Memory - Sessão: Webhook Autonomous Agents (2026-01-10)

## Resumo do que foi resolvido

### 1. Agent Facade Pattern (SPEC008) ✅ COMPLETO
Implementada infraestrutura completa de agentes conforme SPEC008:

**Novos arquivos criados:**
- `src/skybridge/core/contexts/webhooks/infrastructure/agents/domain.py`
  - `AgentState` enum (CREATED, RUNNING, COMPLETED, TIMED_OUT, FAILED)
  - `AgentExecution` dataclass
  - `AgentResult` dataclass
  - `ThinkingStep` dataclass

- `src/skybridge/core/contexts/webhooks/infrastructure/agents/agent_facade.py`
  - Interface abstrata `AgentFacade`

- `src/skybridge/core/contexts/webhooks/infrastructure/agents/claude_agent.py`
  - `ClaudeCodeAdapter` com streaming em tempo real (`subprocess.Popen`)
  - XML streaming protocol para `<skybridge_command>`
  - Skill-based timeouts (hello-world: 60s, bug-simple: 300s, etc)
  - Recuperação de JSON de stdout (`_try_recover_json()`)
  - Encoding UTF-8 para evitar erros de caracteres

- `src/skybridge/core/contexts/webhooks/infrastructure/agents/protocol.py`
  - `XMLStreamingProtocol`
  - `SkybridgeCommand` parser

**Arquivo removido:**
- `src/skybridge/core/contexts/webhooks/application/agent_spawner.py` (código antigo sem streaming)

**Arquivo atualizado:**
- `src/skybridge/core/contexts/webhooks/application/job_orchestrator.py`
  - Substituiu `AgentSpawner` por `ClaudeCodeAdapter`

### 2. Streaming em Tempo Real ✅ COMPLETO
Implementado parsing de `<skybridge_command>` durante execução do agente:
- Loop `for line in process.stdout` processa linha por linha
- Comandos XML são detectados e processados em tempo real
- JSON final é capturado ao completar
- Logging detalhado de progresso (a cada 100 linhas)
- Detecção de palavras-chave (error, warning, permission, confirm)

### 3. Sistema de Logs ✅ COMPLETO
Implementado logging estruturado com saída dupla:
- **Console**: stdout em tempo real
- **Arquivo**: `workspace/skybridge/logs/YYYY-MM-DD.log`
- Encoding UTF-8
- Formatter estruturado com campos extras
- Função `get_log_file_path()` para obter caminho do log atual

### 4. Testes TDD ✅ COMPLETO
- 52 testes específicos do agent infrastructure passando
- `test_agent_infrastructure.py` - 52 testes
  - TestClaudeCodeAdapter (10 testes)
  - TestClaudeCodePathConfig (5 testes)
  - TestJSONValidation (6 novos testes)
  - TestAgentFacadeInterface, TestSkybridgeCommand, TestRealTimeStreaming, etc.
- Total: 170+ testes passando (falhas restantes são de linting/redocly)

### 5. Configuração Centralizada ✅ COMPLETO
**Arquivo:** `src/skybridge/platform/config/config.py`
- `AgentConfig` dataclass com `claude_code_path`
- `load_agent_config()` - Detecta plataforma automaticamente
  - Windows: `claude.cmd`
  - Linux/Mac: `claude`
- ENV var `CLAUDE_CODE_PATH` para override
- `get_agent_config()` singleton

### 6. Recuperação de JSON ✅ COMPLETO
**Arquivo:** `src/skybridge/core/contexts/webhooks/infrastructure/agents/claude_agent.py`
- Método `_try_recover_json(stdout: str) -> str | None`
- 5 estratégias de recuperação:
  1. JSON puro (valida com `json.loads()`)
  2. Bloco markdown `\`\`\`json ... \`\`\``
  3. Bloco código `\`\`\` ... \`\`\``
  4. Busca regex por objeto JSON `{...}`
  5. Busca por chave `"success":` com parsing balanceado de chaves

### 7. System Prompt Aprimorado ✅ COMPLETO
**Arquivo:** `src/skybridge/platform/config/system_prompt.json`
- Instruções explícitas sobre formato JSON
- Exemplo de JSON incluído (escapado como `{{` para não conflitar com format)
- Proibição de markdown (`no \`\`\`json`)
- Adicionado `validation_json.template` para recuperação
- Chaves JSON escapadas (`{{` e `}}`) para evitar conflito com `.format()`

## Issue #4: Bug em dois estágios ✅ COMPLETAMENTE CORRIGIDO

### Estágio 1: ✅ CORRIGIDO
**Problema:** `event_type` incompleto
- **Causa:** `X-GitHub-Event` header é `"issues"` mas código esperava `"issues.opened"`
- **Correção:** `routes.py:794-802` combina header + action do payload
- **Resultado:** Webhook aceito (HTTP 202), job enfileirado

### Estágio 2: ✅ CORRIGIDO (2026-01-11)
**Problema:** `'str' object has no attribute 'get'`
- **Causa raiz:** `claude_agent.py:279` chamava `get_system_prompt_template()` que retorna **STRING** (JSON), mas `render_system_prompt()` espera **DICT**
- **Correção:** Usar `load_system_prompt_config()` que retorna DICT

### Estágio 3: ✅ CORRIGIDO (2026-01-10 23h)
**Problema:** `[WinError 2]` - arquivo não encontrado
- **Causa:** Path "claude" não funciona no Windows
- **Correção:** `AgentConfig` com detecção automática de plataforma (`claude.cmd` no Windows)

### Estágio 4: ✅ CORRIGIDO (2026-01-10 23h)
**Problema:** `unknown option '--cwd'`
- **Causa:** Claude Code CLI não tem flag `--cwd`
- **Correção:** Removido flag, usa `cwd` do `subprocess.Popen`

### Estágio 5: ✅ CORRIGIDO (2026-01-10 23h)
**Problema:** `'charmap' codec can't decode byte 0x8d`
- **Causa:** Encoding padrão do Windows não lê caracteres especiais
- **Correção:** `encoding='utf-8', errors='replace'` no `subprocess.Popen`

### Estágio 6: ✅ CORRIGIDO (2026-01-10 23h)
**Problema:** `ValueError: expected '}' before end of string`
- **Causa:** Chaves `{` e `}` no JSON do exemplo conflitam com `.format()`
- **Correção:** Escapar chaves como `{{` e `}}` em `system_prompt.json`

### Estágio 7: ✅ FUNCIONANDO (2026-01-10 23h20)
**Resultado:** Sistema webhook → agente funcionando end-to-end
- ✅ Webhook aceito (HTTP 202)
- ✅ Job enfileirado
- ✅ Worktree criada
- ✅ Agente executado
- ✅ JSON recuperado com `_try_recover_json()`
- ✅ Job completado com sucesso

### Estágio 8: ✅ CORRIGIDO (2026-01-10 23h30)
**Problema:** `--permission-mode bypass` inválido
- **Causa:** Valor `bypass` não existe no Claude Code CLI, o correto é `bypassPermissions`
- **Correção:** `claude_agent.py:400` alterado para `--permission-mode bypassPermissions`
- **Resultado:** Agente Claude Code CLI responde com sucesso ✅

> "8 estágios de debug, do webhook ao agente funcionando!" – made by Sky 🚀

## Arquivos Chave do Fluxo Webhook → Agente

| Arquivo | Linhas | Status |
|---------|--------|--------|
| `routes.py` | 757-802 | ✅ Bug event_type corrigido |
| `handlers.py` | 50-98 | ✅ OK |
| `webhook_processor.py` | 40-103 | ✅ OK |
| `webhook_worker.py` | 64-114 | ✅ OK |
| `job_orchestrator.py` | 159-220 | ✅ Usa ClaudeCodeAdapter |
| `claude_agent.py` | **todo** | ✅ **MULTIPLOS CORREÇÕES** - encoding, recovery, JSON parsing |
| `agent_prompts.py` | 97 | ✅ OK (espera dict) |
| `config.py` | **AgentConfig** | ✅ **NOVO** - detecção de plataforma |
| `logger.py` | **LOGS** | ✅ **NOVO** - arquivo + console |
| `system_prompt.json` | **validation_json** | ✅ **NOVO** - template de validação |

## Comandos Úteis

### Rodar webhook teste
```bash
python scripts/test_webhook.py
```

### Verificar worktrees
```bash
git worktree list
```

### Verificar logs do dia
```bash
cat workspace/skybridge/logs/2026-01-10.log | grep "job_id"
```

### Rodar testes específicos
```bash
# Todos os agent infrastructure
pytest tests/core/contexts/webhooks/test_agent_infrastructure.py -v

# Apenas JSON validation
pytest tests/core/contexts/webhooks/test_agent_infrastructure.py::TestJSONValidation -v
```

## Resumo Tecnológico

**Stack:**
- Python 3.11.9
- pytest 9.0.1
- Claude Code CLI (via subprocess)
- Git worktrees para isolamento

**Padrões:**
- SPEC008 - Agent Facade Pattern
- PRD013 - Webhook Autonomous Agents
- TDD - Test-Driven Development

**Métricas:**
- 52 testes agent infrastructure
- 170+ testes totais
- Recuperação de JSON: 5 estratégias
- Timeout por skill: 60s a 900s

> "Sistema webhook → agente está COMPLETO e FUNCIONAL!" – made by Sky 🚀
