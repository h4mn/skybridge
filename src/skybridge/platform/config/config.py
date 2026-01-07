# -*- coding: utf-8 -*-
"""
Config — Configuração centralizada da aplicação.

Carrega de base.yaml + profiles + environment variables.
"""

import os
from dataclasses import dataclass
from typing import Any
from pathlib import Path


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
    """Carrega configuração de environment variables."""
    return AppConfig(
        host=os.getenv("SKYBRIDGE_HOST", "0.0.0.0"),
        port=int(os.getenv("SKYBRIDGE_PORT", "8000")),
        log_level=os.getenv("SKYBRIDGE_LOG_LEVEL", "INFO"),
        debug=_env_bool("SKYBRIDGE_DEBUG", False),
        title=os.getenv("SKYBRIDGE_TITLE", "Skybridge API"),
        version=os.getenv("SKYBRIDGE_VERSION", "0.1.0"),
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
            "skybridge.core.shared.queries",
            "skybridge.core.contexts.fileops.application.queries",
            "skybridge.platform.observability.snapshot",
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


# Config global
_config: AppConfig | None = None
_ssl_config: SslConfig | None = None
_ngrok_config: NgrokConfig | None = None
_fileops_config: FileOpsConfig | None = None
_discovery_config: DiscoveryConfig | None = None
_security_config: SecurityConfig | None = None


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
