# Comparação: Integração GitHub - Auto-Claude vs Skybridge

**Data:** 2026-01-14
**Analista:** Sky
**Foco:** Como cada projeto integra com GitHub

---

## 1. Visão Geral dos Enfoques

### Auto-Claude: Poll-Based via GitHub CLI (gh)
- **Abordagem:** Pull-based (polling ativo)
- **Ferramenta:** GitHub CLI (`gh`)
- **Comunicação:** CLI commands com subprocess async
- **Modo:** CLI-driven com comandos manuais

### Skybridge: Event-Driven via Webhooks
- **Abordagem:** Push-based (eventos em tempo real)
- **Ferramenta:** Webhooks HTTP + JSON-RPC
- **Comunicação:** HTTP POST com signature verification
- **Modo:** Event-driven com job queue assíncrona

---

## 2. Arquitetura de Integração

### 2.1 Auto-Claude

```
┌─────────────────────────────────────────────────────────────┐
│                    Auto-Claude GitHub Runner                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  CLI Entry Point: runner.py                                  │
│  - review-pr [PR#]                                           │
│  - triage [issue#]                                           │
│  - auto-fix [issue#]                                         │
│  - batch-issues                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Orchestrator: orchestrator.py                               │
│  - Coordenador principal                                     │
│  - Gerencia workflows: review, triage, auto-fix, batch       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  PRReviewEngine   │ │ TriageEngine │ │ AutoFixProcessor │
│  services/        │ │ services/    │ │ services/        │
└──────────────────┘ └──────────────┘ └──────────────────┘
                │             │             │
                └─────────────┼─────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  GHClient: gh_client.py                                      │
│  - Wrapper para GitHub CLI                                   │
│  - Timeout + retry + rate limiting                           │
│  - Async subprocess execution                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  GitHub CLI (gh)                                            │
│  - Comandos: pr list, pr diff, pr review, issue view, etc  │
│  - Authentication via OAuth token                           │
│  - API proxy via CLI                                        │
└─────────────────────────────────────────────────────────────┘
```

**Componentes Principais:**
1. **runner.py** - CLI entry point com comandos
2. **orchestrator.py** - Coordenador de workflows
3. **gh_client.py** - Client GitHub CLI com timeout/retry
4. **services/** - Camada de serviços especializados
   - `PRReviewEngine` - Multi-pass code review
   - `TriageEngine` - Issue classification
   - `AutoFixProcessor` - Automatic spec creation & execution
   - `BatchProcessor` - Batch similar issues

**Workflow Típico:**
```bash
# 1. Usuário executa comando manual
python runner.py review-pr 123

# 2. Orchestrator cria workflow
# 3. GHClient executa comandos gh async
# 4. Agentes processam dados
# 5. Resultados são postados no GitHub
```

---

### 2.2 Skybridge

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Webhook Event (HTTP POST)                           │
│  - Payload JSON                                             │
│  - X-Hub-Signature-256 header                               │
│  - X-GitHub-Event header                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Endpoint: /webhooks/github                         │
│  - Signature verification                                   │
│  - Body parsing                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Webhook Processor: webhook_processor.py                   │
│  - Valida evento                                             │
│  - Cria WebhookJob                                          │
│  - Enfileira para processamento                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Job Queue: InMemoryJobQueue                               │
│  - Fila assíncrona                                          │
│  - Status tracking                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Job Orchestrator: job_orchestrator.py                     │
│  - Dequeue job                                               │
│  - Create worktree                                          │
│  - Capture snapshot                                          │
│  - Execute agent                                             │
│  - Validate worktree                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent Facade: ClaudeCodeAdapter                            │
│  - Spawna subagente no worktree                             │
│  - Executa skill (/resolve-issue, /respond-discord)        │
│  - Streaming em tempo real                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Git Worktree (isolado)                                     │
│  - Branch: auto-claude/{issue-#}                           │
│  - Modificações ficam isoladas                              │
│  - Preservado para inspeção manual                          │
└─────────────────────────────────────────────────────────────┘
```

**Componentes Principais:**
1. **handlers.py** - Sky-RPC command handler (`webhooks.github.receive`)
2. **webhook_processor.py** - Processador de eventos webhook
3. **job_orchestrator.py** - Orquestrador de jobs (worktree → agent → validate)
4. **worktree_manager.py** - Gerenciador de git worktrees
5. **claude_agent.py** - Facade para Claude Code agent
6. **in_memory_queue.py** - Job queue assíncrona

**Workflow Típico:**
```json
// 1. GitHub envia webhook
POST /webhooks/github
{
  "action": "opened",
  "issue": {"number": 225},
  "repository": {"name": "skybridge"}
}

// 2. Processador cria job
// 3. Job entra na fila
// 4. Orchestrator:
//    - Cria worktree
//    - Captura snapshot inicial
//    - Spawna agente /resolve-issue
//    - Valida worktree (preserva)
// 5. Worktree fica disponível para merge manual
```

---

## 3. Comparação Detalhada por Dimensão

### 3.1 Modelo de Comunicação

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Padrão** | Pull (Polling) | Push (Event-driven) |
| **Iniciador** | CLI/Humano | GitHub webhook |
| **Latência** | Manual/On-demand | Real-time |
| **Autonomia** | Baixa (requer comando) | Alta (automático) |
| **Escalabilidade** | Limitada (um comando por vez) | Alta (fila assíncrona) |

**Auto-Claude:**
```python
# Pull-based - usuário executa comando
result = await orchestrator.review_pr(pr_number=123)
```

**Skybridge:**
```python
# Push-based - GitHub envia evento automaticamente
@command(name="webhooks.github.receive")
def receive_github_webhook(args: dict):
    # Processa webhook automaticamente
    await processor.process_github_issue(payload, event_type)
```

---

### 3.2 Autenticação e Segurança

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Mecanismo** | GitHub OAuth token | HMAC signature + OAuth token |
| **Token Storage** | `.env` (GITHUB_TOKEN, GITHUB_BOT_TOKEN) | `.env` (webhook secret) |
| **Validação** | CLI handles auth | Signature verification |
| **Bot Detection** | ✅ Sim (bot_detector.py) | ❌ Não implementado |

**Auto-Claude:**
```python
# gh_client.py - Usa token OAuth
token = os.environ.get("GITHUB_TOKEN")
cmd = ["gh", "pr", "view", "123", "-R", repo]
proc = await asyncio.create_subprocess_exec(*cmd)
```

**Skybridge:**
```python
# webhook_processor.py - Verifica HMAC signature
if signature:
    # Validar payload com webhook secret
    # (Ainda não implementado totalmente)
```

---

### 3.3 Tipos de Eventos Suportados

| Event Type | Auto-Claude | Skybridge |
|------------|-------------|-----------|
| **issues.opened** | ✅ triage → auto-fix | ✅ resolve-issue |
| **issues.edited** | ✅ triage | ✅ resolve-issue |
| **issues.closed** | ❌ Não processa | ✅ Skip (não executa agente) |
| **issues.labeled** | ✅ triage | ✅ Skip |
| **pull_request.opened** | ✅ review-pr | ❌ TODO |
| **pull_request.updated** | ✅ followup-review-pr | ❌ TODO |
| **pull_request.reviewed** | ❌ Não processa | ❌ TODO |
| **issue_comment.created** | ❌ Não processa | ✅ TODO: respond-discord |

**Auto-Claude:**
```python
# runner.py - Comandos específicos
review-pr 123         # Review pull request
triage 456            # Triage issue
auto-fix 456          # Create spec + execute
batch-issues          # Group similar issues
```

**Skybridge:**
```python
# job_orchestrator.py - Mapeamento evento → skill
EVENT_TYPE_TO_SKILL = {
    "issues.opened": "resolve-issue",
    "issues.reopened": "resolve-issue",
    "issues.edited": "resolve-issue",
    "issues.closed": None,  # Não executa agente
    "issue_comment.created": "respond-discord",  # TODO
    "pull_request.opened": None,  # TODO
}
```

---

### 3.4 Orquestração e Workflow

### Auto-Claude: Multi-Workflow Orchestrator

```python
class GitHubOrchestrator:
    """Coordena múltiplos workflows independentes"""

    async def review_pr(self, pr_number: int):
        """Workflow: PR Review"""
        # 1. ContextGatherer: coleta contexto do PR
        context = await context_gatherer.gather(pr_number)

        # 2. BotDetector: verifica se é próprio bot
        if bot_detector.is_own_pr(pr_number):
            return Result.err("Skipping own PR")

        # 3. PRReviewEngine: executa review em múltiplos passes
        result = await pr_review_engine.review(pr_number)

        # 4. GHClient: posta review no GitHub
        await gh_client.pr_review(pr_number, body=result.summary)

    async def auto_fix_issue(self, issue_number: int):
        """Workflow: Auto-Fix Issue"""
        # 1. PermissionChecker: autoriza usuário
        if not permission_checker.can_auto_fix(issue_number):
            return Result.err("Unauthorized")

        # 2. TriageEngine: classifica issue
        triage = await triage_engine.triage(issue_number)

        # 3. AutoFixProcessor: cria spec + executa
        state = await autofix_processor.process(issue_number)

        # 4. Cria PR com correções
        await gh_client.create_pr(...)
```

**Características:**
- Múltiplos workflows independentes (review, triage, auto-fix, batch)
- Cada workflow é executado como comando separado
- Serviços especializados (PRReviewEngine, TriageEngine, etc.)
- Rate limiting e bot detection integrados

---

### Skybridge: Single-Job Orchestrator

```python
class JobOrchestrator:
    """Orquestra execução de jobs de webhook"""

    async def execute_job(self, job_id: str):
        """Workflow único para todos os eventos"""
        # 1. Dequeue job
        job = await job_queue.get_job(job_id)

        # 2. Determina skill pelo event_type
        skill = EVENT_TYPE_TO_SKILL.get(job.event.event_type)
        if skill is None:
            return Result.ok("Skipped")

        # 3. Create worktree isolado
        worktree_result = worktree_manager.create_worktree(job)

        # 4. Capture snapshot inicial
        initial_snapshot = git_extractor.capture(worktree_path)

        # 5. Execute agent com skill específico
        agent_result = await agent_adapter.spawn(
            job=job,
            skill=skill,  # /resolve-issue, /respond-discord
            worktree_path=worktree_path,
        )

        # 6. Valida worktree (preserva para inspeção)
        validation_result = self._validate_worktree(job)

        return Result.ok({
            "worktree_path": job.worktree_path,
            "branch_name": job.branch_name,
        })
```

**Características:**
- Workflow único para todos os eventos
- Determina skill baseado em event_type
- Worktree isolado sempre criado
- Snapshot antes/depois para diff
- Worktree preservado para inspeção manual

---

### 3.5 Client GitHub

### Auto-Claude: GHClient (GitHub CLI Wrapper)

```python
class GHClient:
    """
    Wrapper async para GitHub CLI com timeout e retry.
    """

    async def run(self, args: list[str], timeout: float):
        """
        Executa comando gh com:
        - Timeout protection (default 30s)
        - Exponential backoff retry (3 tentativas)
        - Rate limiting integrado
        """
        cmd = ["gh"] + args

        # Rate limit check
        if self.enable_rate_limiting:
            await self._rate_limiter.acquire_github()

        # Execute com retry
        for attempt in range(1, self.max_retries + 1):
            proc = await asyncio.create_subprocess_exec(*cmd)

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                return GHCommandResult(stdout, stderr, proc.returncode)
            except asyncio.TimeoutError:
                # Kill hung process
                proc.kill()
                await asyncio.sleep(2 ** (attempt - 1))  # Backoff
                continue

    # Métodos de conveniência
    async def pr_get(self, pr_number: int):
        return await self.run(["pr", "view", str(pr_number), "--json", "all"])

    async def pr_diff(self, pr_number: int):
        return await self.run(["pr", "diff", str(pr_number)])

    async def pr_review(self, pr_number: int, body: str, event: str):
        return await self.run(["pr", "review", str(pr_number), "--body", body, "--event", event])

    async def issue_get(self, issue_number: int):
        return await self.run(["issue", "view", str(issue_number), "--json", "all"])
```

**Características:**
- Usa GitHub CLI como proxy para API
- Timeout + retry + rate limiting
- Async subprocess execution
- Prevenção de processos pendurados

---

### Skybridge: Git Worktree Manager (Sem client GitHub direto)

```python
class WorktreeManager:
    """Gerencia git worktrees para jobs"""

    def create_worktree(self, job: WebhookJob) -> Result[str]:
        """
        Cria worktree isolado para o job.

        Naming convention: auto-claude/{event_type}-{issue-#}
        Ex: auto-claude/issue-225
        """
        # 1. Determina nome da branch
        branch_name = f"auto-claude/{job.event.event_type}-{job.issue_number}"

        # 2. Cria worktree
        subprocess.run(["git", "worktree", "add", worktree_path, branch_name])

        # 3. Atualiza job
        job.branch_name = branch_name
        job.worktree_path = worktree_path

        return Result.ok(worktree_path)
```

**Características:**
- Não usa GitHub CLI diretamente
- Usa git nativo para worktrees
- Preserva worktree após execução
- Foco em isolamento, não em comunicação com GitHub

---

### 3.6 Rate Limiting e Throttling

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Rate Limiter** | ✅ Sim (rate_limiter.py) | ❌ Não implementado |
| **Token Bucket** | ✅ 5000 requests/hour (GitHub standard) | ❌ N/A |
| **Backoff Strategy** | Exponential (1s, 2s, 4s) | ❌ N/A |
| **Queue Batching** | ❌ Não usa fila | ✅ Job queue assíncrona |

**Auto-Claude:**
```python
class RateLimiter:
    """Singleton rate limiter para GitHub API"""

    async def acquire_github(self, timeout: float = 30.0):
        """
        Aguarda disponibilidade de token.
        Usa token bucket: 5000/hour para authenticated.
        """
        while not self._check_token_available():
            await asyncio.sleep(1.0)  # Polling loop

        self._consume_token()
        return True
```

**Skybridge:**
- Não possui rate limiting
- Jobs são enfileirados mas não limitados
- Risco de flood se GitHub enviar muitos eventos

---

### 3.7 Detecção de Bot e Auto-Contenção

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Bot Detection** | ✅ Sim (bot_detector.py) | ❌ Não implementado |
| **Self-Review** | Evita review de próprios PRs | ❌ N/A |
| **Infinite Loop Prevention** | ✅ Rastrea bot comments | ❌ N/A |

**Auto-Claude:**
```python
class BotDetector:
    """Previne loops infinitos de bot review"""

    async def is_own_pr(self, pr_number: int) -> bool:
        """Verifica se PR foi criado pelo bot"""
        # Checa autor do PR
        pr_author = await gh_client.pr_get_author(pr_number)

        # Checa se bot token criou
        if pr_author == bot_username:
            return True

        # Checa se já revisou antes
        if self._has_already_reviewed(pr_number):
            return True

        return False
```

**Skybridge:**
- Não detecta bot
- Não rastreia revisões anteriores
- Risco de loop se webhook dispara commits

---

### 3.8 Permissões e Autorização

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Permission Checker** | ✅ Sim (permissions.py) | ❌ Não implementado |
| **Role-Based Access** | ✅ Configurável | ❌ N/A |
| **External Contributors** | ✅ Controle granular | ❌ N/A |
| **Auto-Fix Authorization** | ✅ Opcional por role | ❌ N/A |

**Auto-Claude:**
```python
class GitHubPermissionChecker:
    """Verifica permissões para auto-fix"""

    def can_auto_fix(self, issue_number: int) -> bool:
        """
        Autoriza auto-fix baseado em:
        - Role do usuário (maintainer, collaborator, etc)
        - Configuração allow_external_contributors
        """
        user = await gh_client.get_issue_author(issue_number)

        # Check role
        if user.role not in config.auto_fix_allowed_roles:
            return False

        # Check external contributor
        if user.is_external and not config.allow_external_contributors:
            return False

        return True
```

**Skybridge:**
- Não verifica permissões
- Qualquer issue pode spawnar agent
- Risco de abuso se repositório público

---

### 3.9 Batch Processing e Agrupamento

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Batch Similar Issues** | ✅ Sim (batch_issues.py) | ❌ Não implementado |
| **Semantic Clustering** | ✅ Embeddings + similarity | ❌ N/A |
| **Theme Extraction** | ✅ AI-powered | ❌ N/A |
| **Batch Spec Creation** | ✅ Um spec para múltiplas issues | ❌ N/A |

**Auto-Claude:**
```python
class BatchProcessor:
    """Agrupa issues similares e cria specs combinadas"""

    async def batch_and_fix_issues(self, issue_numbers: list[int]):
        """
        Workflow:
        1. Coleta contexto de todas issues
        2. Calcula similaridade (embeddings)
        3. Agrupa issues por tema
        4. Cria spec combinado
        5. Executa auto-fix para o batch
        """
        # Coleta embeddings
        embeddings = await self._get_embeddings(issue_numbers)

        # Agrupa por similaridade (>0.8)
        batches = self._cluster_issues(embeddings, threshold=0.8)

        # Cria specs combinados
        for batch in batches:
            spec = await self._create_batch_spec(batch)
            await autofix_processor.execute(spec)
```

**Skybridge:**
- Processa cada issue individualmente
- Não agrupa issues similares
- Cada webhook = um job separado

---

### 3.10 Context Gathering e Memory

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Context Gatherer** | ✅ Sim (context_gatherer.py) | ✅ Snapshot (git_extractor.py) |
| **Multi-Source Context** | ✅ Files, PR comments, commits, etc | ✅ Git stats + structure |
| **Memory Integration** | ✅ Graphiti (long-term) | ❌ Snapshot apenas (curto prazo) |
| **Semantic Search** | ✅ Graphiti embeddings | ❌ N/A |

**Auto-Claude:**
```python
class PRContextGatherer:
    """Coleta contexto multi-fonte para PR review"""

    async def gather(self, pr_number: int) -> PRContext:
        """
        Coleta:
        - PR metadata
        - Diff completo
        - Comentários do PR
        - Commits anteriores
        - Arquivos modificados
        - Issues relacionadas
        - Memory context (Graphiti)
        """
        context = PRContext()

        # GitHub data
        context.pr_data = await gh_client.pr_get(pr_number)
        context.diff = await gh_client.pr_diff(pr_number)
        context.comments = await gh_client.pr_comments(pr_number)

        # Memory (Graphiti)
        context.memory = await graphiti.get_context_for_pr(pr_number)

        # File analysis
        context.files = await self._analyze_files(context.pr_data.files)

        return context
```

**Skybridge:**
```python
class GitExtractor:
    """Extrai snapshot do repositório"""

    def capture(self, repo_path: str) -> GitSnapshot:
        """
        Captura:
        - Metadata (branch, commit, author, timestamp)
        - Stats (files, lines, additions, deletions)
        - Structure (diretórios e tipos de arquivos)
        """
        # Git metadata
        metadata = GitMetadata(
            branch=self._get_current_branch(),
            commit=self._get_current_commit(),
            author=self._get_author(),
            timestamp=datetime.utcnow(),
        )

        # Git stats
        stats = GitStats(
            total_files=self._count_files(),
            total_lines=self._count_lines(),
            additions=self._count_additions(),
            deletions=self._count_deletions(),
        )

        # Repository structure
        structure = self._get_directory_structure()

        return GitSnapshot(metadata, stats, structure)
```

---

### 3.11 QA e Validação

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **QA Loop** | ✅ Automático (qa_loop.py) | ✅ Validação (worktree_validator.py) |
| **Multi-Pass Review** | ✅ 2-3 passes | ✅ Snapshot diff |
| **E2E Testing** | ✅ Electron MCP | ❌ Não implementado |
| **Follow-up Review** | ✅ Detecta mudanças pós-review | ❌ N/A |

**Auto-Claude:**
```python
class QAEngine:
    """Validação automatizada com E2E testing"""

    async def validate_spec(self, spec_id: str):
        """
        QA Loop:
        1. QA Reviewer valida acceptance criteria
        2. Se falha: QA Fixer corrige
        3. Repete até sucesso ou max attempts
        """
        for attempt in range(1, self.max_attempts + 1):
            # Reviewer
            review_result = await qa_reviewer.validate(spec_id)

            if review_result.passed:
                return Result.ok("QA passed")

            # Fixer
            await qa_fixer.fix(spec_id, review_result.issues)

            # E2E testing (Electron MCP)
            if self.electron_mcp_enabled:
                await self._run_e2e_tests(spec_id)
```

**Skybridge:**
```python
def safe_worktree_cleanup(worktree_path: str, dry_run: bool):
    """
    Valida worktree antes de remover.

    Checkpoints:
    - Branch está limpa (unmerged changes)
    - Não há staged changes
    - Untracked files são permitidos
    """
    # Git status
    status = subprocess.run(
        ["git", "-C", worktree_path, "status", "--porcelain"],
        capture_output=True,
    )

    # Parse status
    staged = len([line for line in status.stdout if line.startswith(("A ", "M "))])
    unstaged = len([line for line in status.stdout if line.startswith(("AM", "MM"))])

    if staged > 0 or unstaged > 0:
        return {
            "can_remove": False,
            "status": {"staged": staged, "unstaged": unstaged},
        }

    return {"can_remove": True, "status": {}}
```

---

### 3.12 Preservação de Estado

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **Job State** | ✅ .auto-claude/github/ | ✅ Job queue + worktree |
| **Worktree Cleanup** | ❌ Remove após sucesso | ✅ Preserva para inspeção |
| **History Tracking** | ✅ Memory (Graphiti) | ❌ Snapshot inicial/final |
| **Recovery** | ✅ Reexecução possível | ❌ Trabalho perdido se worktree removido |

**Auto-Claude:**
```python
# .auto-claude/github/ structure
.github/
├── auto-fix/
│   └── 456/
│       ├── state.json
│       ├── spec_id
│       └── pr_number
├── batch/
│   └── batch-123/
│       ├── issues.json
│       └── spec_id
└── reviews/
    └── pr-123/
        └── findings.json
```

**Skybridge:**
```python
# Job state in queue + worktree preservation
{
    "job_id": "uuid",
    "status": "completed",
    "worktree_path": ".git/worktrees/auto-claude/issue-225",
    "branch_name": "auto-claude/issues.opened-225",
    "initial_snapshot": {...},
    "validation": {
        "can_remove": False,  # Preservado!
        "status": {"staged": 5, "unstaged": 0}
    }
}
```

---

### 3.13 Frontend Integration

| Aspecto | Auto-Claude | Skybridge |
|---------|-------------|-----------|
| **UI Integration** | ✅ Electron Kanban Board | ❌ Apenas CLI |
| **Real-time Progress** | ✅ ProgressCallback | ❌ Apenas logs |
| **Status Dashboard** | ✅ Kanban + Agents Terminals | ❌ Apenas CLI |
| **Auto-Post Comments** | ✅ Bot token | ❌ Não implementado |

**Auto-Claude:**
```python
# Frontend → Backend integration
@command(name="github.review-pr")
async def review_pr(args: dict):
    """Chamado via Electron UI"""
    pr_number = args["pr_number"]

    # Orchestrator com progress callback para UI
    orchestrator = GitHubOrchestrator(
        project_dir=project_dir,
        config=config,
        progress_callback=lambda cb: ui.update_progress(cb),
    )

    result = await orchestrator.review_pr(pr_number)
    return result.to_dict()
```

**Skybridge:**
```python
# CLI apenas
sb webhooks github receive \
  --payload @webhook-payload.json \
  --event-type issues.opened \
  --signature sha256=abc123

# ou via FastAPI endpoint
curl -X POST http://localhost:8000/webhooks/github \
  -H "X-Hub-Signature-256: sha256=..." \
  -H "X-GitHub-Event: issues" \
  -d @webhook-payload.json
```

---

## 4. Tabela Comparativa Resumida

| Dimensão | Auto-Claude | Skybridge |
|----------|-------------|-----------|
| **Comunicação** | Pull (CLI) | Push (Webhook) |
| **Autenticação** | OAuth token | HMAC + OAuth |
| **Rate Limiting** | ✅ Token bucket | ❌ Não |
| **Bot Detection** | ✅ Sim | ❌ Não |
| **Permissões** | ✅ Role-based | ❌ Não |
| **Batch Processing** | ✅ Similarity clustering | ❌ Individual |
| **Memory** | ✅ Graphiti (long-term) | ❌ Snapshot (curto) |
| **QA** | ✅ Multi-pass + E2E | ✅ Validação worktree |
| **Worktree** | ❌ Remove após sucesso | ✅ Preserva sempre |
| **Frontend** | ✅ Electron UI | ❌ CLI apenas |
| **Maturidade** | ✅ Produção (v2.7.4) | ⚠️ PoC (0.1.0) |
| **Eventos Suportados** | PR review, triage, auto-fix, batch | Issues (partial), TODO: PRs |

---

## 5. Prós e Contras

### 5.1 Auto-Claude

**Prós:**
✅ Rate limiting integrado (evita bloqueio GitHub)
✅ Bot detection (previne loops infinitos)
✅ Role-based permissions (controle de acesso)
✅ Batch processing (agrupa issues similares)
✅ Graphiti memory (long-term context)
✅ Multi-pass QA (validação robusta)
✅ Electron UI (progresso em tempo real)
✅ Multiple workflows (review, triage, auto-fix, batch)

**Contras:**
❌ Pull-based (requer comando manual)
❌ Depende de GitHub CLI
❌ Remove worktree após sucesso (dificulta inspeção)
❌ Complexidade alta (múltiplos serviços)
❌ Não event-driven (latência manual)

---

### 5.2 Skybridge

**Prós:**
✅ Event-driven (resposta em tempo real)
✅ Job queue assíncrona (escalável)
✅ Worktree preservation (fácil inspeção)
✅ Snapshot antes/depois (auditabilidade)
✅ Arquitetura simples (single workflow)
✅ DDD rigoroso (separação de responsabilidades)
✅ Não depende de GitHub CLI

**Contras:**
❌ Sem rate limiting (risco de flood)
❌ Sem bot detection (possível loop)
❌ Sem permissões (risco de abuso)
❌ Sem batch processing (ineficiente para issues similares)
❌ Sem long-term memory (perde contexto entre jobs)
❌ Sem frontend UI (apenas CLI)
❌ Apenas issues (PRs não implementados)

---

## 6. Conclusão

### 6.1 Diferenças Fundamentais

**Modelo de Comunicação:**
- **Auto-Claude:** Pull-based - Usuário executa comando, sistema puxa dados do GitHub
- **Skybridge:** Push-based - GitHub envia evento, sistema processa automaticamente

**Escopo:**
- **Auto-Claude:** Multi-funcional (review, triage, auto-fix, batch)
- **Skybridge:** Focado em issues (PRs TODO)

**Maturidade:**
- **Auto-Claude:** Produção com proteções (rate limit, bot detection, permissions)
- **Skybridge:** PoC com arquitetura sólida mas sem proteções

---

### 6.2 Quando Usar Qual

**Use Auto-Claude se:**
- Precisa de PR review automatizado
- Quer triage de issues com AI
- Precisa de auto-fix para issues
- Quer batch processing de issues similares
- Requer UI visual com progresso em tempo real
- Precisa de proteções (rate limit, bot detection, permissions)
- Quer long-term memory (Graphiti)

**Use Skybridge se:**
- Quer resposta em tempo real a webhooks
- Precisa de processamento assíncrono escalável
- Prefere worktrees preservados para inspeção
- Quer arquitetura simples e extensível
- Prefere DDD rigoroso
- Não quer depender de GitHub CLI
- Precisa de workflow customizável via skills

---

### 6.3 Recomendações de Evolução

**Para Skybridge:**
1. Implementar rate limiting (token bucket)
2. Adicionar bot detection (previne loops)
3. Implementar permission checker (role-based)
4. Adicionar batch processing (agrupar issues similares)
5. Integrar Graphiti (long-term memory)
6. Implementar PR review workflow
7. Criar frontend UI (opcional, pode ser web-based)

**Para Auto-Claude:**
1. Considerar webhook-driven mode (resposta em tempo real)
2. Preservar worktrees para inspeção manual
3. Implementar snapshot diff (auditabilidade)
4. Adicionar arquitetura DDD mais rigorosa
5. Considerar job queue para escalabilidade
6. Reduzir dependência de GitHub CLI

---

## 7. Referências

### Auto-Claude
- **Runner:** B:\_repositorios\auto-claude\apps\backend\runners\github\runner.py
- **Orchestrator:** B:\_repositorios\auto-claude\apps\backend\runners\github\orchestrator.py
- **GH Client:** B:\_repositorios\auto-claude\apps\backend\runners\github\gh_client.py
- **Rate Limiter:** B:\_repositorios\auto-claude\apps\backend\runners\github\rate_limiter.py
- **Bot Detection:** B:\_repositorios\auto-claude\apps\backend\runners\github\bot_detection.py
- **Permissions:** B:\_repositorios\auto-claude\apps\backend\runners\github\permissions.py
- **Batch Processing:** B:\_repositorios\auto-claude\apps\backend\runners\github\batch_issues.py

### Skybridge
- **Handler:** B:\_repositorios\skybridge\src\skybridge\core\contexts\webhooks\application\handlers.py
- **Processor:** B:\_repositorios\skybridge\src\skybridge\core\contexts\webhooks\application\webhook_processor.py
- **Orchestrator:** B:\_repositorios\skybridge\src\skybridge\core\contexts\webhooks\application\job_orchestrator.py
- **Worktree Manager:** B:\_repositorios\skybridge\src\skybridge\core\contexts\webhooks\application\worktree_manager.py
- **Agent Facade:** B:\_repositorios\skybridge\src\skybridge\core\contexts\webhooks\infrastructure\agents\claude_agent.py
- **Job Queue:** B:\_repositorios\skybridge\src\skybridge\core\contexts\webhooks\adapters\in_memory_queue.py

---

> "Dois caminhos para GitHub: pull ou push, cada um com suas vantagens." – made by Sky 🔀
