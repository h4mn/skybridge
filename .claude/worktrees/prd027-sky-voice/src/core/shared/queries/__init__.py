# -*- coding: utf-8 -*-
"""Shared Queries — Queries compartilhadas entre contextos."""

from core.shared.queries.health import health_query
from core.shared.queries.github import create_issue_query

__all__ = ["health_query", "create_issue_query"]
