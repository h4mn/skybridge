# -*- coding: utf-8 -*-
"""
Request Logging Middleware (RF002).

Middleware para logging estruturado de requisições HTTP.
Registra method, path, status_code, duration_ms, correlation_id e client_ip.
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
    - IP do cliente (com fallback para headers de proxy)

    Formato de log:
    timestamp | INFO | skybridge.request | GET /api/health → 200 | 15.2ms | 127.0.0.1 | abc12345
    """

    async def dispatch(self, request: Request, call_next):
        """Processa request e loga métricas."""
        start_time = time()

        # Correlation ID deve ser adicionado pelo CorrelationMiddleware
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        # Extrai IP do cliente (considera proxies)
        client_ip = self._get_client_ip(request)

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Em caso de exceção não tratada
            status_code = 500
            process_time = (time() - start_time) * 1000
            self._log_request(request, status_code, process_time, correlation_id, client_ip)
            raise

        # Calcula tempo de processamento
        process_time = (time() - start_time) * 1000

        # Loga a request
        self._log_request(request, status_code, process_time, correlation_id, client_ip)

        # Adiciona header com tempo de processamento
        response.headers["x-process-time"] = f"{process_time:.2f}ms"
        response.headers["x-correlation-id"] = correlation_id

        return response

    def _prefer_ipv4(self, ip: str) -> str:
        """
        Prioriza IPv4 sobre IPv6.

        Conversões:
        - ::1 (localhost IPv6) → 127.0.0.1
        - ::ffff:127.0.0.1 (IPv4 mapeado em IPv6) → 127.0.0.1
        - Outros IPv6: mantém original (não há conversão direta)

        Args:
            ip: Endereço IP (pode ser IPv4 ou IPv6)

        Returns:
            IPv4 se conversível, senão IP original
        """
        if not ip:
            return ip

        # IPv4 mapeado em IPv6 (::ffff:x.x.x.x)
        if ip.startswith("::ffff:"):
            ipv4 = ip[7:]  # Remove ::ffff:
            # Valida se é IPv4 válido
            parts = ipv4.split(".")
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                return ipv4

        # Localhost IPv6 (::1) → localhost IPv4
        if ip == "::1":
            return "127.0.0.1"

        # Se já for IPv4, retorna como está
        if "." in ip:
            return ip

        # IPv6 puro (não conversível), mantém original
        return ip

    def _get_client_ip(self, request: Request) -> str:
        """
        Extrai o IP real do cliente, considerando proxies reversos.

        Ordem de verificação (RFC 7239):
        1. X-Forwarded-For (primeiro IP da lista)
        2. X-Real-IP
        3. CF-Connecting-IP (Cloudflare)
        4. request.client.host (direto)

        Sempre retorna IPv4 quando possível.

        Returns:
            IP do cliente como string (preferencialmente IPv4), ou "unknown".
        """
        # Tenta X-Forwarded-For (pode ter múltiplos IPs: "client, proxy1, proxy2")
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Pega o primeiro IP (cliente original) e converte para IPv4 se possível
            ip = forwarded_for.split(",")[0].strip()
            return self._prefer_ipv4(ip)

        # Tenta X-Real-IP (comum em nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return self._prefer_ipv4(real_ip.strip())

        # Tenta CF-Connecting-IP (Cloudflare)
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return self._prefer_ipv4(cf_ip.strip())

        # Fallback para conexão direta
        if request.client and request.client.host:
            return self._prefer_ipv4(request.client.host)

        return "unknown"

    def _log_request(
        self,
        request: Request,
        status_code: int,
        process_time: float,
        correlation_id: str,
        client_ip: str,
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
        log_record.client_ip = client_ip

        # Envia diretamente para o handler (bypass do logger para evitar duplicação)
        logger.handle(log_record)
