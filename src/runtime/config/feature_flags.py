# -*- coding: utf-8 -*-
"""
Feature Flags - Sistema de flags para migração gradual.

PRD019: Implementação do Claude Agent SDK com feature flag para rollback.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(key: str, default: bool = False) -> bool:
    """
    Lê boolean de env var.

    Valores considerados True: "1", "true", "yes", "on"
    Valores considerados False: "0", "false", "no", "off"

    Args:
        key: Nome da environment variable
        default: Valor padrão se não definida

    Returns:
        Valor booleano da env var
    """
    value = os.getenv(key, "").lower()
    if value in ("1", "true", "yes", "on"):
        return True
    if value in ("0", "false", "no", "off"):
        return False
    return default


@dataclass(frozen=True)
class FeatureFlags:
    """
    Feature flags para controle de rollout gradual.

    Attributes:
        use_sdk_adapter: Usa Claude Agent SDK (implementação padrão desde ADR021)
    """

    use_sdk_adapter: bool = True


def load_feature_flags() -> FeatureFlags:
    """
    Carrega feature flags de environment variables.

    Returns:
        FeatureFlags com valores das env vars
    """
    return FeatureFlags(
        use_sdk_adapter=_env_bool("USE_SDK_ADAPTER", True),
    )


# Singleton
_feature_flags: FeatureFlags | None = None


def get_feature_flags() -> FeatureFlags:
    """
    Retorna feature flags (singleton).

    Returns:
        FeatureFlags carregadas das environment variables
    """
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = load_feature_flags()
    return _feature_flags
