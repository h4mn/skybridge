# coding: utf-8
"""
Sistema de comandos para o chat Sky.

Comandos começam com / e permitem ações especiais como:
- /help: mostra ajuda
- /new: nova sessão
- /sair: encerrar chat
- /cancel: cancelar operação
"""

from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """Tipos de comandos suportados."""

    HELP = "help"
    NEW = "new"
    SAIR = "sair"
    QUIT = "quit"
    EXIT = "exit"
    CANCEL = "cancel"
    CONFIG = "config"

    @classmethod
    def from_string(cls, value: str) -> "CommandType | None":
        """
        Converte string em CommandType.

        Args:
            value: String do comando (ex: "help", "sair").

        Returns:
            CommandType ou None se não reconhecido.
        """
        try:
            return cls(value.lower())
        except ValueError:
            return None


@dataclass
class Command:
    """Representa um comando do usuário."""

    type: CommandType
    raw: str

    @classmethod
    def parse(cls, input_str: str) -> "Command | None":
        """
        Parse input do usuário para extrair comando.

        Args:
            input_str: Input do usuário.

        Returns:
            Command se input for comando, None caso contrário.
        """
        input_str = input_str.strip()

        # Comandos começam com / ou são aliases especiais
        if input_str.startswith("/"):
            cmd_part = input_str[1:].lower().split()[0]  # Remove / e pega primeira palavra
            cmd_type = CommandType.from_string(cmd_part)
            if cmd_type:
                return Command(type=cmd_type, raw=input_str)

        # Aliases sem /
        elif input_str.lower() in ["?", "quit", "exit"]:
            if input_str == "?":
                return Command(type=CommandType.HELP, raw=input_str)
            else:
                return Command(type=CommandType.from_string(input_str.lower()), raw=input_str)

        return None


def is_command(input_str: str) -> bool:
    """
    Verifica se input é um comando.

    Args:
        input_str: Input do usuário.

    Returns:
        True se for comando, False caso contrário.
    """
    return Command.parse(input_str) is not None


__all__ = ["Command", "CommandType", "is_command"]
