# coding: utf-8
"""
Testes do StreamEvent e StreamEventType.

Valida o pipeline completo SDK → Adapter → Screen → Turn.
"""

import pytest
from datetime import datetime

from src.core.sky.chat.claude_chat import StreamEvent, StreamEventType


class TestStreamEventType:
    """
    Testa enum StreamEventType.
    """

    def test_tipos_de_eventos_existentes(self):
        """
        QUANDO StreamEventType é inspecionado
        ENTÃO possui todos os tipos esperados
        """
        # Assert
        assert hasattr(StreamEventType, "TEXT")
        assert hasattr(StreamEventType, "THOUGHT")
        assert hasattr(StreamEventType, "TOOL_START")
        assert hasattr(StreamEventType, "TOOL_RESULT")
        assert hasattr(StreamEventType, "ERROR")


class TestStreamEvent:
    """
    Testa dataclass StreamEvent.
    """

    def test_init_com_tipo_e_conteudo(self):
        """
        QUANDO StreamEvent é criado
        ENTÃO armazena tipo e conteúdo
        """
        # Arrange & Act
        event = StreamEvent(
            type=StreamEventType.TEXT,
            content="Texto de teste"
        )

        # Assert
        assert event.type == StreamEventType.TEXT
        assert event.content == "Texto de teste"

    def test_init_com_metadata_none_torna_dict_vazio(self):
        """
        QUANDO StreamEvent é criado sem metadata
        ENTÃO metadata se torna dict vazio
        """
        # Arrange & Act
        event = StreamEvent(
            type=StreamEventType.TEXT,
            content="Texto",
            metadata=None
        )

        # Assert
        assert event.metadata == {}

    def test_init_com_metadata(self):
        """
        QUANDO StreamEvent é criado com metadata
        ENTÃO preserva metadata
        """
        # Arrange
        meta = {"tool": "Read", "path": "/file.txt"}

        # Act
        event = StreamEvent(
            type=StreamEventType.TOOL_START,
            content="Usando Read...",
            metadata=meta
        )

        # Assert
        assert event.metadata == meta

    def test_evento_text(self):
        """
        QUANDO evento de texto é criado
        ENTÃO possui type correto
        """
        # Arrange & Act
        event = StreamEvent(type=StreamEventType.TEXT, content="Olá")

        # Assert
        assert event.type == StreamEventType.TEXT

    def test_evento_tool_start(self):
        """
        QUANDO evento de tool_start é criado
        ENTÃO possui type correto
        """
        # Arrange & Act
        event = StreamEvent(
            type=StreamEventType.TOOL_START,
            content="Usando Read...",
            metadata={"tool": "Read"}
        )

        # Assert
        assert event.type == StreamEventType.TOOL_START
        assert event.metadata["tool"] == "Read"

    def test_evento_tool_result(self):
        """
        QUANDO evento de tool_result é criado
        ENTÃO possui type correto
        """
        # Arrange & Act
        event = StreamEvent(
            type=StreamEventType.TOOL_RESULT,
            content="Resultado de Read",
            metadata={"tool": "Read", "result": "conteúdo"}
        )

        # Assert
        assert event.type == StreamEventType.TOOL_RESULT
        assert event.metadata["tool"] == "Read"

    def test_evento_error(self):
        """
        QUANDO evento de erro é criado
        ENTÃO possui type correto
        """
        # Arrange & Act
        event = StreamEvent(
            type=StreamEventType.ERROR,
            content="Erro ao processar"
        )

        # Assert
        assert event.type == StreamEventType.ERROR
