# -*- coding: utf-8 -*-
"""
Result type — Retorna sucesso ou erro de forma tipada.

Pattern funcional que evita exceptions para fluxo de controle.
"""

from typing import TypeVar, Generic, Any
from dataclasses import dataclass
from enum import Enum

T = TypeVar("T")
E = TypeVar("E")


class Status(Enum):
    """Status de uma operação."""
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """
    Result type para retornos typed.

    Usage:
        success = Result.ok(value)
        failure = Result.error(error_msg)
    """
    status: Status
    value: T | None
    error: E | None

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """Cria um Result de sucesso."""
        return Result(status=Status.SUCCESS, value=value, error=None)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """Cria um Result de erro."""
        return Result(status=Status.FAILURE, value=None, error=error)

    @property
    def is_ok(self) -> bool:
        """Verifica se é sucesso."""
        return self.status == Status.SUCCESS

    @property
    def is_err(self) -> bool:
        """Verifica se é erro."""
        return self.status == Status.FAILURE

    def unwrap(self) -> T:
        """Retorna o valor ou lança RuntimeError se for erro."""
        if self.is_ok:
            return self.value  # type: ignore
        raise RuntimeError(f"Cannot unwrap error: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Retorna o valor ou default se for erro."""
        if self.is_ok:
            return self.value  # type: ignore
        return default

    def map(self, fn) -> "Result[Any, E]":
        """Mapeia o valor se for sucesso."""
        if self.is_ok:
            return Result.ok(fn(self.value))
        return Result.err(self.error)

    def and_then(self, fn) -> "Result[Any, E]":
        """Chain com outra função que retorna Result."""
        if self.is_ok:
            return fn(self.value)
        return Result.err(self.error)
