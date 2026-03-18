# -*- coding: utf-8 -*-
"""
Testes de WorkspaceInitializer.

DOC: ADR024 - Workspace 'core' é auto-criado na primeira execução.
DOC: PB013 - Estrutura de workspaces deve ser criada corretamente.

Estes testes verificam que o WorkspaceInitializer cria a estrutura
completa de diretórios e arquivos para um workspace funcionar.
"""

import sqlite3
import tempfile
from pathlib import Path
import pytest

from runtime.workspace.workspace_initializer import WorkspaceInitializer


class TestWorkspaceInitializer:
    """Testes de WorkspaceInitializer."""

    def test_create_cria_estrutura_de_diretorios(self, tmp_path):
        """
        DOC: ADR024 - create() cria estrutura completa de diretórios.

        Deve criar:
        - workspace/<id>/
        - workspace/<id>/data/
        - workspace/<id>/worktrees/
        - workspace/<id>/snapshots/
        - workspace/<id>/logs/
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create("test-ws", name="Test Workspace")

        # THEN
        ws_path = tmp_path / "test-ws"
        assert ws_path.exists()
        assert (ws_path / "data").exists()
        assert (ws_path / "data").is_dir()
        assert (ws_path / "worktrees").exists()
        assert (ws_path / "worktrees").is_dir()
        assert (ws_path / "snapshots").exists()
        assert (ws_path / "snapshots").is_dir()
        assert (ws_path / "logs").exists()
        assert (ws_path / "logs").is_dir()

    def test_create_cria_arquivo_env_com_comentarios(self, tmp_path):
        """
        DOC: ADR024 - .env é criado com comentários explicativos (não vazio).

        O .env não deve ser vazio - deve ter instruções sobre prioridade
        e como copiar do .env da raiz se necessário.
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create("test-ws", name="Test Workspace")

        # THEN
        env_path = tmp_path / "test-ws" / ".env"
        assert env_path.exists()

        content = env_path.read_text(encoding="utf-8")
        assert "Segredos operacionais do workspace" in content
        assert "Test Workspace" in content
        assert "ADR024" in content
        assert "PRIORIDADE" in content
        assert "cp ../../.env .env" in content

    def test_create_cria_env_example_com_placeholders(self, tmp_path):
        """
        DOC: ADR024 - .env.example contém placeholders e instruções.

        O .env.example deve ter:
        - Instruções sobre ADR024
        - Comando para copiar do .env da raiz
        - Placeholders para as variáveis principais
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create("test-ws", name="Test Workspace")

        # THEN
        env_example_path = tmp_path / "test-ws" / ".env.example"
        assert env_example_path.exists()

        content = env_example_path.read_text(encoding="utf-8")
        # Verifica instruções ADR024
        assert "ADR024" in content or "workspace tem seu próprio .env" in content
        assert "cp ../../.env .env" in content or "copie do .env" in content
        # Verifica placeholders (agora sem valores padrão, apenas nomes)
        assert "GITHUB_TOKEN=" in content
        assert "OPENAI_API_KEY=" in content or "ANTHROPIC_API_KEY=" in content
        assert "Test Workspace" in content or "test-ws" in content

    def test_create_cria_config_json_vazio(self, tmp_path):
        """
        DOC: PB013 - config.json é criado vazio para customização.
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create("test-ws", name="Test Workspace")

        # THEN
        config_path = tmp_path / "test-ws" / "config.json"
        assert config_path.exists()

        import json
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config == {}

    def test_create_cria_jobs_db_com_schema_correto(self, tmp_path):
        """
        DOC: ADR024 - jobs.db é criado com schema inicial.

        Schema deve ter tabela 'jobs' com colunas:
        - id, correlation_id, created_at, status
        - event_source, event_type, event_id
        - payload, metadata, result, error_message
        - locked_at, processing_started_at, completed_at, failed_at
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create("test-ws", name="Test Workspace")

        # THEN
        jobs_db_path = tmp_path / "test-ws" / "data" / "jobs.db"
        assert jobs_db_path.exists()

        conn = sqlite3.connect(str(jobs_db_path))
        cursor = conn.cursor()

        # Verificar tabela jobs existe
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
        )
        result = cursor.fetchone()
        assert result is not None

        # Verificar colunas
        cursor.execute("PRAGMA table_info(jobs)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id", "correlation_id", "created_at", "status",
            "event_source", "event_type", "event_id",
            "payload", "metadata", "result", "error_message",
            "locked_at", "processing_started_at", "completed_at", "failed_at"
        }
        assert expected_columns.issubset(columns)

        # Verificar índices
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='jobs'"
        )
        indexes = {row[0] for row in cursor.fetchall()}
        assert "idx_jobs_status" in indexes
        assert "idx_jobs_created_at" in indexes

        conn.close()

    def test_create_cria_executions_db_com_schema_correto(self, tmp_path):
        """
        DOC: ADR024 - executions.db é criado com schema inicial.

        Schema deve ter tabela 'agent_executions' com colunas:
        - id, job_id, agent_type, skill, state
        - result, error_message, stdout, stderr
        - worktree_path, duration_ms, timeout_seconds
        - created_at, started_at, completed_at
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create("test-ws", name="Test Workspace")

        # THEN
        exec_db_path = tmp_path / "test-ws" / "data" / "executions.db"
        assert exec_db_path.exists()

        conn = sqlite3.connect(str(exec_db_path))
        cursor = conn.cursor()

        # Verificar tabela agent_executions existe
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_executions'"
        )
        result = cursor.fetchone()
        assert result is not None

        # Verificar colunas
        cursor.execute("PRAGMA table_info(agent_executions)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id", "job_id", "agent_type", "skill", "state",
            "result", "error_message", "stdout", "stderr",
            "worktree_path", "duration_ms", "timeout_seconds",
            "created_at", "started_at", "completed_at"
        }
        assert expected_columns.issubset(columns)

        conn.close()

    def test_create_core_cria_workspace_core(self, tmp_path):
        """
        DOC: ADR024 - create_core() cria workspace core automaticamente.

        Workspace core deve ter:
        - id: "core"
        - name: "Skybridge Core"
        - auto: True
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN
        initializer.create_core()

        # THEN
        core_path = tmp_path / "core"
        assert core_path.exists()
        assert (core_path / "data").exists()
        assert (core_path / "worktrees").exists()

        # Verificar .env.example tem nome correto
        env_example = (core_path / ".env.example").read_text(encoding="utf-8")
        assert "Skybridge Core" in env_example

    def test_create_eh_idempotente(self, tmp_path):
        """
        DOC: ADR024 - create() pode ser chamado múltiplas vezes (idempotente).

        Não deve falhar se diretórios já existem.
        """
        # GIVEN
        initializer = WorkspaceInitializer(tmp_path)

        # WHEN - chamado duas vezes
        initializer.create("test-ws", name="Test Workspace")
        initializer.create("test-ws", name="Test Workspace")  # Não deve falhar

        # THEN - estrutura ainda existe
        ws_path = tmp_path / "test-ws"
        assert ws_path.exists()
        assert (ws_path / "data").exists()
