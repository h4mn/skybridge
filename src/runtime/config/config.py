# -*- coding: utf-8 -*-
"""
Config — Configuração centralizada da aplicação.

Carrega de base.yaml + profiles + environment variables.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any
from pathlib import Path

from version import __version__


# Diretório base para worktrees (configurável por ambiente)
# Conforme SPEC008 seção 8.1.1
# PLAN.md: Mudado de skybridge-worktrees para skybridge-auto (mais curto e alinhado com branch auto)
WORKTREES_BASE_PATH = Path(os.getenv(
    "WORKTREES_BASE_PATH",
    "B:/_repositorios/skybridge-auto"
))

# Garante que o diretório existe
WORKTREES_BASE_PATH.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class AppConfig:
    """Configuração da aplicação."""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    debug: bool = False
    title: str = "Skybridge API"
    version: str = "0.1.0"
    description: str = "Ponte entre intenção humana e execução assistida por IA"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass(frozen=True)
class SslConfig:
    """Configuração de HTTPS (TLS)."""
    enabled: bool = False
    cert_file: str | None = None
    key_file: str | None = None


@dataclass(frozen=True)
class NgrokConfig:
    """Configuração do Ngrok."""
    enabled: bool = False
    auth_token: str | None = None
    domain: str | None = None


@dataclass(frozen=True)
class FileOpsConfig:
    """Configuração do FileOps."""
    allowlist_mode: str = "dev"  # "dev" ou "production"
    dev_root: str | None = None  # Default: cwd
    prod_root: str = r"\workspace"  # Default para produção

@dataclass(frozen=True)
class DiscoveryConfig:
    """Configuração de auto-descoberta de handlers."""
    packages: list[str]
    include_submodules: bool = True


@dataclass(frozen=True)
class SecurityConfig:
    """Configuração de segurança baseline."""
    api_key: str | None
    api_keys: dict[str, str]
    bearer_enabled: bool
    bearer_tokens: dict[str, str]
    allow_localhost: bool
    ip_allowlist: list[str]
    method_policy: dict[str, list[str]]
    rate_limit_per_minute: int


@dataclass(frozen=True)
class WebhookConfig:
    """Configuração de webhooks para processamento assíncrono."""
    github_secret: str | None
    discord_secret: str | None
    youtube_secret: str | None
    stripe_secret: str | None
    worktree_base_path: str
    enabled_sources: list[str]
    base_branch: str = "dev"  # Branch base para criar worktrees de agentes
    delete_password: str | None = None  # Senha para deleção de worktrees no WebUI


@dataclass(frozen=True)
class AgentConfig:
    """Configuração de agentes autônomos.

    Environment Variables:
        ANTHROPIC_AUTH_TOKEN: Token de autenticação Anthropic/Z.AI/GLM
        ANTHROPIC_BASE_URL: Base URL para API compatível (opcional)
        ANTHROPIC_DEFAULT_SONNET_MODEL: Modelo padrão (opcional)
    """
    claude_code_path: str  # Caminho para executável do Claude Code CLI
    anthropic_auth_token: str | None = None  # Token Z.AI/GLM (opcional)
    anthropic_base_url: str | None = None  # Base URL Z.AI/GLM (opcional)
    anthropic_default_sonnet_model: str | None = None  # Modelo alternativo (opcional)


@dataclass(frozen=True)
class TrelloConfig:
    """
    Configuração do Trello para integração Kanban.

    Environment Variables:
        TRELLO_API_KEY: Chave de API do Trello (obter em https://trello.com/app-key)
        TRELLO_API_TOKEN: Token de autenticação do usuário (obter em https://trello.com/app-key)
        TRELLO_BOARD_ID: ID do board do Trello (obter na URL do board)

    Example:
        export TRELLO_API_KEY="sua_api_key_aqui"
        export TRELLO_API_TOKEN="seu_token_aqui"
        export TRELLO_BOARD_ID="seu_board_id_aqui"
    """
    api_key: str | None
    api_token: str | None
    board_id: str | None = None

    def is_valid(self) -> bool:
        """Verifica se todas as credenciais estão presentes."""
        return bool(self.api_key and self.api_token and self.board_id)


@dataclass
class TrelloKanbanListsConfig:
    """
    Configuração das listas Kanban do Trello (PRD020).

    Mapeia os IDs das listas do Trello para os estágios do fluxo de trabalho.
    Usado pelo TrelloService para detectar movimentos de cards e iniciar agentes.

    Environment Variables:
        TRELLO_LIST_BRAINROLL: ID da lista de Brainstorm/Backlog
        TRELLO_LIST_TODO: ID da lista "A Fazer"
        TRELLO_LIST_IN_PROGRESS: ID da lista "Em Andamento"
        TRELLO_LIST_REVIEW: ID da lista de Revisão/Teste
        TRELLO_LIST_DONE: ID da lista "Pronto"/Publicar

    Example:
        export TRELLO_LIST_BRAINROLL="5f8d3c2a1b9e0f1234"
        export TRELLO_LIST_TODO="5f8d3c2a1b9e0f1235"
    """

    backlog_list: str = ""  # 🧠 Brainstorm / 📥 Issues
    bugs_list: str = ""  # 📋 A Fazer (mesma que todo_list em muitos boards)
    todo_list: str = ""  # 📋 A Fazer
    in_progress_list: str = ""  # 🚧 Em Andamento
    testing_list: str = ""  # 👀 Em Revisão / ✅ Em Teste
    review_list: str = ""  # ⚔️ Desafio / 👀 Em Revisão
    done_list: str = ""  # 🚀 Publicar / ✅ Pronto

    # Mapeamento de labels do GitHub para Trello
    label_mapping: dict = None

    # Flag para controlar auto-configuração de listas
    auto_create_lists: bool = False

    def __post_init__(self):
        """Inicializa valores padrão após criação do dataclass."""
        if self.label_mapping is None:
            self.label_mapping = {
                "bug": ("bug", "red"),
                "feature": ("feature", "green"),
                "enhancement": ("melhoria", "blue"),
                "documentation": ("docs", "orange"),
                "good-first-issue": ("bom-para-iniciar", "yellow"),
            }

    @property
    def todo(self) -> str:
        """Nome da lista 'A Fazer' (para compatibilidade com código legado)."""
        return "📋 A Fazer"

    @property
    def progress(self) -> str:
        """Nome da lista 'Em Andamento' (para compatibilidade com código legado)."""
        return "🚧 Em Andamento"

    def get_list_names(self) -> list[str]:
        """Retorna lista de nomes das listas Kanban em ordem."""
        return [
            "🧠 Brainstorm",
            "📥 Issues",
            "📋 A Fazer",
            "🚧 Em Andamento",
            "👀 Em Revisão",
            "🚀 Publicar",
        ]

    def get_list_colors(self) -> dict[str, str]:
        """Retorna mapeamento de nome da lista para cor (hex)."""
        return {
            "🧠 Brainstorm": "#E6F7FF",
            "📥 Issues": "#FFF7E6",
            "📋 A Fazer": "#FFFBF0",
            "🚧 Em Andamento": "#E6F7FF",
            "👀 Em Revisão": "#F6FFED",
            "🚀 Publicar": "#F0F5FF",
        }


def get_trello_kanban_lists_config() -> TrelloKanbanListsConfig:
    """
    Retorna configuração das listas Kanban do Trello.

    Lê IDs das listas das environment variables.
    Se não estiverem definidas, retorna config com strings vazias.

    Returns:
        TrelloKanbanListsConfig com IDs das listas
    """
    return TrelloKanbanListsConfig(
        backlog_list=os.getenv("TRELLO_LIST_BRAINROLL", ""),
        bugs_list=os.getenv("TRELLO_LIST_TODO", ""),
        todo_list=os.getenv("TRELLO_LIST_TODO", ""),
        in_progress_list=os.getenv("TRELLO_LIST_IN_PROGRESS", ""),
        testing_list=os.getenv("TRELLO_LIST_REVIEW", ""),
        review_list=os.getenv("TRELLO_LIST_CHALLENGE", ""),
        done_list=os.getenv("TRELLO_LIST_DONE", ""),
    )


def _detect_current_branch() -> str | None:
    """
    Detecta o branch atual do Git.

    Returns:
        Nome do branch atual ou None se não for possível detectar.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _get_log_level_from_branch(branch: str | None) -> str:
    """
    Determina o log level baseado no nome do branch.

    Conforme RF002.1:
    - dev, feature/*, poc/*, hotfix/* → DEBUG
    - main, release/* → INFO
    - Outros → DEBUG (padrão)

    Args:
        branch: Nome do branch Git.

    Returns:
        "DEBUG" ou "INFO"
    """
    if not branch:
        return "INFO"

    branch_lower = branch.lower()

    # Branches de desenvolvimento → DEBUG
    if branch_lower in ("dev", "development") or branch_lower.startswith(("feature/", "poc/", "hotfix/")):
        return "DEBUG"
    # Branches de produção → INFO
    elif branch_lower == "main" or branch_lower.startswith("release/"):
        return "INFO"
    # Padrão → DEBUG
    else:
        return "DEBUG"


def _env_bool(key: str, default: bool = False) -> bool:
    """Lê boolean de env var."""
    value = os.getenv(key, "").lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    return default


def _env_list(key: str, default: list[str]) -> list[str]:
    """Lê lista de env var separada por vírgula."""
    value = os.getenv(key, "")
    if not value:
        return default
    items = [item.strip() for item in value.split(",")]
    return [item for item in items if item]


def _env_map(key: str, default: dict[str, str]) -> dict[str, str]:
    """Lê mapa de env var no formato chave:valor;chave2:valor2."""
    value = os.getenv(key, "")
    if not value:
        return default
    pairs = [item.strip() for item in value.split(";") if item.strip()]
    result: dict[str, str] = {}
    for pair in pairs:
        if ":" not in pair:
            continue
        k, v = pair.split(":", 1)
        if k and v:
            result[k.strip()] = v.strip()
    return result


def _env_policy(key: str, default: dict[str, list[str]]) -> dict[str, list[str]]:
    """Lê policy no formato client:method1,method2;client2:methodA."""
    value = os.getenv(key, "")
    if not value:
        return default
    pairs = [item.strip() for item in value.split(";") if item.strip()]
    result: dict[str, list[str]] = {}
    for pair in pairs:
        if ":" not in pair:
            continue
        client, methods_str = pair.split(":", 1)
        methods = [m.strip() for m in methods_str.split(",") if m.strip()]
        if client and methods:
            result[client.strip()] = methods
    return result


def load_config() -> AppConfig:
    """Carrega configuração de environment variables com detecção automática de log level (RF002.1)."""
    # Detecção automática de log level baseado no branch Git
    current_branch = _detect_current_branch()
    auto_log_level = _get_log_level_from_branch(current_branch)

    # Override manual via SKYBRIDGE_LOG_LEVEL tem precedência
    log_level = os.getenv("SKYBRIDGE_LOG_LEVEL", auto_log_level)

    # Log da detecção (apenas se não for override manual)
    if not os.getenv("SKYBRIDGE_LOG_LEVEL"):
        print(f"[CONFIG] Branch detected: {current_branch or 'unknown'} → Log level: {log_level}")

    return AppConfig(
        host=os.getenv("SKYBRIDGE_HOST", "0.0.0.0"),
        port=int(os.getenv("SKYBRIDGE_PORT", "8000")),
        log_level=log_level,
        debug=_env_bool("SKYBRIDGE_DEBUG", False),
        title=os.getenv("SKYBRIDGE_TITLE", "Skybridge API"),
        version=os.getenv("SKYBRIDGE_VERSION", __version__),
        description=os.getenv("SKYBRIDGE_DESCRIPTION", "Ponte entre intenção humana e execução assistida por IA"),
        docs_url=os.getenv("SKYBRIDGE_DOCS_URL", "/docs"),
        redoc_url=os.getenv("SKYBRIDGE_REDOC_URL", "/redoc"),
    )


def load_ssl_config() -> SslConfig:
    """Carrega configuracao de HTTPS (TLS)."""
    return SslConfig(
        enabled=_env_bool("SKYBRIDGE_SSL_ENABLED", False),
        cert_file=os.getenv("SKYBRIDGE_SSL_CERT_FILE"),
        key_file=os.getenv("SKYBRIDGE_SSL_KEY_FILE"),
    )

def load_ngrok_config() -> NgrokConfig:
    """Carrega configuração do Ngrok."""
    return NgrokConfig(
        enabled=_env_bool("NGROK_ENABLED", False),
        auth_token=os.getenv("NGROK_AUTH_TOKEN"),
        domain=os.getenv("NGROK_DOMAIN"),
    )


def load_fileops_config() -> FileOpsConfig:
    """Carrega configuração do FileOps."""
    return FileOpsConfig(
        allowlist_mode=os.getenv("FILEOPS_ALLOWLIST_MODE", "dev"),
        dev_root=os.getenv("FILEOPS_DEV_ROOT"),
        prod_root=os.getenv("FILEOPS_PROD_ROOT", r"\workspace"),
    )


def load_discovery_config() -> DiscoveryConfig:
    """Carrega configuração de auto-descoberta."""
    packages = _env_list(
        "SKYBRIDGE_DISCOVERY_PACKAGES",
        [
            "core.shared.queries",
            "core.fileops.application.queries",
            "core.webhooks.application",  # PRD013
            "runtime.observability.snapshot",
        ],
    )
    include_submodules = _env_bool("SKYBRIDGE_DISCOVERY_INCLUDE_SUBMODULES", True)
    return DiscoveryConfig(packages=packages, include_submodules=include_submodules)


def load_security_config() -> SecurityConfig:
    """Carrega configuração de segurança baseline."""
    api_keys = _env_map("SKYBRIDGE_API_KEYS", {})
    bearer_tokens = _env_map("SKYBRIDGE_BEARER_TOKENS", {})
    method_policy = _env_policy("SKYBRIDGE_METHOD_POLICY", {})
    return SecurityConfig(
        api_key=os.getenv("SKYBRIDGE_API_KEY"),
        api_keys=api_keys,
        bearer_enabled=_env_bool("SKYBRIDGE_BEARER_ENABLED", False),
        bearer_tokens=bearer_tokens,
        allow_localhost=_env_bool("ALLOW_LOCALHOST", False),
        ip_allowlist=_env_list("SKYBRIDGE_IP_ALLOWLIST", []),
        method_policy=method_policy,
        rate_limit_per_minute=int(os.getenv("SKYBRIDGE_RATE_LIMIT_PER_MINUTE", "0")),
    )


def load_webhook_config() -> WebhookConfig:
    """Carrega configuração de webhooks."""
    return WebhookConfig(
        github_secret=os.getenv("WEBHOOK_GITHUB_SECRET"),
        discord_secret=os.getenv("WEBHOOK_DISCORD_SECRET"),
        youtube_secret=os.getenv("WEBHOOK_YOUTUBE_SECRET"),
        stripe_secret=os.getenv("WEBHOOK_STRIPE_SECRET"),
        # Usa WORKTREES_BASE_PATH definido no módulo (configurável via WORKTREES_BASE_PATH env var)
        worktree_base_path=str(WORKTREES_BASE_PATH),
        enabled_sources=_env_list("WEBHOOK_ENABLED_SOURCES", ["github"]),
        base_branch=os.getenv("WEBHOOK_BASE_BRANCH", "dev"),  # Branch base para worktrees
        delete_password=os.getenv("WEBUI_DELETE_PASSWORD"),  # Senha para deleção de worktrees
    )


def load_agent_config() -> AgentConfig:
    """Carrega configuração de agentes autônomos."""
    # Detecta automaticamente o caminho correto para o Claude Code CLI
    # Usa "claude" que funciona em todos os sistemas (no Windows busca claude.exe)
    default_path = "claude"
    return AgentConfig(
        claude_code_path=os.getenv("CLAUDE_CODE_PATH", default_path),
        anthropic_auth_token=os.getenv("ANTHROPIC_AUTH_TOKEN"),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL"),
        anthropic_default_sonnet_model=os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL"),
    )


def load_trello_config() -> TrelloConfig:
    """Carrega configuração do Trello."""
    return TrelloConfig(
        api_key=os.getenv("TRELLO_API_KEY"),
        api_token=os.getenv("TRELLO_API_TOKEN"),
        board_id=os.getenv("TRELLO_BOARD_ID"),
    )


# Config global
_config: AppConfig | None = None
_ssl_config: SslConfig | None = None
_ngrok_config: NgrokConfig | None = None
_fileops_config: FileOpsConfig | None = None
_discovery_config: DiscoveryConfig | None = None
_security_config: SecurityConfig | None = None
_webhook_config: WebhookConfig | None = None
_agent_config: AgentConfig | None = None
_trello_config: TrelloConfig | None = None


def get_config() -> AppConfig:
    """Retorna configuração da aplicação (singleton)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_ssl_config() -> SslConfig:
    """Retorna configuracao de HTTPS (singleton)."""
    global _ssl_config
    if _ssl_config is None:
        _ssl_config = load_ssl_config()
    return _ssl_config


def get_ngrok_config() -> NgrokConfig:
    """Retorna configuração do Ngrok (singleton)."""
    global _ngrok_config
    if _ngrok_config is None:
        _ngrok_config = load_ngrok_config()
    return _ngrok_config


def get_fileops_config() -> FileOpsConfig:
    """Retorna configuração do FileOps (singleton)."""
    global _fileops_config
    if _fileops_config is None:
        _fileops_config = load_fileops_config()
    return _fileops_config


def get_discovery_config() -> DiscoveryConfig:
    """Retorna configuração de auto-descoberta (singleton)."""
    global _discovery_config
    if _discovery_config is None:
        _discovery_config = load_discovery_config()
    return _discovery_config


def get_security_config() -> SecurityConfig:
    """Retorna configuração de segurança (singleton)."""
    global _security_config
    if _security_config is None:
        _security_config = load_security_config()
    return _security_config


def get_webhook_config() -> WebhookConfig:
    """Retorna configuração de webhooks (singleton)."""
    global _webhook_config
    if _webhook_config is None:
        _webhook_config = load_webhook_config()
    return _webhook_config


def get_agent_config() -> AgentConfig:
    """Retorna configuração de agentes autônomos (singleton)."""
    global _agent_config
    if _agent_config is None:
        _agent_config = load_agent_config()
    return _agent_config


def get_trello_config() -> TrelloConfig:
    """Retorna configuração do Trello (singleton)."""
    global _trello_config
    if _trello_config is None:
        _trello_config = load_trello_config()
    return _trello_config


# ============================================================================
# Funções Centralizadas de Caminhos de Workspace (ADR024)
# ============================================================================

def get_base_path() -> Path:
    """
    Retorna o caminho base do projeto.

    Returns:
        Path do diretório raiz do projeto
    """
    return Path.cwd()


def get_workspace_path(workspace_id: str | None = None) -> Path:
    """
    Retorna o caminho do workspace.

    DOC: ADR024 - Workspaces são isolados em workspace/{workspace_id}/

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)

    Returns:
        Path do workspace: workspace/{workspace_id}/
    """
    if workspace_id is None:
        from runtime.workspace.workspace_context import get_current_workspace
        workspace_id = get_current_workspace()

    return get_base_path() / "workspace" / workspace_id


def get_workspace_data_dir(workspace_id: str | None = None) -> Path:
    """
    Retorna o diretório de dados do workspace.

    DOC: ADR024 - Cada workspace tem seu próprio data/

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)

    Returns:
        Path: workspace/{workspace_id}/data/
    """
    return get_workspace_path(workspace_id) / "data"


def get_workspace_logs_dir(workspace_id: str | None = None) -> Path:
    """
    Retorna o diretório de logs do workspace.

    DOC: ADR024 - Cada workspace tem seu próprio logs/

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)

    Returns:
        Path: workspace/{workspace_id}/logs/
    """
    return get_workspace_path(workspace_id) / "logs"


def get_workspace_queue_dir(workspace_id: str | None = None) -> Path:
    """
    Retorna o diretório de fila do workspace.

    DOC: ADR024 - Cada workspace tem seu próprio fila/ (FileBasedJobQueue)

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)

    Returns:
        Path: workspace/{workspace_id}/fila/
    """
    return get_workspace_path(workspace_id) / "fila"


def get_workspace_snapshots_dir(workspace_id: str | None = None) -> Path:
    """
    Retorna o diretório de snapshots do workspace.

    DOC: ADR017 - Snapshots armazenados em workspace/{workspace_id}/snapshots/

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)

    Returns:
        Path: workspace/{workspace_id}/snapshots/
    """
    return get_workspace_path(workspace_id) / "snapshots"


def get_workspace_diffs_dir(workspace_id: str | None = None) -> Path:
    """
    Retorna o diretório de diffs do workspace.

    DOC: ADR017 - Diffs armazenados em workspace/{workspace_id}/diffs/

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)

    Returns:
        Path: workspace/{workspace_id}/diffs/
    """
    return get_workspace_path(workspace_id) / "diffs"


# ============================================================================
# Funções de Carregamento de .env (ADR024)
# ============================================================================

def load_workspace_env(workspace_id: str | None = None) -> None:
    """
    Carrega variáveis de ambiente do .env na ordem correta (ADR024).

    Ordem de prioridade:
    1. workspace/{workspace_id}/.env (operacional principal)
    2. .env da raiz (fallback/backup/apenas segurança)

    DOC: ADR024 - .env do workspace tem prioridade sobre .env da raiz
    DOC: .env da raiz é APENAS backup/segurança, não deve ser usado operacionalmente

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)
    """
    from dotenv import load_dotenv

    if workspace_id is None:
        from runtime.workspace.workspace_context import get_current_workspace
        workspace_id = get_current_workspace()

    base_path = get_base_path()

    # 1. Tenta carregar .env do workspace (OPERACIONAL)
    workspace_env = base_path / "workspace" / workspace_id / ".env"
    if workspace_env.exists():
        load_dotenv(workspace_env, override=True)
        return

    # 2. Fallback: carrega .env da raiz (BACKUP/SEGURANÇA)
    root_env = base_path / ".env"
    if root_env.exists():
        load_dotenv(root_env, override=False)


def ensure_workspace_env(workspace_id: str | None = None) -> None:
    """
    Garante que o .env do workspace existe, criando se necessário.

    Se o .env do workspace não existir, cria um com comentários explicativos.
    Se .env da raiz existir, oferece para copiar (mas não copia automaticamente).

    Args:
        workspace_id: ID do workspace (None = usa workspace atual)
    """
    if workspace_id is None:
        from runtime.workspace.workspace_context import get_current_workspace
        workspace_id = get_current_workspace()

    base_path = get_base_path()
    workspace_env = base_path / "workspace" / workspace_id / ".env"

    if not workspace_env.exists():
        # Criar .env do workspace com instruções
        workspace_env.parent.mkdir(parents=True, exist_ok=True)
        workspace_env.write_text(
            f"# Segredos operacionais do workspace '{workspace_id}'\n"
            f"# DOC: ADR024 - Este .env tem PRIORIDADE sobre .env da raiz\n"
            f"# \n"
            f"# Para copiar segredos do .env da raiz (backup), use:\n"
            f"#       cp ../../.env .env\n"
            f"# \n"
            f"# Ou configure manualmente abaixo:\n"
            f"GITHUB_TOKEN=\n"
            f"ANTHROPIC_API_KEY=\n"
            f"# ... outras vars ...\n",
            encoding="utf-8"
        )
