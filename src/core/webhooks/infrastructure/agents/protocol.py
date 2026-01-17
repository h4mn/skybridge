# -*- coding: utf-8 -*-
"""
XML Streaming Protocol - Comunicação Bidirecional Skybridge ↔ Agente.

Conforme SPEC008 seção 6 - Interface de Comunicação Skybridge ↔ Agente.

Este módulo implementa o protocolo de comunicação XML streaming
entre o agente e o orchestrator via stdout.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

from runtime.observability.logger import get_logger

logger = get_logger()


# Constantes de validação (SPEC008 seção 6.4.1)
MAX_XML_SIZE = 50000
MAX_THINKING_SIZE = 10000
MAX_LOG_MESSAGE_SIZE = 5000
MAX_THINKINGS_COUNT = 100


@dataclass
class SkybridgeCommand:
    """
    Comando XML enviado pelo agente para Skybridge.

    Conforme SPEC008 seção 6.2 - Formato XML.

    Attributes:
        command: Nome do comando (log, progress, checkpoint, error)
        params: Dicionário de parâmetros do comando
    """

    command: str
    params: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário."""
        return {
            "command": self.command,
            "params": self.params,
        }


class XMLStreamingProtocol:
    """
    Protocolo de comunicação XML streaming.

    Conforme SPEC008 seção 6:

    Responsabilidades:
    - Parsear comandos XML do stdout do agente
    - Validar estrutura e tamanho dos comandos
    - Sanitizar valores para prevenir XML injection
    - Tratamento robusto de erros de parsing
    """

    # Comandos suportados (SPEC008 seção 6.3)
    SUPPORTED_COMMANDS = {
        "log",
        "progress",
        "checkpoint",
        "error",
    }

    def __init__(
        self,
        max_xml_size: int = MAX_XML_SIZE,
        max_thinking_size: int = MAX_THINKING_SIZE,
        max_log_message_size: int = MAX_LOG_MESSAGE_SIZE,
    ):
        """
        Inicializa protocolo.

        Args:
            max_xml_size: Tamanho máximo de comando XML
            max_thinking_size: Tamanho máximo de thinking
            max_log_message_size: Tamanho máximo de mensagem de log
        """
        self.max_xml_size = max_xml_size
        self.max_thinking_size = max_thinking_size
        self.max_log_message_size = max_log_message_size

    def parse_commands(self, stdout: str) -> list[SkybridgeCommand]:
        """
        Parseia comandos XML do stdout do agente.

        Conforme SPEC008 seção 6.4 - Mecanismo de Streaming.

        Args:
            stdout: Saída stdout completa do agente

        Returns:
            Lista de SkybridgeCommand encontrados

        Example:
            >>> protocol = XMLStreamingProtocol()
            >>> stdout = '''
            ... <skybridge_command>
            ...   <command>log</command>
            ...   <parametro name="mensagem">Hello world!</parametro>
            ... </skybridge_command>
            ... '''
            >>> commands = protocol.parse_commands(stdout)
            >>> len(commands)
            1
        """
        commands = []

        # Extrai todos os blocos <skybridge_command>...</skybridge_command>
        # usando regex non-greedy para pegar cada bloco completo
        pattern = r"<skybridge_command>(.*?)</skybridge_command>"
        matches = re.findall(pattern, stdout, re.DOTALL)

        for match in matches:
            cmd = self._parse_xml_command(f"<skybridge_command>{match}</skybridge_command>")
            if cmd:
                commands.append(cmd)

        return commands

    def _parse_xml_command(self, xml_line: str) -> SkybridgeCommand | None:
        """
        Parseia um único comando XML.

        Conforme SPEC008 seção 6.2.1 - Tratamento Seguro de XML.

        Args:
            xml_line: Linha com comando XML

        Returns:
            SkybridgeCommand ou None se inválido
        """
        # Validação de tamanho (previne DoS)
        if len(xml_line) > self.max_xml_size:
            logger.warning(
                f"XML command too large ({len(xml_line)} > {self.max_xml_size}), ignoring"
            )
            return None

        try:
            # Extrai comando usando regex (mais robusto que parser completo)
            command_match = re.search(
                r"<command>(.*?)</command>", xml_line, re.DOTALL
            )
            if not command_match:
                logger.warning("Missing <command> tag in XML command")
                return None

            command = command_match.group(1).strip()

            # Valida se comando é suportado
            if command not in self.SUPPORTED_COMMANDS:
                logger.warning(f"Unknown command: {command}")
                return None

            # Extrai parâmetros
            params = self._extract_params(xml_line)

            return SkybridgeCommand(command=command, params=params)

        except Exception as e:
            logger.error(f"Error parsing XML command: {e}")
            return None

    def _extract_params(self, xml_line: str) -> dict[str, str]:
        """
        Extrai parâmetros do comando XML.

        Args:
            xml_line: Linha com comando XML

        Returns:
            Dicionário de parâmetros
        """
        params = {}

        # Encontra todos os <parametro name="...">valor</parametro>
        param_matches = re.finditer(
            r'<parametro\s+name="([^"]+)">(.*?)</parametro>', xml_line, re.DOTALL
        )

        for match in param_matches:
            name = match.group(1)
            value = match.group(2)

            # Desescapa HTML entities (XML decoding)
            value = html.unescape(value)

            # Valida tamanho de mensagem de log
            if name == "mensagem" and len(value) > self.max_log_message_size:
                logger.warning(
                    f"Log message too large ({len(value)} > {self.max_log_message_size}), truncating"
                )
                value = value[: self.max_log_message_size] + "..."

            params[name] = value

        return params

    def validate_thinking(self, thinking: dict[str, Any]) -> bool:
        """
        Valida um thinking step.

        Conforme SPEC008 seção 6.4.1 - Validação de Estrutura.

        Args:
            thinking: Dicionário com thinking step

        Returns:
            True se válido
        """
        # Verifica campos obrigatórios
        required_fields = {"step", "thought", "timestamp"}
        if not all(k in thinking for k in required_fields):
            logger.warning("Thinking missing required fields")
            return False

        # Valida tamanho do thought
        thought_text = thinking.get("thought", "")
        if len(thought_text) > self.max_thinking_size:
            logger.warning(
                f"Thinking too large ({len(thought_text)} > {self.max_thinking_size})"
            )
            return False

        return True

    def validate_thinkings(self, thinkings: list[dict]) -> bool:
        """
        Valida lista de thinkings.

        Conforme SPEC008 seção 6.4.1 - Validação de Estrutura.

        Args:
            thinkings: Lista de thinking steps

        Returns:
            True se válidos
        """
        # Valida quantidade
        if len(thinkings) > MAX_THINKINGS_COUNT:
            logger.warning(
                f"Too many thinkings ({len(thinkings)} > {MAX_THINKINGS_COUNT})"
            )
            return False

        # Valida cada thinking
        for thinking in thinkings:
            if not self.validate_thinking(thinking):
                return False

        return True

    @staticmethod
    def is_json_output(line: str) -> bool:
        """
        Verifica se a linha é JSON final.

        Conforme SPEC008 seção 6.4 - Mecanismo de Streaming.

        Args:
            line: Linha do stdout

        Returns:
            True se parece ser JSON final
        """
        line = line.strip()
        return line.startswith("{") and line.endswith("}")

    @staticmethod
    def is_xml_command(line: str) -> bool:
        """
        Verifica se a linha é comando XML.

        Conforme SPEC008 seção 6.4 - Mecanismo de Streaming.

        Args:
            line: Linha do stdout

        Returns:
            True se é comando XML
        """
        line = line.strip()
        return line.startswith("<skybridge_command>") and line.endswith(
            "</skybridge_command>"
        )
