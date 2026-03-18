#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Webhook Secret Generator.

Gera secrets criptograficamente seguros para webhooks.
Suporta GitHub, Discord, YouTube, Stripe e fontes genéricas.

Usage:
    python scripts/generate_webhook_secret.py
    python scripts/generate_webhook_secret.py --source github
    python scripts/generate_webhook_secret.py --all
    python scripts/generate_webhook_secret.py --length 64
"""
from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def generate_secret(length: int = 32, prefix: str = "whsec_") -> str:
    """
    Gera secret criptograficamente seguro.

    Args:
        length: Tamanho do secret em bytes (padrão: 32)
        prefix: Prefixo para o secret (padrão: "whsec_")

    Returns:
        Secret gerado em formato hexadecimal
    """
    # Gera bytes criptograficamente seguros
    secret_bytes = secrets.token_bytes(length)
    # Converte para hexadecimal
    secret_hex = secret_bytes.hex()
    return f"{prefix}{secret_hex}"


def generate_github_secret() -> str:
    """
    Gera secret para webhook do GitHub.

    GitHub recomenda: secrets.token_hex() ou similar.
    Formato: string hexadecimal ou base64.

    Returns:
        Secret para GitHub webhook
    """
    # GitHub não requer prefixo específico
    return secrets.token_hex(32)


def generate_discord_secret() -> str:
    """
    Gera secret para webhook do Discord.

    Discord usa: string aleatória para verificação.

    Returns:
        Secret para Discord webhook
    """
    return secrets.token_urlsafe(32)


def generate_youtube_secret() -> str:
    """
    Gera secret para webhook do YouTube (PubSubHubbub).

    YouTube usa: string aleatória para HMAC verification.

    Returns:
        Secret para YouTube webhook
    """
    return secrets.token_hex(32)


def generate_stripe_secret() -> str:
    """
    Gera secret para webhook do Stripe.

    Stripe recomenda: whsec_ prefixo + random string.

    Returns:
        Secret para Stripe webhook (formato whsec_...)
    """
    # Stripe usa prefixo whsec_
    return generate_secret(length=32, prefix="whsec_")


def generate_generic_secret() -> str:
    """
    Gera secret genérico para qualquer fonte.

    Returns:
        Secret genérico com prefixo whsec_
    """
    return generate_secret(length=32, prefix="whsec_")


def print_env_template(secrets: dict[str, str]) -> None:
    """
    Imprime template de variáveis de ambiente.

    Args:
        secrets: Dicionário de source → secret
    """
    print("\n" + "=" * 60)
    print("  Adicione ao seu arquivo .env:")
    print("=" * 60)
    print()

    for source, secret in secrets.items():
        env_var = f"WEBHOOK_{source.upper()}_SECRET"
        print(f'{env_var}="{secret}"')

    print()
    print("=" * 60)
    print("  Comandos de configuração (copy & paste):")
    print("=" * 60)
    print()

    for source, secret in secrets.items():
        env_var = f"WEBHOOK_{source.upper()}_SECRET"
        print(f"# Webhook secret for {source.upper()}")
        print(f"export {env_var}='{secret}'")

    print()


def main() -> int:
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Gera secrets seguros para webhooks"
    )
    parser.add_argument(
        "--source",
        "-s",
        choices=["github", "discord", "youtube", "stripe", "generic"],
        help="Fonte do webhook (padrão: github)",
        default="github",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Gerar secrets para todas as fontes",
    )
    parser.add_argument(
        "--length",
        "-l",
        type=int,
        default=32,
        help="Tamanho do secret em bytes (padrão: 32)",
    )
    parser.add_argument(
        "--no-prefix",
        action="store_true",
        help="Remover prefixo whsec_ do secret",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Mostrar apenas formato .env (sem banner)",
    )

    args = parser.parse_args()

    # Geradores disponíveis
    generators = {
        "github": generate_github_secret,
        "discord": generate_discord_secret,
        "youtube": generate_youtube_secret,
        "stripe": generate_stripe_secret,
        "generic": generate_generic_secret,
    }

    if args.all:
        # Gerar para todas as fontes
        secrets = {source: gen() for source, gen in generators.items()}
    else:
        # Gerar para fonte específica
        generator = generators[args.source]
        secret = generator()
        secrets = {args.source: secret}

    # Remover prefixo se solicitado
    if args.no_prefix:
        secrets = {
            source: secret.replace("whsec_", "").replace("whsec_", "")
            for source, secret in secrets.items()
        }

    # Mostrar resultado
    if not args.env_only:
        print("\n" + "=" * 60)
        print("  Webhook Secret Generator")
        print("=" * 60)
        print()
        for source, secret in secrets.items():
            print(f"  {source.upper():12} : {secret}")
        print()

    # Mostrar template .env
    print_env_template(secrets)

    return 0


if __name__ == "__main__":
    sys.exit(main())
