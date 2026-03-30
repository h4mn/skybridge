# -*- coding: utf-8 -*-
"""Application Queries - Queries CQRS da aplicação Discord."""

from .fetch_messages_query import FetchMessagesQuery
from .list_threads_query import ListThreadsQuery

__all__ = ["FetchMessagesQuery", "ListThreadsQuery"]
