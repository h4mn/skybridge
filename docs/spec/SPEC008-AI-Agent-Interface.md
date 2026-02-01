---
status: rascunho
data: 2026-01-10
version: 0.3.0
---

# SPEC008 — AI Agent Interface (Skybridge)

## 1) Objetivo

Definir o contrato técnico para **agentes de IA autônomos** que operam como subprocessos isolados, capazes de executar tarefas de desenvolvimento através de **inferência de linguagem natural** (nunca heurísticas).

Esta especificação define:
- Interface de criação para agentes AI (Claude Code, Roo Code, etc.)
- Protocolo de comunicação stdin/stdout streaming entre orchestrator e agente
- Formato de entrada/saída para execução autônoma
- Ciclo de vida e gerenciamento de worktrees isolados
- Interface de comunicação Skybridge ↔ Agente via XML
- Observabilidade com snapshot antes/depois
- Log interno persistido em `.sky/`
- System prompts como entidades configuráveis em `config/`

## 2) Escopo

Inclui:

* Criação de agente como subprocesso isolado
* Comunicação via stdin/stdout streaming (prompt principal → agente → JSON output)
* Trabalho em worktree Git isolado
* System prompts configuráveis como entidades próprias
* Resultado estruturado (files created, modified, commits, PRs, thinkings)
* Timeout e cancelamento
* Observabilidade completa (issue_title, output_message, thinkings, timestamps, snapshots)
* Interface de comunicação bidirecional Skybridge ↔ Agente via stdin/stdout
* Log interno do agente em `.sky/`

Não inclui:

* Treinamento ou fine-tuning de modelos
* Implementação interna do agente (black box)
* Gerenciamento de API keys de LLM providers
* UI de interação com agente
* Orquestração de múltiplos agentes (definido em SPEC009)

## 3) Terminologia

| Termo | Definição |
|-------|-----------|
| **Agente AI** | Subprocesso que executa **inferência de linguagem natural** para realizar tarefas de desenvolvimento (ex: Claude Code CLI) |
| **Orchestrator** | Componente Skybridge que cria e gerencia o ciclo de vida do agente |
| **Agent Facade** | Camada de abstração que isola o orchestrator de detalhes específicos de cada agente (Claude, Roo, etc) |
| **Worktree** | Diretório Git isolado onde o agente opera sem afetar o repositório principal |
| **Job** | Unidade de trabalho contendo contexto (issue, repo, branch) para o agente |
| **Skill** | Tipo de tarefa específica que o agente executa (resolve-issue, respond-discord, etc) |
| **Inferência** | Processamento de linguagem natural por LLM para gerar código/ações. Distingue-se de heurística por: 1) Análise contextual do problema (não pattern matching) 2) Geração de soluções adaptativas (não regras fixas) 3) Compreensão de intenção (não sintaxe) |
| **Heurística** | Regras fixas ou pattern matching sem compreensão contextual (ex: string matching, if/else simples). **PROIBIDO** para tomada de decisões pelo agente |
| **Thinkings** | Lista de passos de raciocínio do agente para depuração de dificuldades |
| **System Prompt** | Template de contexto configurável que evolui como entidade própria |
| **skybridge_command** | Comando XML enviado pelo agente para comunicar-se com Skybridge |

### 3.1) Validação de Inferência vs Heurística

**Princípio:** Agentes DEVEM utilizar **inferência** (compreensão contextual) e **NUNCA heurísticas** (regras fixas).

**Exemplos para Distinguir:**

| Aspecto | ✅ Inferência (Válido) | ❌ Heurística (Proibido) |
|---------|------------------------|--------------------------|
| **Análise** | Lê issue, analisa código, compreende contexto | Detecta palavra-chave, executa regra pré-definida |
| **Decisão** | Gera solução adaptativa ao problema | Seleciona script template baseado em pattern |
| **Execução** | Escreve código específico para o contexto | Aplica patch genérico sem entender impacto |
| **Raciocínio** | Thinkings mostram "Analisando X, percebi Y, portanto Z" | Thinkings mostram "Detectei padrão P, apliquei regra R" |

**Exemplo Prático - Issue: "Fix version alignment"**

```
✅ INFERÊNCIA:
  Thinking 1: "Lendo issue #225: version mismatch entre CLI e API"
  Thinking 2: "Analisando __init__.py: CLI=0.2.4, API=0.2.5"
  Thinking 3: "Decisão: alinhar ambos para 0.2.5 (versão mais recente)"
  Thinking 4: "Implementando: atualizando __version__ em ambos os módulos"

❌ HEURÍSTICA:
  Thinking 1: "Detectei keyword 'version' na issue"
  Thinking 2: "Executando script version_fix.sh automaticamente"
  Thinking 3: "Script aplicou patch padronizado"
```

**Indicadores de Inferência Válida:**
- Thinkings demonstram compreensão do problema específico
- Solução é contextualizada (não genérica)
- Agente lê e analisa arquivos antes de agir
- Raciocínio mostra causa → efeito → decisão

**Indicadores de Heurística (Proibido):**
- Thinkings mencionam "padrão detectado", "template", "regra"
- Ação é tomada antes de analisar contexto
- Solução genérica aplicada sem compreensão
- Keywords usadas como gatilho para scripts

## 4) Arquitetura de Agente

### 4.1) Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Skybridge Orchestrator                            │
│                                                                             │
│  Job Queue → Worktree Manager → Agent Spawner ──cria──→  ┌───────────┐   │
│                                                  subprocess  │           │   │
│  Snapshot Before                                                   │  Agente   │   │
│  ├─ Git state                                                      │  AI (CLI) │   │
│  ├─ Files tree                                                     │ Claude /  │   │
│  └─ Worktree metadata                                              │   Roo     │   │
│                                                               └─────┬─────┘   │
│                                                                     │          │
│  ┌──────────────────────────────────────────────────────────────────┐  │          │
│  │                 Agent Facade (Abstração)                        │  │          │
│  │                                                                  │  │          │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │  │          │
│  │  │ Claude Code │  │  Roo Code   │  │  Copilot    │  (futuro)  │  │          │
│  │  │  Adapter    │  │  Adapter    │  │  Adapter    │            │  │          │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │  │          │
│  └─────────┼────────────────┼────────────────┼─────────────────────┘  │          │
│            │                │                │                         │          │
│            └────────────────┴────────────────┴────────┐                │          │
│                                                       │                │          │
│  ┌──────────────────────────────────────────────────────────────────┐  │          │
│  │           Skybridge ↔ Agente Protocol (stdin/stdout)             │  │          │
│  │                                                                  │  │          │
│  │  Orchestrator → Agente:                                         │  │          │
│  │  [stdin] prompt principal + system prompt                        │  │          │
│  │                                                                  │  │          │
│  │  Agente → Orchestrator:                                         │  │          │
│  │  [stdout] <skybridge_command>                                   │  │          │
│  │            <command>log</command>                               │  │          │
│  │            <parametro name="mensagem">hello world!</parametro>  │  │          │
│  │          </skybridge_command>                                   │  │          │
│  │                                                                  │  │          │
│  │  [stdout] JSON final (ao completar)                             │  │          │
│  │                                                                  │  │          │
│  └──────────────────────────────────────────────────────────────────┘  │          │
│                                                                     │          │
│                                                                     ↓          │
│                                                        ┌──────────────────┐ │
│                                                        │  Worktree Git    │ │
│                                                        │  (isolado)       │ │
│                                                        │                  │ │
│                                                        │  .sky/           │ │
│                                                        │  └── agent.log   │ │
│                                                        │  ✨ Agente       │ │
│                                                        │     trabalha     │ │
│                                                        │     aqui         │ │
│                                                        └──────────────────┘ │
│                                                                     ↑          │
│                                                                     │          │
│  Snapshot After                                                     │          │
│  ├─ Git state                                                       │          │
│  ├─ Files tree                                                      │          │
│  ├─ Changes diff                                                    │          │
│  └─ Worktree metadata                                              │          │
│                                                                     │          │
│                                                        Result: ──┘          │
│  ├─ timestamp_start                                               │
│  ├─ timestamp_end                                                 │
│  ├─ success (bool)                                                 │
│  ├─ changes_made (bool)                                            │
│  ├─ files_created (list)                                           │
│  ├─ files_modified (list)                                          │
│  ├─ files_deleted (list)                                           │
│  ├─ commit_hash (str)                                               │
│  ├─ pr_url (str)                                                    │
│  ├─ message (str)                                                   │
│  └─ thinkings (list)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2) Propriedades do Agente

Um agente AI DEVE:

1. **Executar como subprocesso** com comunicação via stdin/stdout streaming
2. **Aceitar worktree path** como diretório de trabalho isolado
3. **Receber contexto** via system prompt configurável (`config/agent_prompts.py`)
4. **Utilizar INFERÊNCIA** para analisar e executar tarefas (JAMAIS heurísticas)
5. **Retornar resultado estruturado** (JSON parseável via stdout)
6. **Respeitar permissões** do sistema de arquivos local
7. **Comunicar-se com Skybridge** via protocolo XML bidirecional
8. **Manter log interno** em `.sky/agent.log`

Um agente AI NÃO DEVE:

1. **Operar fora do worktree** designado
2. **Depender de heurísticas** simples (string matching, if/else) para tomar decisões
3. **Modificar repositório principal** (apenas worktree isolado)
4. **Executar ações destrutivas** sem confirmação (delete, rm -rf, etc)

## 5) Agent Facade (Framework)

### 5.1) Objetivo

O **Agent Facade** é uma camada de abstração que:

* Isola o orchestrator de diferenças entre agentes (Claude, Roo, Copilot)
* Fornece interface única para criação de agentes
* Traduz contexto Skybridge para formato específico de cada agente
* Normaliza saída de diferentes agentes para formato comum

### 5.2) Interface

```python
class AgentFacade(ABC):
    """Interface para criação de agentes AI."""

    @abstractmethod
    def spawn(
        self,
        job: WebhookJob,
        skill: str,
        worktree_path: str,
        skybridge_context: dict
    ) -> Result[AgentExecution, str]:
        """
        Cria agente com contexto completo.

        Args:
            job: Job de webhook com issue/event details
            skill: Tipo de tarefa (resolve-issue, etc)
            worktree_path: Diretório isolado
            skybridge_context: Contexto Skybridge (repo, branch, etc)

        Returns:
            Result com AgentExecution ou erro
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> str:
        """Retorna tipo de agente (claude-code, roo-code, etc)."""
        pass
```

### 5.3) Adapters Específicos

> **Nota:** A partir de ADR021 (2026-01-29), a implementação padrão é `ClaudeSDKAdapter` usando SDK oficial. O exemplo abaixo mantido para referência histórica da arquitetura.

**Implementação Atual (SDK Oficial - ADR021):**
```python
class ClaudeSDKAdapter(AgentFacade):
    """Adapter usando claude-agent-sdk oficial da Anthropic."""

    async def spawn(self, job, skill, worktree_path, skybridge_context):
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

        # System prompt configurável via config/agent_prompts.py
        system_prompt = get_system_prompt_template()
        rendered = render_system_prompt(system_prompt, skybridge_context)

        # SDK com opções nativas
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            permission_mode="acceptEdits",
            cwd=worktree_path,
            system_prompt=rendered,
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(self._build_main_prompt(job))
            result = await self._wait_for_result(client, timeout=self._get_timeout(skill))

        return self._extract_result(result)
```

**Implementação Legada (Subprocess - DEPRECATED):**
```python
class ClaudeCodeAdapter(AgentFacade):
    """Adapter para Claude Code CLI via subprocess (DEPRECATED - ver ADR021)."""

    def spawn(self, job, skill, worktree_path, skybridge_context):
        # System prompt configurável via config/agent_prompts.py
        system_prompt = get_system_prompt_template()
        rendered = render_system_prompt(system_prompt, skybridge_context)

        # Executa com stdin/stdout streaming
        cmd = [
            "claude",
            "--print",
            "--cwd", worktree_path,
            "--system-prompt", rendered,
            "--output-format", "json",
            "--permission-mode", "bypass",
        ]

        result = subprocess.run(
            cmd,
            input=self._build_main_prompt(job),
            capture_output=True,
            text=True,
            timeout=self._get_timeout(skill),
            cwd=worktree_path,
        )

        return self._parse_result(result.stdout)
```

## 6) Interface de Comunicação Skybridge ↔ Agente

### 6.1) Protocolo Bidirecional via stdin/stdout

O agente se comunica com Skybridge através de **stdout streaming**:

1. **Orchestrator → Agente**: Envia prompt principal via stdin
2. **Agente → Orchestrator**: Envia comandos XML via stdout durante execução
3. **Agente → Orchestrator**: Envia JSON final ao completar

### 6.2) Formato: XML (Versão 1 - Hello World)

```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">hello world do subagente!</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

**IMPORTANTE - Distinção Clara:**

| Conceito | Descrição | Exemplo |
|----------|-----------|---------|
| `skybridge_command` | **Comando XML** que o agente envia para se comunicar com Skybridge | `<skybridge_command><command>log</command>...` |
| Script `hello_world.py` | **Arquivo Python** criado pelo agente via inferência após analisar uma issue | `print("Hello, World!")` |

**São coisas completamente distintas:**

* `skybridge_command` é o **protocolo de comunicação** agente ↔ Skybridge
* Script `hello_world.py` é um **artefacto gerado** pelo agente quando a issue pede "criar hello world"

### 6.2.1) Tratamento Seguro de XML

**Por que XML para streaming?**

| Vantagem | Explicação |
|----------|------------|
| **Delimitação clara** | Tags `<skybridge_command>` são facilmente detectáveis no streaming |
| **Extensibilidade** | Novos comandos podem ser adicionados sem quebrar parsers existentes |
| **Separabilidade** | XML não é facilmente confundido com output regular do agente |
| **LLM-friendly** | LLMs modernos (Claude, GPT-4) geram XML com alta precisão |

**Cuidados no Tratamento de XML:**

| Risco | Mitigação |
|-------|-----------|
| **XML Injection** | Sanitizar valores de parâmetros antes de inserir no XML |
| **Parsing malformado** | Usar parser robusto (ex: `lxml` com `recover=True`) |
| **Denial of Service** | Limitar tamanho máximo do XML (50.000 caracteres) |
| **Tags desconhecidas** | Ignorar com WARNING, não quebrar o parsing |
| **Encoding issues** | Forçar UTF-8 e validar encoding antes do parse |

**Exemplo de Parsing Seguro:**

```python
import lxml.etree as ET

def parse_skybridge_command(xml_line: str) -> dict | None:
    """Parse seguro de comando XML."""
    try:
        # Limita tamanho
        if len(xml_line) > 50000:
            logger.warning("XML command too large, ignoring")
            return None

        # Sanitização básica
        xml_line = xml_line.strip()

        # Parse com recovery
        root = ET.fromstring(xml_line, parser=ET.XMLParser(recover=True))

        # Valida estrutura
        if root.tag != "skybridge_command":
            logger.warning(f"Unknown root tag: {root.tag}")
            return None

        command = root.find("command")
        if command is None:
            logger.warning("Missing <command> tag")
            return None

        return {"command": command.text, "params": {...}}

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return None
```

### 6.3) Comandos Disponíveis

| Comando | Parâmetros | Descrição | Status |
|---------|-----------|-----------|--------|
| `log` | `mensagem`, `nivel` | Envia log para Skybridge | ✅ Implementar |
| `progress` | `porcentagem`, `mensagem` | Atualiza progresso | 🔮 Futuro |
| `checkpoint` | `descricao` | Marca checkpoint no fluxo | 🔮 Futuro |
| `error` | `mensagem`, `detalhes` | Reporta erro não fatal | 🔮 Futuro |

### 6.4) Mecanismo de Streaming

**stdin (Orchestrator → Agente):**
```python
# Orchestrator envia prompt principal via stdin
subprocess.run(
    cmd,
    input=prompt_principal,  # ← stdin
    capture_output=True,
    text=True,
)
```

**stdout (Agente → Orchestrator):**
```python
# Agente escreve comandos XML durante execução
print("<skybridge_command>...</skybridge_command>", flush=True)

# Ao completar, agente escreve JSON final
print(json.dumps(resultado))
```

**Orchestrator processa streaming:**
```python
# Lê stdout linha por linha
for line in process.stdout:
    if line.startswith("<skybridge_command>"):
        process_command(line)  # Comando em tempo real
    elif line.startswith("{"):
        resultado = json.loads(line)  # JSON final
```

### 6.4.1) Robustez do Protocolo

**Delimitação de Comandos:**
- Comandos XML DEVEM estar em uma única linha
- Linhas iniciando com `<skybridge_command>` são processadas como comandos
- Linhas iniciando com `{` são processadas como JSON final
- Todas outras linhas são consideradas output regular do agente

**Tratamento de Erros:**

| Erro | Comportamento | Recuperação |
|------|---------------|-------------|
| XML malformado | Registrar erro no log, continuar processamento | Ignorar comando com WARNING |
| JSON inválido | Considerar falha de execução | Retornar erro, marcar como `FAILED` |
| Comando desconhecido | Ignorar com WARNING | Continuar execução normalmente |
| Timeout entre comandos | WARNING no log | Continuar aguardando (timeout global é final) |

**Limites:**

| Limite | Valor | Justificativa |
|--------|-------|---------------|
| Tamanho máximo de thinking | 10.000 caracteres | Evita memory exhaustion |
| Tamanho máximo de mensagem de log | 5.000 caracteres | Mantém logs gerenciáveis |
| Número máximo de thinkings | 100 passos | Previne loops infinitos |
| Tamanho máximo de comando XML | 50.000 caracteres | Buffer seguro para parsing |

**Validação de Estrutura:**

```python
# Exemplo de validação (pseudocódigo)
def validate_command(xml_line: str) -> bool:
    if len(xml_line) > 50000:
        return False  # Excede tamanho máximo
    if not xml_line.startswith("<skybridge_command>"):
        return False  # Formato inválido
    if not xml_line.endswith("</skybridge_command>"):
        return False  # XML incompleto
    return True

def validate_thinking(thinking: dict) -> bool:
    if len(thinking.get("thought", "")) > 10000:
        return False  # Thinking muito longo
    if not all(k in thinking for k in ["step", "thought", "timestamp"]):
        return False  # Campos obrigatórios faltando
    return True
```

## 7) System Prompts como Fonte da Verdade

### 7.1) Localização e Formato

System prompts são gerenciados como **fonte da verdade em JSON**:

```
src/skybridge/platform/config/
├── agent_prompts.py         # Módulo de gerenciamento (OBRIGATÓRIO)
│   ├── load_system_prompt_config()     # Carrega JSON
│   ├── render_system_prompt()          # Renderiza template com variáveis
│   ├── save_system_prompt_config()     # Salva JSON modificado
│   └── reset_to_default_prompt()       # Reset para padrão de fábrica
└── system_prompt.json      # Fonte da verdade (OBRIGATÓRIO)
```

### 7.2) Formato do JSON (system_prompt.json)

O JSON é a **fonte da verdade** para os templates de system prompt:

```json
{
  "version": "1.0.0",
  "metadata": {
    "created_at": "2026-01-10T10:00:00Z",
    "updated_at": "2026-01-10T12:00:00Z",
    "description": "System prompt padrão para agentes autônomos"
  },
  "template": {
    "role": "You are an autonomous AI agent that executes development tasks through natural language inference.",
    "instructions": [
      "Work in an isolated Git worktree at {worktree_path}",
      "Communicate with Skybridge via XML commands: <skybridge_command>...</skybridge_command>",
      "NEVER use heuristics - always use inference to analyze and solve problems",
      "Maintain internal log at .sky/agent.log",
      "Return structured JSON output upon completion"
    ],
    "rules": [
      "DO NOT modify files outside the worktree",
      "DO NOT execute destructive actions without confirmation",
      "DO NOT use string matching or if/else heuristics for decisions",
      "ALWAYS read and analyze code before making changes"
    ],
    "output_format": {
      "success": "boolean",
      "files_created": "list of paths",
      "files_modified": "list of paths",
      "files_deleted": "list of paths",
      "thinkings": "list of reasoning steps"
    }
  }
}
```

### 7.3) Renderização do Template

O sistema lê o JSON e **injeta as variáveis** do contexto:

```python
from skybridge.platform.config import load_system_prompt_config, render_system_prompt

# Carregar configuração (fonte da verdade)
config = load_system_prompt_config()  # Lê system_prompt.json

# Contexto do job
context = {
    "worktree_path": "B:\\_repositorios\\skybridge-auto\\github-issues-225-abc123",
    "issue_number": 225,
    "issue_title": "Fix version alignment",
    "repo_name": "skybridge",
    "branch": "main",
}

# Renderizar template com variáveis injetadas
rendered = render_system_prompt(config, context)

# Resultado passado para o agente via --system-prompt
```

**Resultado Renderizado (exemplo):**

```
You are an autonomous AI agent that executes development tasks through natural language inference.

INSTRUCTIONS:
- Work in an isolated Git worktree at B:\_repositorios\skybridge-auto\github-issues-225-abc123
- Communicate with Skybridge via XML commands: <skybridge_command>...</skybridge_command>
- NEVER use heuristics - always use inference to analyze and solve problems
- Maintain internal log at .sky/agent.log
- Return structured JSON output upon completion

RULES:
- DO NOT modify files outside the worktree
- DO NOT execute destructive actions without confirmation
- DO NOT use string matching or if/else heuristics for decisions
- ALWAYS read and analyze code before making changes

OUTPUT FORMAT:
{
  "success": boolean,
  "files_created": ["path1", "path2"],
  "files_modified": ["path3"],
  "files_deleted": ["path4"],
  "thinkings": [...]
}
```

### 7.4) Evolução do System Prompt

O system prompt é uma **entidade viva** que evolui com o projeto:

| Ação | Como |
|------|------|
| **Atualizar** | Editar `system_prompt.json` e incrementar `version` |
| **Versionar** | Commit do JSON no repo com changelog |
| **Resetar** | Chamar `reset_to_default_prompt()` para voltar ao padrão de fábrica |
| **Validar** | Schema JSON com Pydantic antes de usar |

**Atenção:** O JSON é a **fonte da verdade**. Não há "customização" - o padrão é o JSON, e evoluções são feitas editando-o diretamente.

## 8) Interface de Spawn

### 8.1) Assinatura do Comando (Claude Code)

```bash
claude \
  --print \
  --cwd <worktree_path> \
  --system-prompt <contexto> \
  --output-format json \
  --permission-mode bypass \
  --timeout <segundos> \
  <prompt_principal_via_stdin>
```

| Argumento | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `claude` | string | Sim | Executável do Claude Code |
| `--print` | flag | Sim | Modo não-interativo |
| `--cwd` | path | Sim | Diretório de trabalho (worktree isolado) |
| `--system-prompt` | string | Sim | Contexto da tarefa (de `config/agent_prompts.py`) |
| `--output-format` | string | Sim | Formato de saída (json) |
| `--permission-mode` | enum | Sim | Nível de permissão (bypass para worktrees) |
| `--timeout` | int | Não | Timeout em segundos (default: 600) |
| `prompt_principal` | string | Sim | Descrição da tarefa via stdin |

### 8.1.1) Formato de Worktree Path

**Diretório Base Configurável:**

O diretório base para worktrees é **configurável** via `config.py`:

```python
# config.py
WORKTREES_BASE_PATH = Path("B:/_repositorios/skybridge-auto")
```

**Padrão de Nomenclatura:**

```
{WORKTREES_BASE_PATH}/skybridge-{webhook_type}-{event_type}-{issue_id}-{short_id}
```

**Componentes:**

| Componente | Fonte | Exemplo | Descrição |
|------------|-------|---------|-----------|
| `WORKTREES_BASE_PATH` | `config.WORKTREES_BASE_PATH` | `B:\_repositorios\skybridge-auto` | Diretório configurável |
| `webhook_type` | Tipo de webhook | `github` | GitHub, GitLab, Discord |
| `event_type` | Tipo de evento | `issues` | issues, pr, discussion |
| `issue_id` | ID da issue/PR | `225` | Identificador único |
| `short_id` | UUID truncado | `a1b2c3` | Primeiros 6 chars do job ID |

**Exemplos:**

| Cenário | Path Resultante |
|---------|-----------------|
| GitHub Issue #225, job abc123def | `B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123` |
| GitHub PR #456, job xyz789ghi | `B:\_repositorios\skybridge-auto\skybridge-github-pr-456-xyz789` |
| Discord message, job msg123 | `B:\_repositorios\skybridge-auto\skybridge-discord-message-msg123` |

**Requisitos:**

| Requisito | Descrição |
|-----------|-----------|
| **Configurável** | Diretório base definido em `config.WORKTREES_BASE_PATH` |
| **Unicidade** | DEVE ser único por execução (short_id garante isso) |
| **Rastreabilidade** | DEVE incluir identificadores rastreáveis (webhook, issue, job) |
| **Tamanho máximo** | Path completo ≤ 255 caracteres (limite Windows) |
| **Caracteres seguros** | Apenas `[a-z0-9-]` (minúsculas, números, hífens) |

**Validação:**

```python
from pathlib import Path
import re

def generate_worktree_path(
    webhook_type: str,
    event_type: str,
    issue_id: str,
    job_id: str,
    base_path: Path = config.WORKTREES_BASE_PATH
) -> Path:
    """Gera path de worktree seguindo o padrão configurável."""
    short_id = job_id[:6]  # Primeiros 6 caracteres

    worktree_name = f"skybridge-{webhook_type}-{event_type}-{issue_id}-{short_id}"
    path = base_path / worktree_name

    # Validações
    if len(str(path)) > 255:
        raise ValueError(f"Path too long: {len(path)} > 255")

    if not re.match(r'^[a-z0-9-]+$', worktree_name):
        raise ValueError(f"Invalid characters in worktree name: {worktree_name}")

    return path
```

**Configuração no config.py:**

```python
# config.py
from pathlib import Path

# Diretório base para worktrees (configurável por ambiente)
WORKTREES_BASE_PATH = Path("B:/_repositorios/skybridge-auto")

# Garante que o diretório existe
WORKTREES_BASE_PATH.mkdir(parents=True, exist_ok=True)
```

### 8.2) Timeout

**Timeout Global Padrão:** 600 segundos (10 minutos)

A tabela abaixo define timeouts **recomendados por tipo de tarefa**. Se não especificado via `--timeout`, usa-se o valor da tarefa ou o global padrão (600s).

| Tarefa | Timeout Recomendado | Timeout Máximo | Justificativa |
|--------|---------------------|----------------|----------------|
| Hello World | 60s | 120s | Simples, deve ser rápido |
| Bug fix simples | 300s (5min) | 600s | Análise + implementação |
| Bug fix complexo | 600s (10min) | 900s (15min) | Pode demandar pesquisa |
| Refatoração | 900s (15min) | 1200s (20min) | Múltiplos arquivos, análise profunda |

**Comportamento de Timeout:**

| Aspecto | Comportamento |
|---------|---------------|
| **Precedência** | `--timeout` (CLI) > Timeout por skill > Global padrão (600s) |
| **Sinal** | SIGKILL enviado ao processo após timeout |
| **Estado** | `TIMED_OUT` (diferente de `FAILED`) |
| **Thinkings** | Preservados até o momento do timeout |
| **Worktree** | Mantido por 24h para debugging |
| **Recuperação** | Orchestrator pode retry com timeout maior |

**Exemplo de Uso:**

```bash
# Usa timeout recomendado para skill (ex: 300s para bug fix simples)
claude --print --cwd B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123 --skill resolve-issue

# Override com timeout específico
claude --print --cwd B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123 --timeout 900

# Usa global padrão (600s) se não especificado
claude --print --cwd B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123
```

## 9) Protocolo de Comunicação

### 9.1) Entrada (stdin)

Agente recebe contexto via:

1. **Argumentos CLI** (system prompt, cwd, output format)
2. **Arquivos de contexto** no worktree (README.md, docs/, código existente)
3. **Prompt principal** via stdin (último argumento)
4. **Comandos XML** via stdout durante execução (bidirecional)

### 9.2) Saída (stdout)

**Durante execução (streaming):**
```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Analisando issue...</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

**Ao completar (JSON final):**
```json
{
  "success": true | false,
  "changes_made": true | false,
  "files_created": ["path/to/file1.ext", "path/to/file2.ext"],
  "files_modified": ["path/to/file3.ext"],
  "files_deleted": ["path/to/file4.ext"],
  "commit_hash": "abc123def456" | null,
  "pr_url": "https://github.com/org/repo/pull/123" | null,
  "message": "Descrição legível do que foi feito",
  "issue_title": "Fix version alignment between CLI and API",
  "output_message": "Aligned CLI and API versions to 0.2.5",
  "thinkings": [
    {
      "step": 1,
      "thought": "Analisando issue #225 para entender o problema...",
      "timestamp": "2026-01-10T10:30:00Z",
      "duration_ms": 1500
    },
    {
      "step": 2,
      "thought": "Lendo arquivo __init__.py para localizar versões...",
      "timestamp": "2026-01-10T10:30:02Z",
      "duration_ms": 300
    },
    {
      "step": 3,
      "thought": "Identificada discrepância: CLI=0.2.4, API=0.2.5",
      "timestamp": "2026-01-10T10:30:05Z",
      "duration_ms": 200
    },
    {
      "step": 4,
      "thought": "Atualizando versões para 0.2.5 em ambos...",
      "timestamp": "2026-01-10T10:30:10Z",
      "duration_ms": 5000
    }
  ]
}
```

### 9.3) Erros (stderr)

Erros de execução vão para stderr:

```
Error: Failed to analyze repository structure
Caused by: Unable to parse .git/config
```

Orchestrator DEVE capturar stderr para debugging/observabilidade.

## 10) Log Interno do Agente

### 10.1) Localização

```
${WORKTREE_PATH}/.sky/agent.log
```

### 10.2) Formato

```
[2026-01-10T10:30:00.123Z] [INFO] Starting agent execution
[2026-01-10T10:30:01.456Z] [INFO] Reading issue #225 from GitHub
[2026-01-10T10:30:02.789Z] [DEBUG] Analyzing codebase structure
[2026-01-10T10:30:05.012Z] [INFO] Found version mismatch
[2026-01-10T10:30:10.345Z] [INFO] Modified __init__.py
[2026-01-10T10:30:12.678Z] [INFO] Committed changes: abc123
[2026-01-10T10:30:13.901Z] [INFO] Created PR: https://github.com/...
[2026-01-10T10:30:14.234Z] [INFO] Agent execution completed successfully
```

### 10.3) Níveis de Log

| Nível | Uso |
|-------|-----|
| `DEBUG` | Informação detalhada para debugging |
| `INFO` | Eventos normais de execução |
| `WARNING` | Situações anômalas mas não fatais |
| `ERROR` | Erros que impedem progresso |

## 11) Observabilidade

### 11.1) Logs Estruturados

Cada execução de agente DEVE gerar logs com **issue_title, output_message, thinkings**:

```json
{
  "job_id": "github-issues.opened-abc123",
  "agent_type": "claude-code",
  "worktree_path": "/path/to/worktree",
  "skill": "resolve-issue",
  "issue_number": 225,
  "issue_title": "Fix version alignment between CLI and API",
  "output_message": "Aligned CLI and API versions to 0.2.5",
  "timestamps": {
    "created_at": "2026-01-10T10:30:00Z",
    "started_at": "2026-01-10T10:30:01Z",
    "completed_at": "2026-01-10T10:31:00Z"
  },
  "duration_ms": 59000,
  "thinkings": [
    {
      "step": 1,
      "thought": "Analyzing issue #225...",
      "timestamp": "2026-01-10T10:30:01Z",
      "duration_ms": 1500
    },
    {
      "step": 2,
      "thought": "Reading __init__.py...",
      "timestamp": "2026-01-10T10:30:02Z",
      "duration_ms": 300
    }
  ],
  "snapshots": {
    "before": {
      "git_branch": "main",
      "git_hash": "def456",
      "files_count": 150
    },
    "after": {
      "git_branch": "webhook/github/issue/225/abc123",
      "git_hash": "abc123",
      "files_count": 151
    },
    "diff": {
      "files_created": ["hello_world.py"],
      "files_modified": ["__init__.py"],
      "files_deleted": []
    }
  },
  "result": {
    "success": true,
    "changes_made": true,
    "files_created": 1,
    "files_modified": 1,
    "commit_hash": "abc123",
    "pr_url": "https://github.com/.../pull/123"
  }
}
```

### 11.2) Snapshot Antes/Depois

**Snapshot ANTES (pré-execução):**
```json
{
  "timestamp": "2026-01-10T10:30:00Z",
  "worktree_path": "B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123",
  "git": {
    "branch": "webhook/github/issue/225/abc123",
    "hash": "parent_hash",
    "staged": [],
    "unstaged": [],
    "untracked": []
  },
  "files": {
    "count": 150,
    "listing": ["src/", "tests/", "docs/"]
  }
}
```

**Snapshot DEPOIS (pós-execução):**
```json
{
  "timestamp": "2026-01-10T10:31:00Z",
  "worktree_path": "B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123",
  "git": {
    "branch": "webhook/github/issue/225/abc123",
    "hash": "abc123",
    "staged": [],
    "unstaged": [],
    "untracked": []
  },
  "files": {
    "count": 151,
    "listing": ["src/", "tests/", "docs/", "hello_world.py"]
  }
}
```

### 11.3) Métricas

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `agent_spawn_total` | counter | Total de agentes criados |
| `agent_spawn_success` | counter | Agentes que completaram com sucesso |
| `agent_spawn_failed` | counter | Agentes que falharam ou timed out |
| `agent_duration_seconds` | histogram | Duração da execução |
| `agent_thinkings_count` | histogram | Número de passos de raciocínio |
| `agent_files_created` | histogram | Arquivos criados por execução |
| `agent_files_modified` | histogram | Arquivos modificados por execução |
| `agent_worktree_cleanup` | counter | Worktrees limpos após execução |
| `agent_snapshot_diff_files` | histogram | Diff de arquivos (antes/depois) |

## 12) Ciclo de Vida

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Ciclo de Vida do Agente                            │
│                                                                             │
│  [CREATED]                                                                  │
│      │                                                                      │
│      │ subprocess.run(stdin=prompt) + Snapshot ANTES                       │
│      ↓                                                                      │
│  [RUNNING] ← Agente analisa contexto, executa inferência                    │
│      │                                                                      │
│      │ ├─ Envia <skybridge_command> via stdout (streaming)                 │
│      │ ├─ timeout? → [TIMED_OUT] → SIGKILL                                 │
│      │ ├─ erro? → [FAILED] → Captura stderr                                │
│      │ └─ completion? → [COMPLETED]                                        │
│      │                         │                                           │
│      │                         │ Snapshot DEPOIS                           │
│      │                         │ parse stdout + thinkings                  │
│      │                         ↓                                           │
│      │                    [SUCCESS] / [FAILED]                              │
│      │                                                                      │
│      └──────────────────────────────────→ validate + cleanup worktree     │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

Estados possíveis:

| Estado | Descrição |
|--------|-----------|
| `CREATED` | Subprocesso iniciado, stdin enviado, snapshot antes capturado |
| `RUNNING` | Agente executando inferência, enviando comandos via stdout |
| `TIMED_OUT` | Tempo limite excedido, processo terminado |
| `COMPLETED` | Agente finalizou, JSON recebido, snapshot depois capturado |
| `FAILED` | Erro na execução (crash, permission denied, etc) |

## 13) Segurança

### 13.1) Permissões

Agente DEVE operar sob **sandbox de worktree**:

| Operação | Permitida | Observação |
|----------|-----------|------------|
| Read worktree | ✅ | Acesso completo ao worktree |
| Write worktree | ✅ | Criar/modificar arquivos no worktree |
| Read main repo | ✅ | Acesso leitura ao repositório principal |
| Write main repo | ❌ | Proibido escrever fora do worktree |
| Execute commands (git) | ✅ | Comandos git permitidos |
| Execute commands (rm/rf) | ❌ | Comandos destrutivos bloqueados |
| Network access | ⚠️ | Conforme policy do agente |

### 13.2) Validação

Orchestrator DEVE validar **após execução**:

1. **Arquivos criados** estão no worktree
2. **Comandos git** foram executados no worktree
3. **Nenhum arquivo** foi modificado fora do worktree
4. **Commit hash** é válido (se declarado)
5. **PR URL** é válida (se declarada)
6. **Log interno** existe em `.sky/agent.log`

### 13.3) Tratamento de Erros

**Cenários de Falha:**

| Cenário | Comportamento Esperado | Estado Final | Recuperação |
|---------|------------------------|--------------|-------------|
| **Timeout** | Processo terminado via SIGKILL, stderr capturado | `TIMED_OUT` | Preservar thinkings parciais, manter worktree 24h para debug |
| **Crash** | Stderr capturado, worktree mantido para análise | `FAILED` | Gerar bug report com stack trace, manter worktree 24h |
| **Validação falha** | Snapshot depois capturado, diff analisado | `FAILED` | Reverter worktree ou marcar como FAILED, não criar commit/PR |
| **Inferência falha** | Agente retorna `success: false` com mensagem | `FAILED` | Preservar JSON output, thinkings, log interno |
| **Permissão negada** | Erro capturado em stderr, operação bloqueada | `FAILED` | Log detalhado da operação bloqueada |

**Preservação de Estado em Falha:**

```json
{
  "success": false,
  "error_type": "timeout | crash | validation_failed | inference_failed | permission_denied",
  "error_message": "Descrição do erro",
  "stderr": "Output completo do stderr",
  "partial_thinkings": [
    // Thinkings até o momento da falha (DEVE ser sempre preservado)
  ],
  "worktree_preserved": true,
  "worktree_path": "B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123",
  "worktree_retention_hours": 24
}
```

**Regras de Preservação:**
- Thinkings DEVE ser sempre preservado, mesmo em falha
- Log interno `.sky/agent.log` DEVE conter stack trace completo em caso de crash
- Worktree DEVE ser mantido por 24h para debugging em caso de falha
- JSON parcial DEVE ser retornado com `success: false` e campos disponíveis

**Distinção Timeout vs Falha:**
| Aspecto | Timeout | Falha |
|---------|---------|-------|
| **Causa** | Tempo limite excedido | Erro/crash durante execução |
| **Sinal** | SIGKILL pelo orchestrator | Exceção/crash do processo |
| **Estado** | `TIMED_OUT` | `FAILED` |
| **Thinkings** | Parciais (até timeout) | Parciais (até falha) |
| **Stderr** | "Timeout after X seconds" | Stack trace do erro |

### 13.4) Conformidade com SPEC001

Conforme **[SPEC001 — Baseline de Segurança](./SPEC001-baseline-seguranca-llm.md)**, esta especificação DEVE:

| Requisito SPEC001 | Implementação em SPEC008 | Status |
|-------------------|--------------------------|--------|
| **Validação de saída LLM** | Parse JSON com validação de schema; thinkings com limites de tamanho | ✅ Seção 6.4.1, 9.2 |
| **Proteção contra prompt injection** | System prompt sanitizado; escaping de input do usuário | ✅ Seção 7.3 |
| **Sandboxing** | Worktree isolado; permissões limitadas | ✅ Seção 13.1 |
| **Logging estruturado** | `.sky/agent.log` + thinkings estruturados + timestamps | ✅ Seção 10, 11 |
| **Timeout enforcement** | Kill signal em caso de timeout; estados distintos | ✅ Seção 8.2, 13.3 |
| **Observabilidade** | Snapshots antes/depois; métricas; logs estruturados | ✅ Seção 11 |
| **Validação de input** | Validação de XML comandos; limites de tamanho | ✅ Seção 6.4.1 |

**Mapeamento Detalhado:**

```python
# Exemplo de conformidade com SPEC001

from pydantic import BaseModel, validator

class AgentOutput(BaseModel):
    """Validação de saída LLM (SPEC001 requirement)"""
    success: bool
    changes_made: bool
    files_created: list[str]
    files_modified: list[str]
    files_deleted: list[str]
    thinkings: list[dict]

    @validator("thinkings")
    def validate_thinkings(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 thinkings allowed")
        for t in v:
            if len(t.get("thought", "")) > 10000:
                raise ValueError("Thinking too long")
        return v
```

## 14) Versionamento

### 14.1) Escopo de Versionamento

O bounded context `webhooks/` possui versionamento independente do core Skybridge:

| Componente | Versionamento | Escopo |
|------------|---------------|--------|
| Skybridge Core | SemVer (X.Y.Z) | Main repo |
| Webhooks BC | SemVer próprio | `src/skybridge/core/contexts/webhooks/` |

### 14.2) Compatibilidade

Mudanças breaking no bounded context `webhooks/` requerem:

* Incrementar versão MAJOR do BC (ex: `0.3.0` → `1.0.0`)
* Atualizar implementação do orchestrator
* Manter compatibilidade com agentes legados via feature flag

## 15) Compatibilidade

### 15.1) Agentes Suportados

| Agente | CLI | Status | Observações |
|--------|-----|--------|-------------|
| **Claude Code** | `claude` | ✅ Principal | Anthropic, inferência via Claude 3.5+ |
| **Roo Code** | `roocode` | 🔮 Futuro | Open source, autônomo |
| **GitHub Copilot** | `copilot-cli` | 🔮 Futuro | GitHub, integration pendente |
| **Criador de Issue** | `claude` | 🔮 Futuro | Skill `/create-issue`, coordena workflow (ver SPEC009) |
| **Testador de Issue** | `claude` | 🔮 Futuro | Skill `/test-issue`, valida testes (ver SPEC009) |
| **Desafiador de Qualidade** | `claude` | 🔮 Futuro | Skill `/challenge-quality`, ataques adversariais (ver SPEC009) |

**Nota:** Os agentes Criador, Testador e Desafiador são especializações do Claude Code com skills específicas definidas em SPEC009 — Orquestração de Workflow Multi-Agente.

## 16) Exemplos

### 16.1) Exemplo 1: Resolução de Issue (Inferência Real)

```bash
# Entrada via stdin
SYSTEM_PROMPT=$(get_system_prompt_template | render -context)
echo "Resolve issue #225: Fix version alignment" | claude --print \
  --cwd B:\_repositorios\skybridge-auto\skybridge-github-issues-225-abc123 \
  --system-prompt "${SYSTEM_PROMPT}" \
  --output-format json \
  --permission-mode bypass \
  --timeout 600

# Saída JSON (stdout)
{
  "success": true,
  "changes_made": true,
  "files_created": [],
  "files_modified": ["src/skybridge/__init__.py"],
  "files_deleted": [],
  "commit_hash": "a1b2c3d4",
  "pr_url": "https://github.com/h4mn/skybridge/pull/226",
  "issue_title": "Fix version alignment between CLI and API",
  "output_message": "Aligned CLI and API versions to 0.2.5",
  "message": "Aligned CLI and API versions to 0.2.5",
  "thinkings": [
    {"step": 1, "thought": "Analyzing issue...", "timestamp": "...", "duration_ms": 1500},
    {"step": 2, "thought": "Reading __init__.py...", "timestamp": "...", "duration_ms": 300},
    {"step": 3, "thought": "Found mismatch: CLI=0.2.4, API=0.2.5", "timestamp": "...", "duration_ms": 200},
    {"step": 4, "thought": "Updating both to 0.2.5...", "timestamp": "...", "duration_ms": 5000}
  ]
}
```

### 16.2) Exemplo 2: skybridge_command vs Script Gerado

**Cenário**: Issue pede "Create hello world script"

**Passo 1 - Agente usa INFERÊNCIA para entender a issue:**
```json
{
  "step": 1,
  "thought": "Issue requests creation of hello world script",
  "timestamp": "2026-01-10T10:30:00Z",
  "duration_ms": 500
}
```

**Passo 2 - Agente comunica-se com Skybridge (skybridge_command):**
```xml
<skybridge_command>
  <command>log</command>
  <parametro name="mensagem">Starting hello world script creation</parametro>
  <parametro name="nivel">info</parametro>
</skybridge_command>
```

**Passo 3 - Agente CRIA o arquivo via inferência (script hello_world.py):**
```python
# Conteúdo do arquivo criado pelo agente
#!/usr/bin/env python3
"""
Hello World Script

Created by Skybridge Autonomous Agent
"""

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

**Passo 4 - Agente envia resultado final:**
```json
{
  "success": true,
  "files_created": ["hello_world.py"],
  "issue_title": "Create hello world script",
  "output_message": "Created hello_world.py script",
  "thinkings": [
    {"step": 1, "thought": "Understood issue: create hello world", ...},
    {"step": 2, "thought": "Sent log command to Skybridge", ...},
    {"step": 3, "thought": "Created hello_world.py with proper structure", ...},
    {"step": 4, "thought": "Verified script runs correctly", ...}
  ]
}
```

**Diferença Clara:**

| Aspecto | skybridge_command | hello_world.py |
|---------|-------------------|----------------|
| **O que é** | Protocolo de comunicação | Arquivo criado |
| **Quem cria** | Agente envia para Skybridge | Agente gera via inferência |
| **Formato** | XML | Python |
| **Propósito** | Comunicar progresso | Resolver a issue |

### 16.3) Exemplo 3: Streaming stdin/stdout

```python
# Orchestrator cria agente
process = subprocess.Popen(
    ["claude", "--print", "--cwd", worktree, "--system-prompt", prompt],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

# Envia prompt principal via stdin
process.stdin.write(main_prompt)
process.stdin.close()

# Processa stdout em tempo real
while True:
    line = process.stdout.readline()
    if not line:
        break

    if line.strip().startswith("<skybridge_command>"):
        # Comando XML em tempo real
        cmd = parse_xml_command(line)
        logger.info(f"Agent command: {cmd['command']}")
    elif line.strip().startswith("{"):
        # JSON final
        result = json.loads(line)
        break
```

## 17) Referências

* [PRD013 — Webhook-Driven Autonomous Agents](../prd/PRD013-webhook-autonomous-agents.md)
* [SPEC001 — Baseline de Segurança](./SPEC001-baseline-seguranca-llm.md)
* [SPEC007 — Snapshot Service](./SPEC007-Snapshot-Service.md)
* [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
* [Claude Code Documentation](https://code.claude.com/docs/en/overview)
* [Relatório: Bounded Context Analysis](../report/bounded-context-analysis-agents.md)
* [Relatório: Claude Code CLI Infra](../report/claude-code-cli-infra.md)
* [agent_spawner.py](../../src/skybridge/core/contexts/webhooks/application/agent_spawner.py)
* [agent_prompts.py](../../src/skybridge/platform/config/agent_prompts.py)

---

> "Um agente sem inferência é apenas um script com marketing" – made by Sky 🤖

> "Observabilidade completa é a diferença entre 'funciona' e 'funciona bem'" – made by Sky 📊

> "System prompts são entidades vivas que evoluem com o projeto" – made by Sky 🌱
