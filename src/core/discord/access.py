"""
Gerenciamento de acesso via access.json.

Este módulo é responsável por:
- Ler/escrever access.json
- Validar acesso de usuários
- Gerenciar códigos de pareamento pendentes
- Pruning de entradas expiradas

Compatível com o skill /discord:access — não alterar schema do access.json.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from .presentation.dto.legacy_dto import Access, DMPolicy, PendingEntry

if TYPE_CHECKING:
    pass

# Diretório de estado
STATE_DIR = Path(
    os.environ.get("DISCORD_STATE_DIR", Path.home() / ".claude" / "channels" / "discord")
)
ACCESS_FILE = STATE_DIR / "access.json"
APPROVED_DIR = STATE_DIR / "approved"

# Cache estático (modo STATIC)
BOOT_ACCESS: Access | None = None


def default_access() -> Access:
    """Retorna Access com valores padrão."""
    return Access(
        dm_policy=DMPolicy.PAIRING,
        allow_from=[],
        groups={},
        pending={},
    )


def read_access_file() -> Access:
    """Lê access.json do disco."""
    try:
        raw = ACCESS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        return Access.model_validate(data)
    except FileNotFoundError:
        return default_access()
    except json.JSONDecodeError as e:
        # Arquivo corrompido — move para backup e retorna fresh
        _backup_corrupt()
        return default_access()
    except Exception as e:
        _backup_corrupt()
        return default_access()


def _backup_corrupt() -> None:
    """Faz backup de access.json corrompido."""
    if ACCESS_FILE.exists():
        import time

        backup = ACCESS_FILE.with_suffix(f".corrupt-{int(time.time() * 1000)}")
        try:
            shutil.move(str(ACCESS_FILE), str(backup))
        except Exception:
            pass


def load_access() -> Access:
    """Carrega Access, usando cache estático se configurado."""
    global BOOT_ACCESS

    # Modo estático: usa cache de boot
    if os.environ.get("DISCORD_ACCESS_MODE") == "static":
        if BOOT_ACCESS is not None:
            return BOOT_ACCESS
        BOOT_ACCESS = read_access_file()
        # Downgrade pairing → allowlist em modo estático
        if BOOT_ACCESS.dm_policy == DMPolicy.PAIRING:
            BOOT_ACCESS.dm_policy = DMPolicy.ALLOWLIST
        BOOT_ACCESS.pending = {}
        return BOOT_ACCESS

    return read_access_file()


def save_access(access: Access) -> None:
    """Salva Access para access.json atomicamente."""
    # Não salva em modo estático
    if os.environ.get("DISCORD_ACCESS_MODE") == "static":
        return

    # Garante diretório existe
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Escrita atômica: tmp → rename
    tmp_file = ACCESS_FILE.with_suffix(".tmp")
    content = access.model_dump(by_alias=True, exclude_none=True)

    tmp_file.write_text(
        json.dumps(content, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    shutil.move(str(tmp_file), str(ACCESS_FILE))


def prune_expired(access: Access) -> bool:
    """Remove entradas pending expiradas. Retorna True se houve mudança."""
    import time

    now = int(time.time() * 1000)
    changed = False

    expired = [code for code, entry in access.pending.items() if entry.expires_at < now]

    for code in expired:
        del access.pending[code]
        changed = True

    return changed


def generate_pairing_code() -> str:
    """Gera código de pareamento de 6 caracteres hex."""
    return secrets.token_hex(3)


def create_pending_entry(
    access: Access, sender_id: str, chat_id: str, expires_in_ms: int = 3600000
) -> str:
    """
    Cria entrada pendente de pareamento.

    Args:
        access: Access a modificar
        sender_id: ID do usuário Discord
        chat_id: ID do canal DM
        expires_in_ms: Tempo até expirar (default: 1h)

    Returns:
        Código de pareamento gerado
    """
    import time

    code = generate_pairing_code()
    now = int(time.time() * 1000)

    access.pending[code] = PendingEntry(
        sender_id=sender_id,
        chat_id=chat_id,
        created_at=now,
        expires_at=now + expires_in_ms,
        replies=1,
    )

    return code


def find_pending_by_sender(access: Access, sender_id: str) -> tuple[str, PendingEntry] | None:
    """Encontra entrada pendente por sender_id."""
    for code, entry in access.pending.items():
        if entry.sender_id == sender_id:
            return code, entry
    return None


def approve_pairing(access: Access, code: str) -> tuple[str, str] | None:
    """
    Aprova pareamento.

    Args:
        access: Access a modificar
        code: Código de pareamento

    Returns:
        (sender_id, chat_id) se aprovado, None se não encontrado/expirado
    """
    entry = access.pending.get(code)
    if entry is None:
        return None

    # Verifica expiração
    import time

    if entry.expires_at < int(time.time() * 1000):
        del access.pending[code]
        return None

    sender_id = entry.sender_id
    chat_id = entry.chat_id

    # Adiciona à allowlist
    if sender_id not in access.allow_from:
        access.allow_from.append(sender_id)

    # Remove do pending
    del access.pending[code]

    # Cria arquivo de aprovação para o servidor Discord ler
    _write_approval(sender_id, chat_id)

    return sender_id, chat_id


def _write_approval(sender_id: str, chat_id: str) -> None:
    """Escreve arquivo de aprovação para poll do servidor."""
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    approval_file = APPROVED_DIR / sender_id
    approval_file.write_text(chat_id, encoding="utf-8")


def check_approvals() -> list[tuple[str, str]]:
    """
    Verifica aprovações pendentes (poll).

    Returns:
        Lista de (sender_id, chat_id) aprovados
    """
    if not APPROVED_DIR.exists():
        return []

    approved = []
    for approval_file in APPROVED_DIR.iterdir():
        if approval_file.is_file():
            sender_id = approval_file.name
            try:
                chat_id = approval_file.read_text(encoding="utf-8").strip()
                if chat_id:
                    approved.append((sender_id, chat_id))
            except Exception:
                pass
            # Remove arquivo após ler
            approval_file.unlink()

    return approved


# =============================================================================
# Gate Functions
# =============================================================================


class GateResult:
    """Resultado do gate de acesso."""

    def __init__(
        self,
        action: str,
        access: Access | None = None,
        code: str | None = None,
        is_resend: bool = False,
    ):
        self.action = action  # 'deliver', 'drop', 'pair'
        self.access = access
        self.code = code
        self.is_resend = is_resend


def gate_dm(access: Access, sender_id: str) -> GateResult:
    """
    Avalia acesso para mensagem privada.

    Returns:
        GateResult com action: 'deliver', 'drop', ou 'pair'
    """
    # Política desabilitada
    if access.dm_policy == DMPolicy.DISABLED:
        return GateResult(action="drop")

    # Usuário já autorizado
    if sender_id in access.allow_from:
        return GateResult(action="deliver", access=access)

    # Modo allowlist — drop se não está na lista
    if access.dm_policy == DMPolicy.ALLOWLIST:
        return GateResult(action="drop")

    # Modo pairing — gera ou reutiliza código
    existing = find_pending_by_sender(access, sender_id)
    if existing:
        code, entry = existing
        # Limite de reenvios
        if entry.replies >= 2:
            return GateResult(action="drop")
        # Incrementa contador
        entry.replies += 1
        save_access(access)
        return GateResult(action="pair", code=code, is_resend=True)

    # Cap de pendings
    if len(access.pending) >= 3:
        return GateResult(action="drop")

    # Cria novo código
    code = create_pending_entry(access, sender_id, sender_id)  # DM: chat_id = sender_id
    save_access(access)
    return GateResult(action="pair", code=code, is_resend=False)


def gate_group(
    access: Access, channel_id: str, sender_id: str, is_thread: bool = False, parent_id: str | None = None, is_forum: bool = False
) -> GateResult:
    """
    Avalia acesso para canal de grupo.

    Threads herdam política do canal pai.
    Canais de fórum são tratados como grupos com política específica.

    Args:
        access: Access atual
        channel_id: ID do canal (ou thread)
        sender_id: ID do usuário
        is_thread: Se mensagem veio de thread
        parent_id: ID do canal pai (se thread)
        is_forum: Se canal é um ForumChannel

    Returns:
        GateResult com action: 'deliver' ou 'drop'
    """
    # Lookup pelo canal pai se for thread
    lookup_id = parent_id if is_thread and parent_id else channel_id

    policy = access.groups.get(lookup_id)
    if not policy:
        return GateResult(action="drop")

    # Para fóruns, verificar se a política está configurada para fóruns
    if is_forum and not policy.is_forum:
        # Política existe mas não está marcada como fórum - verificar fallback
        # Por segurança, drop se não configurado explicitamente para fórum
        return GateResult(action="drop")

    # Verifica allowlist do grupo
    if policy.allow_from and sender_id not in policy.allow_from:
        return GateResult(action="drop")

    # requireMention é verificado externamente (precisa do message object)
    return GateResult(action="deliver", access=access)
