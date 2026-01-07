# -*- coding: utf-8 -*-
"""
Setup configuration for Skybridge.

Versionamento: Lido do arquivo VERSION (single source of truth - ADR012)
"""

from pathlib import Path
from setuptools import setup, find_packages

README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

# Read version from VERSION file (single source of truth per ADR012)
_VERSION_FILE = Path(__file__).parent / "VERSION"
_version = "0.1.0"  # fallback

if _VERSION_FILE.exists():
    with open(_VERSION_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "SKYBRIDGE_VERSION":
                    _version = v.strip()
                    break

setup(
    name="skybridge",
    version=_version,
    description="Skybridge - Microkernel RPC Platform",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Skybridge Team",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "typer>=0.9.0",
        "requests>=2.31.0",
        "rich>=13.7.0",
        "pyngrok>=7.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "skybridge-api=skybridge.platform.bootstrap.app:main",
            "sb=apps.cli.main:main",
        ],
    },
)
