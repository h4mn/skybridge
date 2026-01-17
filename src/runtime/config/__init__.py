# -*- coding: utf-8 -*-
"""Config — Configuração centralizada da aplicação."""

from runtime.config.config import (
    AppConfig,
    SslConfig,
    NgrokConfig,
    FileOpsConfig,
    DiscoveryConfig,
    SecurityConfig,
    WebhookConfig,
    AgentConfig,
    TrelloConfig,
    get_config,
    get_ssl_config,
    get_ngrok_config,
    get_fileops_config,
    get_discovery_config,
    get_security_config,
    get_webhook_config,
    get_agent_config,
    get_trello_config,
)

from runtime.config.agent_prompts import (
    get_system_prompt_template,
    render_system_prompt,
    save_custom_prompt,
    reset_to_default_prompt,
    get_json_validation_prompt,
)

__all__ = [
    # Config classes
    "AppConfig",
    "SslConfig",
    "NgrokConfig",
    "FileOpsConfig",
    "DiscoveryConfig",
    "SecurityConfig",
    "WebhookConfig",
    "AgentConfig",
    "TrelloConfig",
    # Config getters
    "get_config",
    "get_ssl_config",
    "get_ngrok_config",
    "get_fileops_config",
    "get_discovery_config",
    "get_security_config",
    "get_webhook_config",
    "get_agent_config",
    "get_trello_config",
    # Agent prompts
    "get_system_prompt_template",
    "render_system_prompt",
    "save_custom_prompt",
    "reset_to_default_prompt",
    "get_json_validation_prompt",
]
