# -*- coding: utf-8 -*-
"""
Decorators — Registro automatico de handlers no registry.
"""

from typing import Callable, Any, ParamSpec, TypeVar

from kernel.contracts.result import Result
from kernel.registry.query_registry import get_query_registry

P = ParamSpec("P")
R = TypeVar("R")


def query(
    *,
    name: str,
    description: str | None = None,
    tags: list[str] | None = None,
    auth: str | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    notification_allowed: bool = False,
) -> Callable[[Callable[P, Result[Any, str]]], Callable[P, Result[Any, str]]]:
    """Decorador para registrar query handler automaticamente."""
    def decorator(func: Callable[P, Result[Any, str]]) -> Callable[P, Result[Any, str]]:
        get_query_registry().register(
            name=name,
            handler=func,
            description=description,
            kind="query",
            notification_allowed=notification_allowed,
            tags=tags,
            auth=auth,
            input_schema=input_schema,
            output_schema=output_schema,
        )
        return func

    return decorator


def command(
    *,
    name: str,
    description: str | None = None,
    tags: list[str] | None = None,
    auth: str | None = None,
    input_schema: dict[str, Any] | None = None,
    output_schema: dict[str, Any] | None = None,
    notification_allowed: bool = False,
) -> Callable[[Callable[P, Result[Any, str]]], Callable[P, Result[Any, str]]]:
    """Decorador para registrar command handler automaticamente."""
    def decorator(func: Callable[P, Result[Any, str]]) -> Callable[P, Result[Any, str]]:
        get_query_registry().register(
            name=name,
            handler=func,
            description=description,
            kind="command",
            notification_allowed=notification_allowed,
            tags=tags,
            auth=auth,
            input_schema=input_schema,
            output_schema=output_schema,
        )
        return func

    return decorator
