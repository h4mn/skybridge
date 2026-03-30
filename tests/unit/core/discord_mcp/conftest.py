"""
Fixtures para testes do módulo Discord MCP.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def temp_state_dir():
    """
    Cria diretório temporário isolado para estado do Discord.
    Patch DISCORD_STATE_DIR no módulo access.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "discord_state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Patch no módulo access
        with patch("src.core.discord.access.STATE_DIR", state_dir), \
             patch("src.core.discord.access.ACCESS_FILE", state_dir / "access.json"), \
             patch("src.core.discord.access.APPROVED_DIR", state_dir / "approved"), \
             patch("src.core.discord.utils.STATE_DIR", state_dir), \
             patch("src.core.discord.utils.INBOX_DIR", state_dir / "inbox"), \
             patch.dict(os.environ, {"DISCORD_STATE_DIR": str(state_dir)}):
            yield state_dir


@pytest.fixture
def sample_access_data():
    """Dados de exemplo para access.json."""
    return {
        "dmPolicy": "allowlist",
        "allowFrom": ["123456789"],
        "groups": {
            "987654321": {
                "requireMention": True,
                "allowFrom": []
            }
        },
        "pending": {},
        "mentionPatterns": ["@sky", "@Sky", "Sky,"]
    }


@pytest.fixture
def access_file(temp_state_dir, sample_access_data):
    """Cria arquivo access.json com dados de exemplo."""
    access_file = temp_state_dir / "access.json"
    access_file.write_text(json.dumps(sample_access_data, indent=2), encoding="utf-8")
    return access_file


@pytest.fixture
def empty_state_dir(temp_state_dir):
    """State dir sem access.json."""
    access_file = temp_state_dir / "access.json"
    if access_file.exists():
        access_file.unlink()
    return temp_state_dir
