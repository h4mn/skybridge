# -*- coding: utf-8 -*-
"""
Logger — Logging estruturado com correlation ID.

Logger com suporte a console e arquivo, organizado por data.
"""

import ast
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# Códigos ANSI para cores no terminal
class Colors:
    """Códigos ANSI para cores no terminal."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Níveis de log
    DEBUG = "\033[36m"      # Cyan
    INFO = "\033[32m"       # Green
    WARNING = "\033[33m"    # Yellow
    ERROR = "\033[31m"      # Red
    CRITICAL = "\033[35m"   # Magenta

    # Cores adicionais
    BLUE = "\033[34m"
    GRAY = "\033[90m"       # Cinza escuro (para metadata)
    WHITE = "\033[97m"      # Branco claro (para variáveis, tracebacks)
    BRIGHT_GRAY = "\033[37m"  # Cinza claro (alternativa)
    CYAN = "\033[96m"       # Cyan claro (para URLs, links)
    MAGENTA = "\033[95m"    # Magenta claro (para destaque)
    YELLOW = "\033[93m"     # Amarelo claro (para warnings)
    PIPE = "\033[38;5;240m"  # Cor para pipes | (cinza médio)


# Diretório base para logs
LOGS_DIR = Path("workspace/skybridge/logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class ColorFormatter(logging.Formatter):
    """
    Formatter com cores para console.

    Cores apenas no console, arquivo fica sem cores.

    Suporta campos estruturados de request logging:
    - status_code: HTTP status code com cor
    - duration_ms: Tempo de processamento
    - correlation_id: ID de correlação
    """

    # Mapeamento de nível para cor
    LEVEL_COLORS = {
        logging.DEBUG: Colors.DEBUG,
        logging.INFO: Colors.INFO,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.ERROR,
        logging.CRITICAL: Colors.CRITICAL,
    }

    # Formato base
    BASE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(self.BASE_FORMAT, datefmt=self.DATE_FORMAT)

    def _get_status_color(self, status: int) -> str:
        """
        Retorna cor baseada no HTTP status code.

        Args:
            status: HTTP status code

        Returns:
            Código ANSI de cor
        """
        if 200 <= status < 300:
            return Colors.INFO
        elif 400 <= status < 500:
            return Colors.WARNING
        elif 500 <= status < 600:
            return Colors.ERROR
        return Colors.RESET

    def _pretty_format_value(self, value: Any, reset: str) -> str:
        """Formata valores complexos (dicts, lists) com pretty-print."""
        # Se for dict ou list nativo, faz pretty print JSON
        if isinstance(value, (dict, list)):
            try:
                json_str = json.dumps(value, indent=2, ensure_ascii=False, default=str)
                # Adiciona indentação para alinhar com o log
                lines = json_str.split("\n")
                if len(lines) > 1:
                    # Primeira linha normal, resto com indentação de 2 espaços
                    indent = "  "
                    indented_lines = [lines[0]]
                    for line in lines[1:]:
                        indented_lines.append(f"{indent}{Colors.WHITE}{line}{reset}")
                    return f"{Colors.WHITE}{lines[0]}{reset}\n" + "\n".join(indented_lines[1:])
                return f"{Colors.WHITE}{json_str}{reset}"
            except Exception:
                return f"{Colors.WHITE}{str(value)}{reset}"

        # Tenta parsear como string estruturada
        if isinstance(value, str):
            stripped = value.strip()

            # Tenta JSON primeiro (nossa serialização)
            if stripped.startswith(("{", "[")) and '"' in stripped:
                try:
                    parsed = json.loads(stripped)
                    return self._pretty_format_value(parsed, reset)
                except json.JSONDecodeError:
                    pass

            # Tenta Python literal (aspas simples) - str() de listas/dicts
            if stripped.startswith(("{", "[", "(")) and ("'" in stripped or '"' in stripped):
                try:
                    parsed = ast.literal_eval(stripped)
                    return self._pretty_format_value(parsed, reset)
                except (ValueError, SyntaxError):
                    pass

        # Valor simples
        return f"{Colors.WHITE}{str(value)}{reset}"

    def _format_structured_request(self, record: logging.LogRecord) -> str:
        """
        Formata logs de request HTTP com campos estruturados.

        Formato esperado:
        - status_code: int (HTTP status)
        - duration_ms: float (tempo de processamento)
        - correlation_id: str (ID de correlação)

        Retorna formato colorido:
        timestamp | INFO | skybridge.request | METHOD path → 200 | 15.2ms | corr_id
        """
        reset = Colors.RESET
        level_color = self.LEVEL_COLORS.get(record.levelno, "")

        # Extrai campos estruturados
        status_code = getattr(record, "status_code", 0)
        duration_ms = getattr(record, "duration_ms", 0)
        correlation_id = getattr(record, "correlation_id", "unknown")

        # Cor baseada no status
        status_color = self._get_status_color(status_code)
        status_str = f"{status_color}{status_code}{reset}"

        # Formata timestamp
        timestamp = f"{Colors.DIM}{self.formatTime(record, self.DATE_FORMAT)}{reset}"

        # Formata nível
        levelname = f"{level_color}{record.levelname}{reset}"

        # Formata nome
        name = f"{Colors.BLUE}{record.name}{reset}"

        # Formata mensagem (METHOD path)
        message = record.getMessage()

        # Formata duração
        duration_str = f"{Colors.WHITE}{duration_ms}ms{reset}"

        # Formata correlation_id (abreviado)
        corr_short = correlation_id[:8] if len(correlation_id) > 8 else correlation_id
        corr_str = f"{Colors.DIM}{corr_short}{reset}"

        # Monta linha formatada
        return (
            f"{timestamp}{Colors.PIPE} |{reset} {levelname:<8}{Colors.PIPE} |{reset} "
            f"{name}{Colors.PIPE} |{reset} {message} → {status_str} | {duration_str} | {corr_str}"
        )

    def format(self, record: logging.LogRecord) -> str:
        """Formata record com cores."""
        # Detecta campos estruturados do RequestLoggingMiddleware
        if hasattr(record, "status_code"):
            return self._format_structured_request(record)

        # Pega cor baseada no nível
        level_color = self.LEVEL_COLORS.get(record.levelno, "")
        reset = Colors.RESET

        # Formata nível com cor
        levelname = f"{level_color}{record.levelname}{reset}"

        # Formata timestamp com cinza (DIM)
        timestamp = f"{Colors.DIM}{self.formatTime(record, self.DATE_FORMAT)}{reset}"

        # Formata nome com azul
        name = f"{Colors.BLUE}{record.name}{reset}"

        # Monta mensagem com cores
        raw_message = record.getMessage()

        # Detecta JSON na mensagem (formato: "mensagem {json}")
        message = raw_message
        json_data = None
        message_prefix = raw_message

        # Procura por JSON no final da mensagem (apenas dicts, não listas)
        # Listas como [123] são comuns em mensagens do uvicorn e não devem ser parseadas
        for i in range(len(raw_message) - 1, -1, -1):
            if raw_message[i] == "{":  # Apenas dicts, não listas []
                try:
                    json_str = raw_message[i:]
                    json_data = json.loads(json_str)
                    message_prefix = raw_message[:i].strip()
                    break
                except json.JSONDecodeError:
                    continue

        # Cabeçalho do log
        header = f"{timestamp}{Colors.PIPE} |{reset} {levelname:<8}{Colors.PIPE} |{reset} {name}{Colors.PIPE} |{reset} {message_prefix}"

        # Se achou JSON na mensagem, formata pretty
        if json_data is not None:
            formatted_json = self._pretty_format_value(json_data, reset)
            if "\n" in formatted_json:
                header += "\n" + formatted_json
            else:
                header += " " + formatted_json

        # Adiciona extra fields se existirem
        extra_lines = []
        for key, value in vars(record).items():
            if key.startswith("_"):
                continue
            # Pula campos padrão do LogRecord e campos internos do uvicorn
            if key in ("name", "msg", "args", "levelname", "levelno", "pathname",
                      "filename", "module", "lineno", "funcName", "created", "msecs",
                      "relativeCreated", "thread", "threadName", "processName",
                      "process", "getMessage", "exc_info", "exc_text", "stack_info",
                      "color_message"):  # uvicorn color_message - nós já aplicamos cores
                continue

            # Formata qualquer outro campo como extra
            formatted_value = self._pretty_format_value(value, reset)
            # Se o valor formatado tem quebras de linha, trata diferente
            if "\n" in formatted_value:
                extra_lines.append(f"\n  {Colors.DIM}{key}:{reset} {formatted_value}")
            else:
                extra_lines.append(f" {Colors.DIM}{key}:{reset} {formatted_value}")

        if extra_lines:
            # Une os extras na mesma linha se não tiver quebras
            flat_extras = [e for e in extra_lines if "\n" not in e]
            multiline_extras = [e for e in extra_lines if "\n" in e]

            if flat_extras:
                header += f" |{Colors.DIM}" + "".join(flat_extras) + reset

            if multiline_extras:
                header += "\n" + "".join(multiline_extras)

        return header


class SkybridgeLogger:
    """
    Logger estruturado para Skybridge.

    Suporta:
    - Console output (stdout)
    - Arquivo rotativo por data
    - Formato estruturado com extra context
    """

    def __init__(self, name: str = "skybridge", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Evita duplicação de handlers
        if self.logger.handlers:
            return

        # Formatter para arquivo (sem cores)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Handler de console COM cores
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter())
        self.logger.addHandler(console_handler)

        # Handler de arquivo SEM cores
        log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def _format(self, message: str, extra: dict[str, Any] | None = None) -> str:
        """Formata mensagem com extra context."""
        # Mantém apenas para compatibilidade - não mais usado
        return message

    def _serialize_extra(self, extra: dict[str, Any]) -> dict[str, str]:
        """Serializa extras para strings JSON mantendo tipos."""
        serialized = {}
        for key, value in extra.items():
            if isinstance(value, (dict, list, tuple)):
                # Converte para JSON string para preservar estrutura
                serialized[key] = json.dumps(value, ensure_ascii=False)
            else:
                serialized[key] = str(value)
        return serialized

    def _log_with_extra(self, level_func, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log com extras serializados como JSON para preservar tipos."""
        if extra:
            serialized = self._serialize_extra(extra)
            level_func(message, extra=serialized)
        else:
            level_func(message)

    def info(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log info."""
        self._log_with_extra(self.logger.info, message, extra)

    def error(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log error."""
        self._log_with_extra(self.logger.error, message, extra)

    def warning(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log warning."""
        self._log_with_extra(self.logger.warning, message, extra)

    def debug(self, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log debug."""
        self._log_with_extra(self.logger.debug, message, extra)

    def structured(self, message: str, data: dict[str, Any] | list[Any], level: str = "info") -> None:
        """Log com dados estruturados (dict/list) em formato pretty-print."""
        level_method = getattr(self.logger, level.lower(), self.logger.info)
        # Formata como JSON string para ser processado pelo formatter
        json_str = json.dumps(data, ensure_ascii=False, default=str)
        level_method(f"{message} {json_str}")

    def get_log_file_path(self) -> Path:
        """Retorna o caminho do arquivo de log atual."""
        return LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"


# Singleton global
_logger: SkybridgeLogger | None = None


def get_logger(name: str = "skybridge", level: str = "INFO") -> SkybridgeLogger:
    """Retorna logger global."""
    global _logger
    if _logger is None:
        _logger = SkybridgeLogger(name, level)
    return _logger


def get_log_file_path() -> Path:
    """Retorna o caminho do arquivo de log atual."""
    return LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"


def reset_logger() -> None:
    """Reseta o logger global (útil para testes)."""
    global _logger
    if _logger:
        # Remove todos os handlers
        for handler in _logger.logger.handlers[:]:
            handler.close()
            _logger.logger.removeHandler(handler)
    _logger = None


def print_separator(char: str = "─", width: int = 60) -> None:
    """Imprime uma linha separadora com o caractere e largura especificados."""
    separator = f"{Colors.DIM}{char * width}{Colors.RESET}"
    print(separator)


def print_banner(title: str, version: str | None = None) -> None:
    """Imprime um banner de entrada bonito estilo Claude."""
    width = 60

    print()
    print_separator("═", width)
    print(f"{Colors.BOLD}{Colors.CYAN}{' ' * ((width - len(title)) // 2)}{title}{Colors.RESET}")
    if version:
        version_text = f"v{version}"
        print(f"{Colors.DIM}{' ' * ((width - len(version_text)) // 2)}{version_text}{Colors.RESET}")
    print_separator("═", width)
    print()


def print_ngrok_urls(
    base_url: str,
    docs_url: str = "/docs",
    reserved_domain: str | None = None
) -> None:
    """Imprime URLs do ngrok com cores bonitas."""
    width = 60

    print()
    if reserved_domain:
        print_separator("─", width)
        print(f"  {Colors.YELLOW}URL:{Colors.RESET} {Colors.CYAN}{base_url}{Colors.RESET}")
        print_separator("─", 60)
    print()


def print_local_urls(
    host: str,
    port: int,
    docs_url: str = "/docs"
) -> None:
    """Imprime URLs locais com cores bonitas."""
    width = 60
    base_url = f"http://{host}:{port}"

    print()
    print_separator("═", width)
    print(f"{Colors.BOLD}{Colors.MAGENTA}  ══ Local Access ══{Colors.RESET}")
    print_separator("═", width)
    print(f"  {Colors.YELLOW}Ticket:{Colors.RESET}    {Colors.CYAN}{base_url}/ticket{Colors.RESET}")
    print(f"  {Colors.YELLOW}Envelope:{Colors.RESET}  {Colors.CYAN}{base_url}/envelope{Colors.RESET}")
    print(f"  {Colors.YELLOW}OpenAPI:{Colors.RESET}   {Colors.CYAN}{base_url}/openapi{Colors.RESET}")
    print(f"  {Colors.YELLOW}Docs:{Colors.RESET}      {Colors.CYAN}{base_url}{docs_url}{Colors.RESET}")
    print_separator("═", width)
    print()
