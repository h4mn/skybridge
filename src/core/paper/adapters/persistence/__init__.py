"""
Persistence Adapters - Paper Trading

SQLite+WAL é o único backend de persistência.
"""
from .sqlite_paper_state import SQLitePaperState

__all__ = [
    "SQLitePaperState",
]
