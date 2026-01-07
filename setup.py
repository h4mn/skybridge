# -*- coding: utf-8 -*-
"""
Setup configuration for Skybridge.
"""

from pathlib import Path
from setuptools import setup, find_packages

README = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="skybridge",
    version="0.3.0",
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
