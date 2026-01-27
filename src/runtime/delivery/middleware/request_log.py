# -*- coding: utf-8 -*-
"""
Request Logging Middleware (RF002).

Middleware para logging estruturado de requisições HTTP.
Registra method, path, status_code, duration_ms e correlation_id.
"""

import logging
from time import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


# Logger específico para requests HTTP
logger = logging.getLogger("skybridge.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requisições HTTP com métricas.

    Registra:
    - Método HTTP e path
    - Status code da resposta (com cor)
    - Tempo de processamento em ms
    - Correlation ID da request

    Formato de log:
    timestamp | INFO | skybridge.request | GET /api/health → 200 | 15.2ms | abc12345
    """

    async def dispatch(self, request: Request, call_next):
        """Processa request e loga métricas."""
        start_time = time()

        # Correlation ID deve ser adicionado pelo CorrelationMiddleware
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Em caso de exceção não tratada
            status_code = 500
            process_time = (time() - start_time) * 1000
            self._log_request(request, status_code, process_time, correlation_id)
            raise

        # Calcula tempo de processamento
        process_time = (time() - start_time) * 1000

        # Loga a request
        self._log_request(request, status_code, process_time, correlation_id)

        # Adiciona header com tempo de processamento
        response.headers["x-process-time"] = f"{process_time:.2f}ms"
        response.headers["x-correlation-id"] = correlation_id

        return response

    def _log_request(
        self,
        request: Request,
        status_code: int,
        process_time: float,
        correlation_id: str
    ):
        """
        Loga a requisição com campos estruturados.

        Cria um LogRecord manual com campos extras para o ColorFormatter.
        """
        # Monta mensagem com method e path
        message = f"{request.method} {request.url.path}"

        # Cria LogRecord manual com campos estruturados
        log_record = logging.LogRecord(
            name="skybridge.request",
            level=logging.INFO,
            pathname="", lineno=0,
            msg=message,
            args=(), exc_info=None,
        )
        # Adiciona campos estruturados para o ColorFormatter
        log_record.status_code = status_code
        log_record.duration_ms = round(process_time, 2)
        log_record.correlation_id = correlation_id

        # Envia diretamente para o handler (bypass do logger para evitar duplicação)
        logger.handle(log_record)
