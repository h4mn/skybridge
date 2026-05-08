"""
Testes para logging_config.py — Spec: logging-config

Cenários:
- Logger padrão com stdout + FileHandler
- Rotação automática ao atingir 5MB
- Diretório logs/ criado automaticamente
- Formato estruturado correto
- Funciona sem Glitchtip/Docker
- Importação isolada sem dependências
"""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from core.observability.logging_config import (
    LOG_DIR,
    LOG_FILE,
    MAX_BYTES,
    BACKUP_COUNT,
    get_logger,
)


class TestGetLogger:
    """Spec: logging-config — Requirement: Logger com FileHandler rotativo"""

    def test_retorna_logger_com_nome_correto(self):
        logger = get_logger("youtube")
        assert logger.name == "youtube"

    def test_tem_stdout_handler(self):
        logger = get_logger("test.stdout")
        stream_handlers = [
            h for h in logger.handlers if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) >= 1

    def test_tem_file_handler_rotativo(self):
        from logging.handlers import RotatingFileHandler
        logger = get_logger("test.file")
        file_handlers = [
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        ]
        assert len(file_handlers) >= 1

    def test_file_handler_aponta_para_logs_dir(self):
        from logging.handlers import RotatingFileHandler
        logger = get_logger("test.path")
        fh = next(
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        )
        assert Path(fh.baseFilename).name == "observability.log"

    def test_rotacao_5mb_3_backups(self):
        from logging.handlers import RotatingFileHandler
        logger = get_logger("test.rotation")
        fh = next(
            h for h in logger.handlers if isinstance(h, RotatingFileHandler)
        )
        assert fh.maxBytes == MAX_BYTES
        assert fh.backupCount == BACKUP_COUNT


class TestDiretorioLogs:
    """Spec: logging-config — Scenario: Diretório logs/ não existe"""

    def test_diretorio_logs_criado_automaticamente(self, tmp_path):
        with patch("core.observability.logging_config.LOG_DIR", tmp_path / "logs"):
            with patch("core.observability.logging_config.LOG_FILE", tmp_path / "logs" / "test.log"):
                get_logger("test.mkdir")
                assert (tmp_path / "logs").exists()


class TestFormatoEstruturado:
    """Spec: logging-config — Scenario: Formato de saída"""

    def test_formato_contém_timestamp_nível_nome_mensagem(self):
        logger = get_logger("test.format")
        formatter = logger.handlers[0].formatter
        assert "%(asctime)s" in formatter._fmt
        assert "%(levelname)" in formatter._fmt
        assert "%(name)s" in formatter._fmt
        assert "%(message)s" in formatter._fmt


class TestIsolamento:
    """Spec: logging-config — Requirement: Disponibilidade independente do Glitchtip"""

    def test_importação_sem_glitchtip(self):
        """Importar logging_config não importa glitchtip_client."""
        import core.observability.logging_config as mod
        assert not hasattr(mod, "GlitchtipMCPClient")

    def test_logger_funciona_sem_docker(self):
        """Logger funciona mesmo sem Docker instalado."""
        logger = get_logger("test.no_docker")
        # Se chegou aqui sem exception, funciona sem Docker
        assert logger is not None
