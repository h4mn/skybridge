# coding: utf-8
"""
Clipboard vendorizado - Implementação interna de cópia para clipboard.

Baseado no pyperclip mas simplificado e sem dependências externas.
Suporta Windows, macOS e Linux.
"""

import sys
from typing import Literal

Platform = Literal["windows", "macos", "linux"]


def _detect_platform() -> Platform:
    """Detecta a plataforma atual."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def _copy_windows(text: str) -> bool:
    """Copia texto para clipboard no Windows."""
    try:
        # Tenta win32clipboard primeiro (mais rápido)
        import win32clipboard  # type: ignore

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        return True
    except Exception:
        # Fallback para subprocess com PowerShell
        # Usa stdin para evitar problemas de escape
        try:
            import subprocess

            # Passa texto via stdin para evitar problemas com caracteres especiais
            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Comando PowerShell que lê de stdin e define o clipboard
            cmd = f"$input | Set-Clipboard\r\n"
            process.communicate(input=(cmd + text).encode("utf-16-le"))
            return process.returncode == 0
        except Exception:
            return False


def _copy_macos(text: str) -> bool:
    """Copia texto para clipboard no macOS."""
    try:
        import subprocess

        process = subprocess.Popen(
            ["pbcopy"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.communicate(text.encode("utf-8"))
        return process.returncode == 0
    except Exception:
        return False


def _copy_linux(text: str) -> bool:
    """Copia texto para clipboard no Linux."""
    import subprocess

    # Tenta xclip primeiro
    commands = [
        ["xclip", "-selection", "clipboard"],
        ["wl-copy"],  # Wayland
    ]

    for cmd in commands:
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            process.communicate(text.encode("utf-8"))
            if process.returncode == 0:
                return True
        except FileNotFoundError:
            continue
        except Exception:
            continue

    # Nenhum comando funcionou - retorna False
    return False


def copy_to_clipboard(text: str) -> bool:
    """Copia texto para clipboard de forma cross-platform.

    Args:
        text: Texto para copiar

    Returns:
        True se sucesso, False caso contrário
    """
    if not text:
        return True

    platform = _detect_platform()

    if platform == "windows":
        return _copy_windows(text)
    if platform == "macos":
        return _copy_macos(text)
    return _copy_linux(text)


__all__ = ["copy_to_clipboard"]
