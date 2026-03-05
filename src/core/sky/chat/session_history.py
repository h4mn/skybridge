# coding: utf-8
"""
Histórico de Sessão para Debug.

Coleta e salva informações da sessão de chat em arquivo JSON para debugging.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ToolUseRecord:
    """Registro de uso de ferramenta."""
    name: str
    params: dict
    result: str
    timestamp: str
    error: Optional[str] = None


@dataclass
class MessageRecord:
    """Registro de mensagem."""
    role: str
    content: str
    timestamp: str


@dataclass
class SessionMetadata:
    """Metadados da sessão."""
    session_id: str
    model: str
    total_turns: int
    duration_ms: float


class SessionHistory:
    """
    Gerencia coleta e salvamento de histórico de sessão.

    DOC: openspec/changes/agent-sdk-client-session/specs/session-debug-history/spec.md
    """

    def __init__(self, session_id: str, model: str):
        """
        Inicializa coletor de histórico.

        Args:
            session_id: ID único da sessão.
            model: Nome do modelo Claude usado.
        """
        self._session_id = session_id
        self._model = model
        self._start_time = datetime.now(timezone.utc)
        self._messages: list[MessageRecord] = []
        self._tool_uses: list[ToolUseRecord] = []
        self._total_turns = 0

    def is_enabled(self) -> bool:
        """
        Verifica se salvamento de histórico está habilitado.

        Returns:
            True se histórico deve ser salvo, False caso contrário.
        """
        return os.getenv("SKY_CHAT_DEBUG_HISTORY", "true").lower() != "false"

    def add_message(self, role: str, content: str) -> None:
        """
        Adiciona mensagem ao histórico.

        Args:
            role: "user" ou "sky".
            content: Conteúdo da mensagem.
        """
        if not self.is_enabled():
            return

        self._messages.append(MessageRecord(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ))

    def add_tool_use(self, name: str, params: dict, result: str, error: Optional[str] = None) -> None:
        """
        Adiciona registro de uso de ferramenta.

        Args:
            name: Nome da ferramenta (Read, Glob, Grep).
            params: Parâmetros passados para a ferramenta.
            result: Resultado retornado pela ferramenta.
            error: Mensagem de erro, se houver.
        """
        if not self.is_enabled():
            return

        self._tool_uses.append(ToolUseRecord(
            name=name,
            params=params,
            result=result,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error=error,
        ))

    def increment_turns(self) -> None:
        """Incrementa contador de turnos."""
        self._total_turns += 1

    async def save(self) -> None:
        """
        Salva histórico em arquivo JSON.

        O arquivo é salvo em .sky/debug/session_<timestamp>.json.
        """
        if not self.is_enabled():
            return

        # Cria diretório se não existir
        debug_dir = Path.cwd() / ".sky" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        # Gera nome de arquivo único
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        filename = f"session_{timestamp}.json"
        filepath = debug_dir / filename

        # Calcula duração
        duration_ms = (datetime.now(timezone.utc) - self._start_time).total_seconds() * 1000

        # Monta estrutura JSON
        data = {
            "metadata": asdict(SessionMetadata(
                session_id=self._session_id,
                model=self._model,
                total_turns=self._total_turns,
                duration_ms=round(duration_ms, 2),
            )),
            "messages": [asdict(m) for m in self._messages],
            "tool_uses": [asdict(t) for t in self._tool_uses],
        }

        # Salva arquivo
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


__all__ = ["SessionHistory"]
