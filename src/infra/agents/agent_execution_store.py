# -*- coding: utf-8 -*-
"""
Agent Execution Store - Persistência de execuções de agentes em SQLite.

PRD: Página de Agents (Agent Spawns)
Responsabilidades:
- Persistir AgentExecution em SQLite
- Recuperar execuções por job_id
- Listar todas as execuções
- Calcular métricas (total, por estado, success_rate)
"""
from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from core.webhooks.infrastructure.agents.domain import (
    AgentExecution,
    AgentResult,
    AgentState,
)


class AgentExecutionStore:
    """
    Store para persistência de execuções de agentes em SQLite.

    Atributos:
        _db_path: Caminho para o arquivo SQLite
        _conn: Conexão SQLite
    """

    def __init__(self, db_path: str | None = None):
        """
        Inicializa store e cria tabela se não existir.

        Args:
            db_path: Caminho para arquivo SQLite. Se None, usa padrão.
        """
        if db_path is None:
            # Usa diretório workspace/skybridge/data se existir
            data_dir = Path("workspace/skybridge/data")
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "agent_executions.db")

        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        self._create_table()

    def _create_table(self) -> None:
        """Cria tabela agent_executions se não existir."""
        cursor = self._conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                agent_type TEXT NOT NULL,
                skill TEXT NOT NULL,
                state TEXT NOT NULL,
                result TEXT,  -- JSON de AgentResult
                error_message TEXT,
                stdout TEXT,
                stderr TEXT,
                worktree_path TEXT NOT NULL,
                duration_ms INTEGER,
                timeout_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
        """)

        self._conn.commit()

    def save(self, execution: AgentExecution) -> None:
        """
        Salva ou atualiza execução no banco (UPSERT).

        Args:
            execution: AgentExecution a persistir
        """
        cursor = self._conn.cursor()

        # Serializa result para JSON se existir
        result_json = None
        if execution.result:
            result_json = json.dumps(execution.result.to_dict())

        # Calcula duration_ms
        duration_ms = execution.duration_ms

        # UPSERT usando INSERT OR REPLACE
        cursor.execute("""
            INSERT OR REPLACE INTO agent_executions (
                job_id, agent_type, skill, state, result, error_message,
                stdout, stderr, worktree_path, duration_ms, timeout_seconds,
                created_at, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            execution.job_id,
            execution.agent_type,
            execution.skill,
            execution.state.value,
            result_json,
            execution.error_message,
            execution.stdout,
            execution.stderr,
            execution.worktree_path,
            duration_ms,
            execution.timeout_seconds,
            execution.created_at.isoformat(),
            execution.started_at.isoformat() if execution.started_at else None,
            execution.completed_at.isoformat() if execution.completed_at else None,
        ))

        self._conn.commit()

    def get(self, job_id: str) -> AgentExecution | None:
        """
        Retorna execução pelo job_id.

        Args:
            job_id: ID do job

        Returns:
            AgentExecution ou None se não encontrado
        """
        cursor = self._conn.cursor()

        cursor.execute("""
            SELECT * FROM agent_executions WHERE job_id = ?
        """, (job_id,))

        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_execution(row)

    def list_all(self, limit: int | None = None) -> list[AgentExecution]:
        """
        Lista todas as execuções ordenadas por created_at DESC.

        Args:
            limit: Limite de registros (opcional)

        Returns:
            Lista de AgentExecution
        """
        cursor = self._conn.cursor()

        query = """
            SELECT * FROM agent_executions
            ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query)

        return [self._row_to_execution(row) for row in cursor.fetchall()]

    def get_metrics(self) -> dict[str, Any]:
        """
        Retorna métricas de execuções.

        Returns:
            Dict com métricas:
            - total: Total de execuções
            - created: Execuções em estado CREATED
            - running: Execuções em estado RUNNING
            - completed: Execuções em estado COMPLETED
            - failed: Execuções em estado FAILED
            - timed_out: Execuções em estado TIMED_OUT
            - success_rate: Taxa de sucesso (0-100) ou None
        """
        cursor = self._conn.cursor()

        # Conta total
        cursor.execute("SELECT COUNT(*) FROM agent_executions")
        total = cursor.fetchone()[0]

        # Conta por estado
        cursor.execute("""
            SELECT state, COUNT(*) FROM agent_executions
            GROUP BY state
        """)
        state_counts = {row[0]: row[1] for row in cursor.fetchall()}

        created = state_counts.get(AgentState.CREATED.value, 0)
        running = state_counts.get(AgentState.RUNNING.value, 0)
        completed = state_counts.get(AgentState.COMPLETED.value, 0)
        failed = state_counts.get(AgentState.FAILED.value, 0)
        timed_out = state_counts.get(AgentState.TIMED_OUT.value, 0)

        # Calcula success_rate
        # success_rate = (completed com result.success=True) / (completed + failed + timed_out)
        success_rate = None
        terminal_total = completed + failed + timed_out
        if terminal_total > 0:
            # Conta completed com success=True
            cursor.execute("""
                SELECT COUNT(*) FROM agent_executions
                WHERE state = ? AND result IS NOT NULL
            """, (AgentState.COMPLETED.value,))
            completed_with_result = cursor.fetchone()[0]

            # Conta quantos têm result.success = True
            cursor.execute("""
                SELECT COUNT(*) FROM agent_executions
                WHERE state = ? AND result IS NOT NULL
                AND json_extract(result, '$.success') = 1
            """, (AgentState.COMPLETED.value,))
            completed_success = cursor.fetchone()[0]

            if completed_with_result > 0:
                success_rate = (completed_success / terminal_total) * 100

        return {
            "total": total,
            "created": created,
            "running": running,
            "completed": completed,
            "failed": failed,
            "timed_out": timed_out,
            "success_rate": success_rate,
        }

    def _row_to_execution(self, row: sqlite3.Row) -> AgentExecution:
        """Converte linha do banco para AgentExecution."""
        # Deserializa result se existir
        result = None
        if row["result"]:
            result_dict = json.loads(row["result"])
            result = AgentResult.from_dict(result_dict)

        execution = AgentExecution(
            agent_type=row["agent_type"],
            job_id=row["job_id"],
            worktree_path=row["worktree_path"],
            skill=row["skill"],
            state=AgentState(row["state"]),
            result=result,
            error_message=row["error_message"],
            stdout=row["stdout"] or "",
            stderr=row["stderr"] or "",
            timeout_seconds=row["timeout_seconds"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )
        return execution

    def close(self) -> None:
        """Fecha conexão com banco."""
        if self._conn:
            self._conn.close()
