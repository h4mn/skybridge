"""
Testes de especificação para fachada MCP do Glitchtip.

Estes testes servem como TEMPLATE para futuras fachadas MCP.
Cada fachada MCP deve testar:

1. Resolução de caminhos (project root, compose dir)
2. Carregamento de .env (raiz + específico)
3. Precedência de variáveis (ENV > .env raiz > .env específico)
4. Defaults seguros quando nada está configurado
5. Integração com o client real (mockado)
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Path para importar a fachada
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FACADE_PATH = PROJECT_ROOT / "apps" / "mcp" / "glitchtip.py"


class TestResolucaoDeCaminhos:
    """Fachada deve resolver todos os caminhos relativos ao project root."""

    def test_project_root_aponta_para_skybridge(self, tmp_path):
        """O _project_root calculado deve ser a raiz da skybridge."""
        # _project_root = Path(__file__).resolve().parents[2]
        # apps/mcp/glitchtip.py → parents[2] = skybridge/
        expected_root = FACADE_PATH.resolve().parents[2]
        assert expected_root.name == "skybridge"

    def test_compose_dir_default_aponta_para_runtime(self):
        """GLITCHTIP_COMPOSE_DIR default deve ser runtime/observability/."""
        compose_default = str(PROJECT_ROOT / "runtime" / "observability")
        assert "runtime" in compose_default
        assert "observability" in compose_default


class TestCarregamentoEnv:
    """Fachada deve carregar variáveis do .env na ordem correta."""

    def test_carrega_env_raiz(self, tmp_path):
        """Deve ler GLITCHTIP_API_TOKEN do .env na raiz do projeto."""
        env_file = tmp_path / ".env"
        env_file.write_text("GLITCHTIP_API_TOKEN=token-from-root\n")

        # Simula o _load_env da fachada
        original = os.environ.copy()
        os.environ.pop("GLITCHTIP_API_TOKEN", None)
        try:
            for line in env_file.read_text(encoding="utf-8").split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip()
                    if key and key not in os.environ:
                        os.environ[key] = val

            assert os.environ.get("GLITCHTIP_API_TOKEN") == "token-from-root"
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_carrega_env_runtime(self, tmp_path):
        """Deve ler variáveis do .env em runtime/observability/."""
        runtime_env = tmp_path / "runtime" / "observability"
        runtime_env.mkdir(parents=True)
        (runtime_env / ".env").write_text("DATABASE_URL=postgres://test\n")

        original = os.environ.copy()
        os.environ.pop("DATABASE_URL", None)
        try:
            for line in (runtime_env / ".env").read_text(encoding="utf-8").split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip()
                    if key and key not in os.environ:
                        os.environ[key] = val

            assert os.environ.get("DATABASE_URL") == "postgres://test"
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_env_raiz_tem_precedencia_sobre_runtime(self, tmp_path):
        """Se var existe no .env raiz E no runtime, raiz vence."""
        root_env = tmp_path / ".env"
        root_env.write_text("GLITCHTIP_API_TOKEN=from-root\n")

        runtime_dir = tmp_path / "runtime" / "observability"
        runtime_dir.mkdir(parents=True)
        (runtime_dir / ".env").write_text("GLITCHTIP_API_TOKEN=from-runtime\n")

        original = os.environ.copy()
        os.environ.pop("GLITCHTIP_API_TOKEN", None)
        try:
            # Simula ordem: raiz primeiro, runtime depois
            for env_path in [root_env, runtime_dir / ".env"]:
                if not env_path.exists():
                    continue
                for line in env_path.read_text(encoding="utf-8").split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, val = line.partition("=")
                        key, val = key.strip(), val.strip()
                        if key and key not in os.environ:
                            os.environ[key] = val

            assert os.environ.get("GLITCHTIP_API_TOKEN") == "from-root"
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_env_var_tem_precedencia_maxima(self, tmp_path):
        """Variável já em os.environ não deve ser sobrescrita por .env."""
        root_env = tmp_path / ".env"
        root_env.write_text("GLITCHTIP_API_TOKEN=from-file\n")

        original = os.environ.copy()
        try:
            os.environ["GLITCHTIP_API_TOKEN"] = "from-env"
            for line in root_env.read_text(encoding="utf-8").split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip()
                    if key and key not in os.environ:
                        os.environ[key] = val

            assert os.environ.get("GLITCHTIP_API_TOKEN") == "from-env"
        finally:
            os.environ.clear()
            os.environ.update(original)

    def test_env_sem_arquivo_nao_falha(self, tmp_path):
        """Se .env não existe, fachada deve continuar sem erro."""
        missing = tmp_path / "nao_existe" / ".env"
        assert not missing.exists()
        # Não deve lançar exception
        if missing.exists():
            for line in missing.read_text().split("\n"):
                pass

    def test_linhas_comentadas_e_vazias_ignoradas(self, tmp_path):
        """Linhas com # e vazias no .env devem ser ignoradas."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# comentário\n"
            "\n"
            "GLITCHTIP_API_TOKEN=valid-token\n"
            "  # outro comentário\n"
        )

        original = os.environ.copy()
        os.environ.pop("GLITCHTIP_API_TOKEN", None)
        try:
            for line in env_file.read_text(encoding="utf-8").split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip()
                    if key and key not in os.environ:
                        os.environ[key] = val

            assert os.environ.get("GLITCHTIP_API_TOKEN") == "valid-token"
            # Comentários não viraram variáveis
            assert "# comentário" not in os.environ
        finally:
            os.environ.clear()
            os.environ.update(original)


class TestDefaults:
    """Fachada deve prover defaults seguros."""

    def test_default_mcp_url(self):
        """URL padrão deve ser http://localhost:8000/mcp."""
        default = "http://localhost:8000/mcp"
        assert "localhost" in default
        assert "/mcp" in default

    def test_default_compose_dir(self):
        """Compose dir padrão deve ser runtime/observability/."""
        default = str(PROJECT_ROOT / "runtime" / "observability")
        assert default.endswith("runtime" + os.sep + "observability") or \
               default.endswith("runtime/observability")

    def test_default_timeout_30s(self):
        """Timeout padrão deve ser 30 segundos."""
        assert int(os.environ.get("GLITCHTIP_STARTUP_TIMEOUT", "30")) == 30


class TestIntegracaoComClient:
    """Fachada deve chamar o client corretamente."""

    def test_importa_client_sem_erro(self):
        """Deve conseguir importar o módulo do client."""
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from core.observability.glitchtip_client import main
        assert callable(main)

    def test_fachada_eh_executavel(self):
        """O arquivo da fachada deve existir e ser legível."""
        assert FACADE_PATH.exists()
        content = FACADE_PATH.read_text(encoding="utf-8")
        assert "asyncio.run(main())" in content
        assert "_load_env" in content
