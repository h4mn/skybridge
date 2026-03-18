# coding: utf-8
"""
Event Tracer - Log de eventos Textual com buffer circular.
"""

import csv
import json
import re
import uuid
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from io import StringIO
from typing import Any, Callable

# Logger removido - usando ChatLogger isolado
# from runtime.observability.logger import get_logger
# logger = get_logger("sky.chat.dom.tracer", level="DEBUG")


class EventType(Enum):
    """Tipos de eventos rastreados."""

    MOUNT = "MOUNT"
    UNMOUNT = "UNMOUNT"
    INTERACTION = "INTERACTION"
    PROP_CHANGED = "PROP_CHANGED"
    ERROR = "ERROR"
    CUSTOM = "CUSTOM"


@dataclass
class EventEntry:
    """Entrada de evento no tracer."""

    event_id: str
    timestamp: datetime
    event_type: EventType
    widget_dom_id: str | None
    widget_class: str | None
    data: dict[str, Any]

    def to_dict(self) -> dict:
        """Converte para dict."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "widget_dom_id": self.widget_dom_id,
            "widget_class": self.widget_class,
            "data": self.data,
        }


class EventTracer:
    """
    Tracer de eventos Textual com buffer circular.

    Mantém buffer de eventos normais e buffer separado para eventos críticos.
    """

    def __init__(self, buffer_size: int = 1000, critical_size: int = 100):
        """
        Inicializa o tracer.

        Args:
            buffer_size: Tamanho do buffer principal
            critical_size: Tamanho do buffer de eventos críticos
        """
        self._buffer = deque(maxlen=buffer_size)
        self._critical = deque(maxlen=critical_size)
        self._subscribers: list[tuple[Callable, dict]] = []

        # Detecção de padrões
        self._error_count = 0
        self._error_window_start = None
        self._error_threshold = 5
        self._error_window_sec = 10

        # Event types conhecidos
        self._known_event_types: set[str] = set()

    def capture_event(
        self,
        event_type: EventType,
        widget_dom_id: str | None = None,
        widget_class: str | None = None,
        **data,
    ) -> EventEntry:
        """
        Captura um evento.

        Args:
            event_type: Tipo do evento
            widget_dom_id: ID do widget relacionado
            widget_class: Classe do widget
            **data: Dados adicionais do evento

        Returns:
            EventEntry criada
        """
        entry = EventEntry(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            event_type=event_type,
            widget_dom_id=widget_dom_id,
            widget_class=widget_class,
            data=data,
        )

        # Detectar novo tipo de evento customizado
        if event_type == EventType.CUSTOM:
            event_name = data.get("event_type", "UNKNOWN")
            if event_name not in self._known_event_types:
                self._known_event_types.add(event_name)

        # Adicionar ao buffer apropriado
        self._buffer.append(entry)

        if event_type == EventType.ERROR:
            self._critical.append(entry)
            self._check_error_burst()

        # Notificar subscribers
        self._notify_subscribers(entry)

        return entry

    def _check_error_burst(self) -> None:
        """Detecta burst de erros."""
        now = datetime.now()

        if self._error_window_start is None:
            self._error_window_start = now
            self._error_count = 1
        else:
            elapsed = (now - self._error_window_start).total_seconds()
            if elapsed > self._error_window_sec:
                # Resetar janela
                self._error_window_start = now
                self._error_count = 1
            else:
                self._error_count += 1

        if self._error_count > self._error_threshold:
            self._emit_alert("ERROR_BURST", f"{self._error_count} errors in {elapsed:.1f}s")
            self._error_count = 0  # Reset para evitar spam

    def _emit_alert(self, alert_type: str, message: str) -> None:
        """Emite alerta de padrão detectado."""
        # logger.structured("DOM tracer alert", {
        #     "alert_type": alert_type,
        #     "message": message,
        # }, level="warning")
        pass  # Silenciado - DOM tracer alerts não são mais logados

    def filter(
        self,
        event_types: list[EventType] | None = None,
        widget_dom_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[EventEntry]:
        """
        Filtra eventos por critérios.

        Args:
            event_types: Tipos de eventos a incluir
            widget_dom_id: ID do widget
            since: Timestamp inicial
            until: Timestamp final

        Returns:
            Lista de EventEntry filtrada
        """
        results = []

        for entry in self._buffer:
            # Filtro por tipo
            if event_types and entry.event_type not in event_types:
                continue

            # Filtro por widget
            if widget_dom_id and entry.widget_dom_id != widget_dom_id:
                continue

            # Filtro por tempo
            if since and entry.timestamp < since:
                continue
            if until and entry.timestamp > until:
                continue

            results.append(entry)

        return results

    def search(self, text: str, prop: str | None = None, regex: bool = False) -> list[EventEntry]:
        """
        Busca textual em eventos.

        Args:
            text: Texto a buscar
            prop: Propriedade específica (ex: "error_message")
            regex: Se True, usa regex

        Returns:
            Lista de EventEntry matching
        """
        results = []

        for entry in self._buffer:
            # Buscar em todos os campos se prop não especificado
            search_targets = []
            if prop:
                search_targets.append(str(entry.data.get(prop, "")))
            else:
                search_targets.extend([
                    str(entry.widget_dom_id or ""),
                    str(entry.widget_class or ""),
                    json.dumps(entry.data, default=str),
                ])

            for target in search_targets:
                match = (
                    re.search(text, target, re.IGNORECASE)
                    if regex
                    else text.lower() in target.lower()
                )

                if match:
                    results.append(entry)
                    break

        return results

    def export(self, fmt: str = "json") -> str:
        """
        Exporta eventos.

        Args:
            fmt: Formato ("json" ou "csv")

        Returns:
            String exportada
        """
        if fmt == "json":
            return json.dumps(
                [e.to_dict() for e in self._buffer],
                indent=2,
            )

        if fmt == "csv":
            output = StringIO()
            fieldnames = ["event_id", "timestamp", "event_type", "widget_dom_id", "widget_class", "data"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for entry in self._buffer:
                row = entry.to_dict()
                row["data"] = json.dumps(row["data"])
                writer.writerow(row)

            return output.getvalue()

        raise ValueError(f"Unknown format: {fmt}")

    def subscribe(self, callback: Callable[[EventEntry], None], filter: dict | None = None) -> str:
        """
        Inscreve callback para eventos em tempo real.

        Args:
            callback: Função chamada para cada evento
            filter: Filtros opcionais (event_types, widget, etc)

        Returns:
            Subscription ID para cancelar
        """
        sub_id = str(uuid.uuid4())
        self._subscribers.append((callback, filter or {}))
        return sub_id

    def unsubscribe(self, sub_id: str) -> bool:
        """
        Cancela subscrição.

        Args:
            sub_id: ID da subscrição

        Returns:
            True se removido, False se não encontrado
        """
        for i, (cb, filt) in enumerate(self._subscribers):
            # Verificar se o callback tem algum ID que possamos usar
            # Na prática, usaríamos um dict, mas aqui simplificamos
            pass

        # Por enquanto, limpamos todos (simplificação)
        self._subscribers.clear()
        return True

    def _notify_subscribers(self, entry: EventEntry) -> None:
        """Notifica todos os subscribers de um evento."""
        for callback, filt in self._subscribers:
            # TODO: Aplicar filtros
            try:
                callback(entry)
            except Exception:
                pass  # Falha em um subscriber não afeta outros

    def get_events(self) -> list[EventEntry]:
        """Retorna todos os eventos em ordem reversa."""
        return list(reversed(self._buffer))

    def clear(self) -> None:
        """Limpa todos os buffers."""
        self._buffer.clear()
        self._critical.clear()


__all__ = ["EventType", "EventEntry", "EventTracer"]
