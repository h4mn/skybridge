# -*- coding: utf-8 -*-
"""
Utilitários para processamento de logs no WebUI.

Converte códigos ANSI coloridos do console para HTML/markdown e fornece
utilitários para formatação de logs.
"""
from __future__ import annotations

import re
from typing import Any

# Mapeamento de códigos ANSI para cores CSS
ANSI_COLOR_MAP = {
    '30': 'black',     # Preto
    '31': 'red',       # Vermelho
    '32': 'green',     # Verde
    '33': 'yellow',    # Amarelo
    '34': 'blue',      # Azul
    '35': 'magenta',   # Magenta
    '36': 'cyan',      # Ciano
    '37': 'white',     # Branco
    '90': 'gray',      # Cinza escuro
    '91': 'light-red',     # Vermelho claro
    '92': 'light-green',   # Verde claro
    '93': 'light-yellow',  # Amarelo claro
    '94': 'light-blue',    # Azul claro
    '95': 'light-magenta', # Magenta claro
    '96': 'light-cyan',    # Ciano claro
    '97': 'light-white',   # Branco claro
}

# Mapeamento de estilos ANSI
ANSI_STYLE_MAP = {
    '0': 'reset',      # Reset
    '1': 'bold',       # Negrito
    '2': 'dim',        # Escuro
    '3': 'italic',     # Itálico
    '4': 'underline',  # Sublinhado
    '7': 'reverse',    # Reverso
    '9': 'strikethrough', # Riscado
}


def ansi_to_html(text: str) -> str:
    """
    Converte códigos ANSI coloridos para HTML.

    Args:
        text: Texto com códigos ANSI (ex: "[97mWebUI[0m")

    Returns:
        Texto HTML com tags <span> para estilos
    """
    if not text:
        return text

    # Regex para capturar códigos ANSI: \x1b[...m ou [...m
    ansi_pattern = re.compile(r'\x1b\[([0-9;]+)m|(\[([0-9;]+)m\])')

    result = []
    current_styles = {'color': None, 'bold': False}

    pos = 0
    for match in ansi_pattern.finditer(text):
        # Adiciona texto antes do código ANSI
        if match.start() > pos:
            plain_text = text[pos:match.start()]
            if current_styles:
                styles = []
                if current_styles['color']:
                    styles.append(f"color: {current_styles['color']}")
                if current_styles['bold']:
                    styles.append("font-weight: bold")
                style_attr = f" style=\"{'; '.join(styles)}\"" if styles else ""
                result.append(f'<span{style_attr}>{plain_text}</span>')
            else:
                result.append(plain_text)

        # Processa códigos ANSI
        codes = match.group(1) or match.group(3)
        for code in codes.split(';'):
            if code == '0':
                # Reset
                current_styles = {'color': None, 'bold': False}
            elif code in ANSI_COLOR_MAP:
                current_styles['color'] = ANSI_COLOR_MAP[code]
            elif code == '1':
                current_styles['bold'] = True

        pos = match.end()

    # Adiciona texto restante
    if pos < len(text):
        plain_text = text[pos:]
        if current_styles:
            styles = []
            if current_styles['color']:
                styles.append(f"color: {current_styles['color']}")
            if current_styles['bold']:
                styles.append("font-weight: bold")
            style_attr = f" style=\"{'; '.join(styles)}\"" if styles else ""
            result.append(f'<span{style_attr}>{plain_text}</span>')
        else:
            result.append(plain_text)

    return ''.join(result)


def strip_ansi_codes(text: str) -> str:
    """
    Remove todos os códigos ANSI do texto.

    Args:
        text: Texto com códigos ANSI

    Returns:
        Texto sem códigos ANSI
    """
    if not text:
        return text
    # Remove todos os códigos ANSI
    return re.sub(r'\x1b\[[0-9;]+m', '', text)


def parse_log_line(line: str) -> dict[str, Any] | None:
    """
    Parseia uma linha de log no formato Skybridge.

    Formato esperado:
    YYYY-MM-DD HH:MM:SS | LEVEL | LOGGER | MESSAGE

    Args:
        line: Linha de log cru (pode conter códigos ANSI)

    Returns:
        Dict com keys: timestamp, level, logger, message, message_html
        ou None se a linha não tiver o formato esperado
    """
    line = line.rstrip()
    if not line:
        return None

    # Regex para parsear formato: timestamp | level | logger | message
    # Level pode ter espaços de preenchimento, logger é sem espaços
    match = re.match(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\S+)\s*\| (\S+)\s*\| (.+)$',
        line
    )

    if not match:
        return None

    timestamp, level, logger_name, message = match.groups()

    return {
        'timestamp': timestamp,
        'level': level.strip(),
        'logger': logger_name.strip(),
        'message': message,
        'message_html': ansi_to_html(message),
        'raw': line
    }


def format_log_level(level: str) -> str:
    """
    Formata nível de log para exibição.

    Args:
        level: Nível de log (ex: INFO, WARNING, ERROR)

    Returns:
        Badge HTML ou texto simples
    """
    level_upper = level.upper()
    colors = {
        'DEBUG': 'secondary',
        'INFO': 'primary',
        'WARNING': 'warning',
        'ERROR': 'danger',
        'CRITICAL': 'danger',
    }
    return colors.get(level_upper, 'secondary')
