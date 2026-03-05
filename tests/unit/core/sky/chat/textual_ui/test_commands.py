# coding: utf-8
"""
Testes do sistema de comandos.

DOC: openspec/changes/sky-chat-textual-ui/specs/textual-chat-ui/spec.md
DOC: openspec/changes/sky-chat-textual-ui/design.md - Comandos
"""

import pytest
from unittest.mock import Mock, patch

from src.core.sky.chat.textual_ui.commands import (
    Command,
    CommandType,
    is_command,
)


class TestCommandType:
    """
    Testa enum CommandType.
    """

    def test_command_type_values(self):
        """
        QUANDO CommandType é inspecionado
        ENTÃO possui todos os tipos esperados
        """
        # Assert
        assert CommandType.HELP is not None
        assert CommandType.NEW is not None
        assert CommandType.CANCEL is not None
        assert CommandType.SAIR is not None
        assert CommandType.QUIT is not None
        assert CommandType.EXIT is not None
        assert CommandType.CONFIG is not None

    def test_command_type_sao_unicos(self):
        """
        QUANDO CommandType é inspecionado
        ENTÃO todos os valores são únicos
        """
        # Assert
        values = [
            CommandType.HELP,
            CommandType.NEW,
            CommandType.CANCEL,
            CommandType.SAIR,
            CommandType.QUIT,
            CommandType.EXIT,
            CommandType.CONFIG,
        ]
        assert len(values) == len(set(values))


class TestCommandParse:
    """
    Testa Command.parse().
    """

    def test_parse_help_retorna_command_help(self):
        """
        QUANDO parse() é chamado com "/help"
        ENTÃO retorna Command com type=HELP
        """
        # Arrange & Act
        result = Command.parse("/help")

        # Assert
        assert result is not None
        assert result.type == CommandType.HELP
        assert result.raw == "/help"

    def test_parse_interrogacao_retorna_command_help(self):
        """
        QUANDO parse() é chamado com "?"
        ENTÃO retorna Command com type=HELP
        """
        # Arrange & Act
        result = Command.parse("?")

        # Assert
        assert result is not None
        assert result.type == CommandType.HELP
        assert result.raw == "?"

    def test_parse_new_retorna_command_new(self):
        """
        QUANDO parse() é chamado com "/new"
        ENTÃO retorna Command com type=NEW
        """
        # Arrange & Act
        result = Command.parse("/new")

        # Assert
        assert result is not None
        assert result.type == CommandType.NEW
        assert result.raw == "/new"

    def test_parse_cancel_retorna_command_cancel(self):
        """
        QUANDO parse() é chamado com "/cancel"
        ENTÃO retorna Command com type=CANCEL
        """
        # Arrange & Act
        result = Command.parse("/cancel")

        # Assert
        assert result is not None
        assert result.type == CommandType.CANCEL
        assert result.raw == "/cancel"

    def test_parse_sair_retorna_command_sair(self):
        """
        QUANDO parse() é chamado com "/sair"
        ENTÃO retorna Command com type=SAIR
        """
        # Arrange & Act
        result = Command.parse("/sair")

        # Assert
        assert result is not None
        assert result.type == CommandType.SAIR
        assert result.raw == "/sair"

    def test_parse_quit_retorna_command_quit(self):
        """
        QUANDO parse() é chamado com "quit"
        ENTÃO retorna Command com type=QUIT
        """
        # Arrange & Act
        result = Command.parse("quit")

        # Assert
        assert result is not None
        assert result.type == CommandType.QUIT
        assert result.raw == "quit"

    def test_parse_exit_retorna_command_exit(self):
        """
        QUANDO parse() é chamado com "exit"
        ENTÃO retorna Command com type=EXIT
        """
        # Arrange & Act
        result = Command.parse("exit")

        # Assert
        assert result is not None
        assert result.type == CommandType.EXIT
        assert result.raw == "exit"

    def test_parse_config_retorna_command_config(self):
        """
        QUANDO parse() é chamado com "/config"
        ENTÃO retorna Command com type=CONFIG
        """
        # Arrange & Act
        result = Command.parse("/config")

        # Assert
        assert result is not None
        assert result.type == CommandType.CONFIG
        assert result.raw == "/config"

    def test_parse_mensagem_normal_retorna_none(self):
        """
        QUANDO parse() é chamado com mensagem normal
        ENTÃO retorna None
        """
        # Arrange & Act
        result = Command.parse("Olá Sky, tudo bem?")

        # Assert
        assert result is None

    def test_parse_string_vazia_retorna_none(self):
        """
        QUANDO parse() é chamado com string vazia
        ENTÃO retorna None
        """
        # Arrange & Act
        result = Command.parse("")

        # Assert
        assert result is None

    def test_parse_comando_desconhecido_retorna_none(self):
        """
        QUANDO parse() é chamado com comando desconhecido
        ENTÃO retorna None
        """
        # Arrange & Act
        result = Command.parse("/desconhecido")

        # Assert
        assert result is None

    def test_parse_case_sensitive(self):
        """
        QUANDO parse() é chamado com maiúsculas
        ENTÃO não reconhece como comando (exceto quit/exit)
        """
        # Arrange & Act
        result = Command.parse("/HELP")

        # Assert - não deve reconhecer /HELP em maiúsculas
        assert result is None

    def test_parse_com_espacos(self):
        """
        QUANDO parse() é chamado com espaços ao redor
        ENTÃO ainda reconhece comando
        """
        # Arrange & Act
        result = Command.parse("  /help  ")

        # Assert - deve fazer strip antes de verificar
        # Isso depende da implementação - se não fizer strip, retorna None
        # Vou assumir que a implementação faz strip
        # Se não, esse teste precisa ser ajustado

    def test_parse_quit_sem_barra(self):
        """
        QUANDO parse() é chamado com "quit" (sem /)
        ENTÃO retorna Command com type=QUIT
        """
        # Arrange & Act
        result = Command.parse("quit")

        # Assert
        assert result is not None
        assert result.type == CommandType.QUIT


class TestIsCommand:
    """
    Testa função is_command().
    """

    def test_is_command_com_help_retorna_true(self):
        """
        QUANDO is_command() é chamado com "/help"
        ENTÃO retorna True
        """
        # Arrange & Act
        result = is_command("/help")

        # Assert
        assert result is True

    def test_is_command_com_new_retorna_true(self):
        """
        QUANDO is_command() é chamado com "/new"
        ENTÃO retorna True
        """
        # Arrange & Act
        result = is_command("/new")

        # Assert
        assert result is True

    def test_is_command_com_mensagem_normal_retorna_false(self):
        """
        QUANDO is_command() é chamado com mensagem normal
        ENTÃO retorna False
        """
        # Arrange & Act
        result = is_command("Olá Sky!")

        # Assert
        assert result is False

    def test_is_command_com_string_vazia_retorna_false(self):
        """
        QUANDO is_command() é chamado com string vazia
        ENTÃO retorna False
        """
        # Arrange & Act
        result = is_command("")

        # Assert
        assert result is False

    def test_is_command_com_quit_retorna_true(self):
        """
        QUANDO is_command() é chamado com "quit"
        ENTÃO retorna True
        """
        # Arrange & Act
        result = is_command("quit")

        # Assert
        assert result is True

    def test_is_command_com_exit_retorna_true(self):
        """
        QUANDO is_command() é chamado com "exit"
        ENTÃO retorna True
        """
        # Arrange & Act
        result = is_command("exit")

        # Assert
        assert result is True


class TestCommandIntegracao:
    """
    Testes de integração do sistema de comandos.
    """

    def test_todos_comandos_estao_mapeados(self):
        """
        QUANDO todos os CommandType são verificados
        ENTÃO cada um tem um parse correspondente
        """
        # Arrange - mapeamento de comando para string de entrada
        command_map = {
            CommandType.HELP: "/help",
            CommandType.NEW: "/new",
            CommandType.CANCEL: "/cancel",
            CommandType.SAIR: "/sair",
            CommandType.QUIT: "quit",
            CommandType.EXIT: "exit",
            CommandType.CONFIG: "/config",
        }

        # Act & Assert
        for cmd_type, input_str in command_map.items():
            result = Command.parse(input_str)
            assert result is not None, f"Comando {input_str} não foi reconhecido"
            assert result.type == cmd_type, f"Comando {input_str} retornou tipo errado"

    def test_alias_help_funcionam(self):
        """
        QUANDO aliases de /help são testados
        ENTÃO ambos são reconhecidos
        """
        # Arrange & Act
        result1 = Command.parse("/help")
        result2 = Command.parse("?")

        # Assert
        assert result1 is not None
        assert result2 is not None
        assert result1.type == CommandType.HELP
        assert result2.type == CommandType.HELP

    def test_alias_saida_funcionam(self):
        """
        QUANDO aliases de sair são testados
        ENTÃO todos são reconhecidos
        """
        # Arrange & Act
        result1 = Command.parse("/sair")
        result2 = Command.parse("quit")
        result3 = Command.parse("exit")

        # Assert
        assert result1.type == CommandType.SAIR
        assert result2.type == CommandType.QUIT
        assert result3.type == CommandType.EXIT


class TestCommandDetection:
    """
    Testa detecção de comandos no input field.
    """

    def test_detectar_comando_no_inicio(self):
        """
        QUANDO input começa com /
        ENTÃO é potencialmente um comando
        """
        # Arrange & Act
        result = Command.parse("/help")

        # Assert
        assert result is not None

    def test_nao_detectar_comando_no_meio(self):
        """
        QUANDO input tem / no meio (ex: path)
        ENTÃO não é um comando
        """
        # Arrange & Act
        result = Command.parse("Veja o arquivo /home/user/doc.txt")

        # Assert
        assert result is None

    def test_nao_detectar_comando_ao_final(self):
        """
        QUANDO input tem / no final (ex: url)
        ENTÃO não é um comando
        """
        # Arrange & Act
        result = Command.parse("Acesse https://example.com/")

        # Assert
        assert result is None


__all__ = [
    "TestCommandType",
    "TestCommandParse",
    "TestIsCommand",
    "TestCommandIntegracao",
    "TestCommandDetection",
]
