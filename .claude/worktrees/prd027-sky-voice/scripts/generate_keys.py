# -*- coding: utf-8 -*-
"""Gera API keys e tokens localmente.

Nota: formalizar este fluxo via ADR quando o onboarding de tenant incluir
geracao de chaves via UI/servico interno.
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone


def _rand_token(length: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key(length: int = 32) -> str:
    """Gera uma API key simples (ASCII)."""
    return _rand_token(length)


def generate_bearer_token(length: int = 48) -> str:
    """Gera um bearer token simples (ASCII)."""
    return _rand_token(length)


def _join_map(values: dict[str, str]) -> str:
    return ";".join(f"{name}:{value}" for name, value in values.items())


def main() -> None:
    tenants = ["sky", "pm"]
    api_keys = {tenant: generate_api_key() for tenant in tenants}
    bearer_tokens = {tenant: generate_bearer_token() for tenant in tenants}
    timestamp = datetime.now(timezone.utc).isoformat()
    env_lines = [
        f"# gerado em {timestamp} UTC",
        f"SKYBRIDGE_API_KEYS={_join_map(api_keys)}",
        f"SKYBRIDGE_BEARER_TOKENS={_join_map(bearer_tokens)}",
    ]
    with open(".env", "a", encoding="utf-8") as env_file:
        env_file.write("\n".join(env_lines) + "\n")


if __name__ == "__main__":
    main()
