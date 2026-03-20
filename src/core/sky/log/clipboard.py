# coding: utf-8
"""
Clipboard - Lib externa com fallback vendored.

POC invalidou implementação 100% vendored. Usa lib 'clipboard' como preferência.
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


def _copy_windows_fallback(text: str) -> bool:
    """Copia texto para clipboard no Windows (fallback vendored)."""
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
        try:
            import subprocess

            process = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            cmd = f"$input | Set-Clipboard\r\n"
            process.communicate(input=(cmd + text).encode("utf-16-le"))
            return process.returncode == 0
        except Exception:
            return False


def _copy_macos_fallback(text: str) -> bool:
    """Copia texto para clipboard no macOS (fallback vendored)."""
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


def _copy_linux_fallback(text: str) -> bool:
    """Copia texto para clipboard no Linux (fallback vendored)."""
    import subprocess

    commands = [
        ["xclip", "-selection", "clipboard"],
        ["wl-copy"],
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

    return False


def copy_to_clipboard(text: str) -> bool:
    """Copia texto para clipboard de forma cross-platform.

    Tenta lib 'clipboard' primeiro, depois fallback vendored.

    Args:
        text: Texto para copiar

    Returns:
        True se sucesso, False caso contrário
    """
    if not text:
        return True

    # Tenta lib clipboard primeiro (POC validou como mais robusta)
    try:
        import clipboard

        clipboard.copy(text)
        return True
    except ImportError:
        # Lib não instalada - usa fallback vendored
        pass
    except Exception:
        # Lib falhou - tenta fallback vendored
        pass

    # Fallback vendored
    platform = _detect_platform()

    if platform == "windows":
        return _copy_windows_fallback(text)
    if platform == "macos":
        return _copy_macos_fallback(text)
    return _copy_linux_fallback(text)


__all__ = ["copy_to_clipboard"]
