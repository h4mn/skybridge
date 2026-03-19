# coding: utf-8
"""
Módulo de eventos para comunicação loose-coupled entre componentes.

DOC: openspec/changes/refactor-chat-event-driven/specs/event-bus/spec.md

Implementa padrão publish-subscribe para desacoplar chat, TTS e UI.
"""

from core.sky.events.event_bus import BaseEvent, EventBus, InMemoryEventBus

__all__ = ["BaseEvent", "EventBus", "InMemoryEventBus"]
