# -*- coding: utf-8 -*-
"""
Config — Configuração centralizada da aplicação.

Carrega de base.yaml + profiles + environment variables.
"""

import os
import sys
from dataclasses import dataclass
from typing import Any
from pathlib import Path


# Diretório base para worktrees (configurável por ambiente)
# Conforme SPEC008 seção 8.1.1
WORKTREES_BASE_PATH = Path(os.getenv(
    "WORKTREES_BASE_PATH",
    "B:/_repositorios/skybridge-worktrees"
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


@dataclass(frozen=True)
class AgentConfig:
    """Configuração de agentes autônomos."""
    claude_code_path: str  # Caminho para executável do Claude Code CLI


@dataclass(frozen=True)
class TrelloConfig:
    """
    Configuração do Trello para integração Kanban.

    Environment Variables:
        TRELLO_API_KEY: Chave de API do Trello (obter em https://trello.com/app-key)
        TRELLO_API_TOKEN: Token de autenticação do usuário (obter em https://trello.com/app-key)

    Example:
        export TRELLO_API_KEY="sua_api_key_aqui"
        export TRELLO_API_TOKEN="seu_token_aqui"
    """
    api_key: str | None
    api_token: str | None

    @staticmethod
    def from_env() -> "TrelloConfig":
        """Cria config a partir de environment variables."""
        return TrelloConfig(
            api_key=os.getenv("TRELLO_API_KEY"),
            api_token=os.getenv("TRELLO_API_TOKEN"),
        )

    def is_valid(self) -> bool:
        """Verifica se ambas as credenciais estão presentes."""
        return bool(self.api_key and self.api_token)
