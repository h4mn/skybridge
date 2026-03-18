# -*- coding: utf-8 -*-
"""
Agent Domain Entities.

Entidades de domínio para execução de agentes AI.
Conforme SPEC008 seção 12 - Ciclo de Vida.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentState(Enum):
    """
    Estados possíveis de um agente durante execução.

    Conforme SPEC008 seção 12:
    - CREATED: Subprocesso iniciado, stdin enviado, snapshot antes capturado
    - RUNNING: Agente executando inferência, enviando comandos via stdout
    - TIMED_OUT: Tempo limite excedido, processo terminado
    - COMPLETED: Agente finalizou, JSON recebido, snapshot depois capturado
    - FAILED: Erro na execução (crash, permission denied, etc)
    """

    CREATED = "created"
    """Subprocesso iniciado, stdin enviado, snapshot antes capturado."""

    RUNNING = "running"
    """Agente executando inferência, enviando comandos via stdout."""

    TIMED_OUT = "timed_out"
    """Tempo limite excedido, processo terminado via SIGKILL."""

    COMPLETED = "completed"
    """Agente finalizou, JSON recebido, snapshot depois capturado."""

    FAILED = "failed"
    """Erro na execução (crash, permission denied, etc)."""


@dataclass
class ThinkingStep:
    """
    Um passo de raciocínio do agente para observabilidade.

    Conforme SPEC008 seção 9.2 - thinkings estruturados.

    Attributes:
        step: Número sequencial do passo
        thought: Descrição do pensamento/raciocínio
        timestamp: Momento do pensamento
        duration_ms: Duração em milissegundos (opcional)
        inference_used: Se usou inferência (deve ser sempre True)
    """

    step: int
    thought: str
    timestamp: datetime
    duration_ms: int | None = None
    inference_used: bool = True  # Sempre True por padrão (inferência obrigatória)


@dataclass
class AgentResult:
    """
    Resultado estruturado da execução de um agente.

    Conforme SPEC008 seção 9.2 - Saída (stdout).

    Attributes:
        success: Se a execução foi bem-sucedida
        changes_made: Se o agente fez alterações
        files_created: Lista de arquivos criados
        files_modified: Lista de arquivos modificados
        files_deleted: Lista de arquivos deletados
        commit_hash: Hash do commit criado (se aplicável)
        pr_url: URL da PR criada (se aplicável)
        message: Mensagem descritiva legível
        issue_title: Título da issue original
        output_message: Resumo curto da saída
        thinkings: Lista de passos de raciocínio
    """

    success: bool
    changes_made: bool
    files_created: list[str]
    files_modified: list[str]
    files_deleted: list[str]
    commit_hash: str | None
    pr_url: str | None
    message: str
    issue_title: str
    output_message: str
    thinkings: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário para serialização JSON."""
        return {
            "success": self.success,
            "changes_made": self.changes_made,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "commit_hash": self.commit_hash,
            "pr_url": self.pr_url,
            "message": self.message,
            "issue_title": self.issue_title,
            "output_message": self.output_message,
            "thinkings": self.thinkings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentResult":
        """Cria instância a partir de dicionário."""
        return cls(
            success=data.get("success", False),
            changes_made=data.get("changes_made", False),
            files_created=data.get("files_created", []),
            files_modified=data.get("files_modified", []),
            files_deleted=data.get("files_deleted", []),
            commit_hash=data.get("commit_hash"),
            pr_url=data.get("pr_url"),
            message=data.get("message", ""),
            issue_title=data.get("issue_title", ""),
            output_message=data.get("output_message", ""),
            thinkings=data.get("thinkings", []),
        )


@dataclass
class AgentExecution:
    """
    Representa uma execução completa de um agente AI.

    Conforme SPEC008 seção 12 - Ciclo de Vida.

    Attributes:
        agent_type: Tipo de agente (claude-code, roo-code, etc)
        job_id: ID do job de webhook associado
        worktree_path: Caminho para o worktree isolado
        skill: Tipo de tarefa executada
        state: Estado atual da execução
        result: Resultado da execução (quando completado)
        error_message: Mensagem de erro (se falhou)
        stdout: Saída stdout completa
        stderr: Saída stderr completa
        xml_commands_received: Comandos XML recebidos durante execução (tempo real)
        created_at: Timestamp de criação
        started_at: Timestamp de início da execução
        completed_at: Timestamp de conclusão
        timeout_seconds: Timeout configurado
    """

    agent_type: str
    job_id: str
    worktree_path: str
    skill: str
    state: AgentState
    result: AgentResult | None = None
    error_message: str | None = None
    stdout: str = ""
    stderr: str = ""
    xml_commands_received: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    timeout_seconds: int = 600

    @property
    def duration_ms(self) -> int | None:
        """Duração da execução em milissegundos."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def is_terminal(self) -> bool:
        """Se a execução está em estado terminal."""
        return self.state in (
            AgentState.COMPLETED,
            AgentState.TIMED_OUT,
            AgentState.FAILED,
        )

    def mark_running(self) -> None:
        """Marca execução como em andamento."""
        self.state = AgentState.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, result: AgentResult) -> None:
        """Marca execução como completada com sucesso."""
        self.state = AgentState.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_timed_out(self, error_message: str) -> None:
        """Marca execução como timeout."""
        self.state = AgentState.TIMED_OUT
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

    def mark_failed(self, error_message: str) -> None:
        """Marca execução como falha."""
        self.state = AgentState.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário para serialização JSON."""
        return {
            "agent_type": self.agent_type,
            "job_id": self.job_id,
            "worktree_path": self.worktree_path,
            "skill": self.skill,
            "state": self.state.value,
            "result": self.result.to_dict() if self.result else None,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "timeout_seconds": self.timeout_seconds,
            "timestamps": {
                "created_at": self.created_at.isoformat(),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": (
                    self.completed_at.isoformat() if self.completed_at else None
                ),
            },
        }
