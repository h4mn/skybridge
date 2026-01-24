# -*- coding: utf-8 -*-
"""
Routes - Rotas da API Skybridge.

Thin adapters que chamam handlers registrados.
"""

from typing import Any, Union
from pathlib import Path
import time
import uuid
import yaml

from fastapi import APIRouter, Request, Response, Body, Query
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from kernel import get_query_registry
from kernel.registry.skyrpc_registry import get_skyrpc_registry
from kernel.schemas.schemas import (
    SkyRpcDiscovery,
    SkyRpcHandler,
    ReloadResponse,
    Kind,
)
from runtime.config.config import get_security_config
from runtime.observability.logger import get_logger

logger = get_logger()

_rate_limit_state: dict[str, list[float]] = {}
_privacy_text: str | None = None
_ticket_store: dict[str, dict[str, Any]] = {}
_TICKET_TTL_SECONDS = 30


class EnvelopeDetail(BaseModel):
    """Envelope estruturado Sky-RPC v0.2."""
    context: str = Field(..., description="Contexto da operação (ex.: fileops.read)")
    subject: str | None = Field(None, description="Entidade-alvo (arquivo, job, secret, etc)")
    action: str = Field(..., description="Ação dentro do contexto (read, create, list...)")
    payload: dict[str, Any] = Field(..., description="Dados específicos da execução")

    @field_validator('payload')
    @classmethod
    def payload_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v or len(v) == 0:
            raise ValueError("Payload cannot be empty (minProperties: 1)")
        return v


class EnvelopeRequest(BaseModel):
    """Sky-RPC envelope request v0.2."""
    ticket_id: str
    detail: Union[str, EnvelopeDetail, None] = Field(None, description="Detalhes da operação (legado string ou estruturado)")
    model_config = ConfigDict(extra="allow")

def _is_localhost(host: str) -> bool:
    return host in ("127.0.0.1", "::1", "localhost")

def _check_rate_limit(client_id: str, limit_per_minute: int) -> int | None:
    if limit_per_minute <= 0:
        return None
    now = time.monotonic()
    window = 60.0
    entries = _rate_limit_state.get(client_id, [])
    entries = [ts for ts in entries if now - ts < window]
    if len(entries) >= limit_per_minute:
        retry_after = max(1, int(window - (now - entries[0]) + 0.999))
        _rate_limit_state[client_id] = entries
        return retry_after
    entries.append(now)
    _rate_limit_state[client_id] = entries
    return None


def _extract_envelope_attrs(
    detail_type: str,
    detail: Union[str, EnvelopeDetail, None],
    flat_params: dict[str, Any],
) -> dict[str, Any]:
    """
    Extrai atributos do envelope para logs de observabilidade.

    Returns:
        Dict com atributos relevantes conforme detail_type
    """
    if detail_type == "structured" and isinstance(detail, EnvelopeDetail):
        return {
            "context": detail.context,
            "action": detail.action,
            "subject": detail.subject,
            "payload_keys": list(detail.payload.keys()),
            "payload_size": len(detail.payload),
        }
    elif detail_type == "legacy" and isinstance(detail, str):
        return {
            "detail_value": detail,
        }
    elif detail_type == "legacy":
        # Mapeamento reverso (detalhe em flat_params)
        detalhe_value = flat_params.get("detalhe", "")
        return {
            "detail_value": detalhe_value,
            "has_detalhe": "detalhe" in flat_params,
            "has_detalhe_n": any(k.startswith("detalhe_") for k in flat_params.keys()),
        }
    return {"detail_type": detail_type}


def _parse_detail(
    detail: Union[str, EnvelopeDetail, None],
    model_extra: dict[str, Any],
) -> tuple[dict[str, Any], str | None, str]:
    """
    Parser de envelope Sky-RPC v0.2 com compatibilidade legada.

    Returns:
        (flat_params, error, detail_type) onde detail_type é "legacy", "structured" ou "none"
    """
    # Caso 1: Envelope estruturado v0.2
    if isinstance(detail, EnvelopeDetail):
        # Extrair payload como parâmetros flat
        flat_params = dict(detail.payload)
        # Adicionar subject como "detalhe" para mapear para o primeiro parâmetro required do handler
        if detail.subject:
            flat_params["detalhe"] = detail.subject
        return flat_params, None, "structured"

    # Caso 2: String (legado v0.1)
    if isinstance(detail, str):
        return {"detalhe": detail}, None, "legacy"

    # Caso 3: Mapeamento reverso (detalhe -> detail) via model_extra
    # Verificar se há campos legados em model_extra (para compatibilidade)
    if "detalhe" in model_extra:
        return {"detalhe": model_extra["detalhe"]}, None, "legacy"

    # Buscar detalhe_1, detalhe_2, etc.
    flat_params = {}
    for key, value in model_extra.items():
        if key == "detalhe" or key.startswith("detalhe_"):
            flat_params[key] = value

    if flat_params:
        return flat_params, None, "legacy"

    # Caso 0: detail é None e não há campos legados (requests sem detail)
    if detail is None:
        return {}, None, "none"

    return {}, "Invalid detail: expected string or structured object", "unknown"


def _map_flat_details(
    handler: Any,
    flat_params: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    ordered: list[Any] = []
    if "detalhe" in flat_params:
        ordered.append(flat_params["detalhe"])
    numbered = []
    for key, value in flat_params.items():
        if key.startswith("detalhe_"):
            suffix = key.split("_", 1)[1]
            if suffix.isdigit():
                numbered.append((int(suffix), value))
            else:
                return {}, f"Invalid detalhe key: {key}"
    ordered.extend(value for _, value in sorted(numbered))

    schema = handler.input_schema or {}
    required = schema.get("required") or []
    properties = schema.get("properties") or {}

    if not required and not properties:
        # Se o handler nao tem schema, ignora parametros
        return {}, None

    payload = {
        key: value
        for key, value in flat_params.items()
        if key != "detalhe" and not key.startswith("detalhe_")
    }

    args: dict[str, Any] = {}
    ordered_index = 0
    missing_required: list[str] = []

    for key in required:
        if key in payload:
            args[key] = payload.pop(key)
        elif ordered_index < len(ordered):
            args[key] = ordered[ordered_index]
            ordered_index += 1
        else:
            missing_required.append(key)

    if missing_required:
        return {}, "Missing required detalhes"

    target_keys = list(properties.keys()) if properties else []
    for key in target_keys:
        if key in args:
            continue
        if key in payload:
            args[key] = payload.pop(key)
        elif ordered_index < len(ordered):
            args[key] = ordered[ordered_index]
            ordered_index += 1

    return args, None

def _sky_rpc_error_response(
    *,
    code: int,
    message: str,
    ticket_id: str | None,
    method: str | None,
    correlation_id: str,
    data: dict[str, Any] | None = None,
) -> JSONResponse:
    payload_data = {
        "method": method,
        "ticket_id": ticket_id,
        "correlation_id": correlation_id,
    }
    if data:
        payload_data.update(data)
    payload = {
        "ok": False,
        "id": ticket_id,
        "error": {
            "code": code,
            "message": message,
            "data": payload_data,
        },
    }
    return JSONResponse(status_code=200, content=payload)

def _load_privacy_text() -> str:
    global _privacy_text
    if _privacy_text is None:
        repo_root = None
        for parent in Path(__file__).resolve().parents:
            if (parent / "docs").is_dir() and (parent / "src").is_dir():
                repo_root = parent
                break
        if repo_root is None:
            repo_root = Path.cwd()
        privacy_path = repo_root / "docs" / "privacy.md"
        _privacy_text = privacy_path.read_text(encoding="utf-8")
    return _privacy_text

def _create_ticket(method: str, client_id: str) -> dict[str, Any]:
    ticket_id = uuid.uuid4().hex[:8]
    expires_at = time.time() + _TICKET_TTL_SECONDS
    ticket = {
        "id": ticket_id,
        "method": method,
        "client_id": client_id,
        "expires_at": expires_at,
    }
    _ticket_store[ticket_id] = ticket
    return ticket

def _get_ticket(ticket_id: str) -> tuple[dict[str, Any] | None, bool]:
    ticket = _ticket_store.get(ticket_id)
    if not ticket:
        return None, False
    if time.time() > ticket["expires_at"]:
        _ticket_store.pop(ticket_id, None)
        return None, True
    return ticket, False

def create_rpc_router() -> APIRouter:
    """Cria router Sky-RPC."""
    router = APIRouter()
    registry = get_query_registry()
    skyrpc_registry = get_skyrpc_registry()

    def _auth_check(method: str, http_request: Request, correlation_id: str) -> tuple[str | None, JSONResponse | None]:
        security = get_security_config()
        client_host = http_request.client.host if http_request.client else ""
        client_id: str | None = None
        logger.debug(
            "Auth check iniciado",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "client_host": client_host,
            },
        )
        if security.ip_allowlist and client_host not in security.ip_allowlist:
            return None, _sky_rpc_error_response(
                code=4030,
                message="Forbidden",
                ticket_id=None,
                method=method,
                correlation_id=correlation_id,
            )

        if security.allow_localhost and _is_localhost(client_host):
            client_id = "localhost"
        else:
            auth_header = http_request.headers.get("authorization")
            if security.bearer_enabled and auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                client_id = security.bearer_tokens.get(token)
            if client_id is None:
                api_key = http_request.headers.get("x-api-key")
                if api_key:
                    if security.api_keys:
                        client_id = security.api_keys.get(api_key)
                    elif security.api_key and api_key == security.api_key:
                        client_id = "global"

        if client_id is None and not (security.allow_localhost and _is_localhost(client_host)):
            return None, _sky_rpc_error_response(
                code=4010,
                message="Unauthorized",
                ticket_id=None,
                method=method,
                correlation_id=correlation_id,
            )

        policy = security.method_policy.get(client_id or "", [])
        if method not in policy:
            return None, _sky_rpc_error_response(
                code=4030,
                message="Forbidden",
                ticket_id=None,
                method=method,
                correlation_id=correlation_id,
            )

        retry_after = _check_rate_limit(client_id or "", security.rate_limit_per_minute)
        if retry_after is not None:
            return None, _sky_rpc_error_response(
                code=4290,
                message="Rate limited",
                ticket_id=None,
                method=method,
                correlation_id=correlation_id,
                data={"retry_after": retry_after},
            )

        return client_id, None

    @router.get("/openapi")
    async def openapi_document(http_request: Request):
        """
        Retorna o documento OpenAPI Híbrido.

        Conforme ADR016:
        - Operações HTTP: estáticas (do YAML)
        - Schemas: dinâmicos (do registry runtime)
        """
        # Obtém o OpenAPI Híbrido gerado por app._custom_openapi()
        spec = http_request.app.openapi()
        # Converte para YAML
        yaml_content = yaml.dump(spec, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return Response(
            content=yaml_content,
            media_type="application/yaml; charset=utf-8",
        )

    @router.get("/privacy")
    async def privacy_policy():
        """Retorna política de privacidade."""
        return Response(
            content=_load_privacy_text(),
            media_type="text/plain; charset=utf-8",
        )

    @router.get("/health")
    async def health_check():
        """
        Health check endpoint.

        Retorna status simples da API sem requerer autenticação nem ticket.
        """
        registry = get_query_registry()
        handler = registry.get("health")

        if not handler:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "error": "Health handler not found"}
            )

        result = handler.handler()
        if result.is_ok:
            return JSONResponse(status_code=200, content=result.value)
        else:
            return JSONResponse(
                status_code=503,
                content={"status": "unavailable", "error": str(result.error)}
            )

    @router.get("/ticket")
    async def create_ticket(http_request: Request, method: str = Query(...)):
        """Cria ticket para execução Sky-RPC."""
        correlation_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))
        logger.debug("Recebido GET /ticket", extra={"correlation_id": correlation_id, "method": method, "client_host": http_request.client.host if http_request.client else ""})
        client_id, error = _auth_check(method, http_request, correlation_id)
        if error:
            return error

        ticket = _create_ticket(method, client_id or "")
        logger.debug("Ticket criado", extra={"correlation_id": correlation_id, "ticket_id": ticket["id"], "method": ticket["method"], "client_id": ticket["client_id"]})
        payload = {
            "ok": True,
            "ticket": {
                "id": ticket["id"],
                "method": ticket["method"],
                "expires_in": _TICKET_TTL_SECONDS,
                "accepts": "application/json",
            },
        }
        return JSONResponse(status_code=200, content=payload)

    @router.post("/envelope")
    async def submit_envelope(http_request: Request, payload: EnvelopeRequest = Body(...)):
        """Recebe envelope Sky-RPC."""
        correlation_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))
        logger.debug(
            "Recebido POST /envelope",
            extra={
                "correlation_id": correlation_id,
                "ticket_id": payload.ticket_id,
                "client_host": http_request.client.host if http_request.client else "",
            },
        )
        ticket, expired = _get_ticket(payload.ticket_id)
        if expired:
            logger.debug(
                "POST /envelope falhou por ticket expirado",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                },
            )
            return _sky_rpc_error_response(
                code=4100,
                message="Ticket expired",
                ticket_id=payload.ticket_id,
                method=None,
                correlation_id=correlation_id,
            )
        if ticket is None:
            logger.debug(
                "POST /envelope falhou por ticket inexistente",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                },
            )
            return _sky_rpc_error_response(
                code=4040,
                message="Ticket not found",
                ticket_id=payload.ticket_id,
                method=None,
                correlation_id=correlation_id,
            )

        method = ticket["method"]
        client_id, error = _auth_check(method, http_request, correlation_id)
        if error:
            logger.debug(
                "POST /envelope recusado no auth",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                    "method": method,
                },
            )
            return error
        if client_id and client_id != ticket["client_id"]:
            logger.debug(
                "POST /envelope recusado por client_id divergente",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                    "method": method,
                    "client_id": client_id,
                },
            )
            return _sky_rpc_error_response(
                code=4030,
                message="Forbidden",
                ticket_id=payload.ticket_id,
                method=method,
                correlation_id=correlation_id,
            )

        handler = registry.get(method)
        if not handler:
            logger.debug(
                "POST /envelope falhou por metodo desconhecido",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                    "method": method,
                },
            )
            return _sky_rpc_error_response(
                code=4220,
                message="Invalid method",
                ticket_id=payload.ticket_id,
                method=method,
                correlation_id=correlation_id,
            )

        # Parser v0.2: detail pode ser string ou objeto estruturado
        model_extra = payload.model_dump(exclude={"ticket_id", "detail"})
        flat_params, parse_error, detail_type = _parse_detail(payload.detail, model_extra)

        if parse_error:
            logger.debug(
                "POST /envelope falhou no parsing de detail",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                    "method": method,
                    "detail_type": detail_type,
                    "error": parse_error,
                },
            )
            # Verificar se é erro de payload vazio (4221)
            if "empty" in parse_error.lower() or "minproperties" in parse_error.lower():
                return _sky_rpc_error_response(
                    code=4221,
                    message="Payload cannot be empty (minProperties: 1)",
                    ticket_id=payload.ticket_id,
                    method=method,
                    correlation_id=correlation_id,
                )
            return _sky_rpc_error_response(
                code=4220,
                message=parse_error,
                ticket_id=payload.ticket_id,
                method=method,
                correlation_id=correlation_id,
            )

        # Log de observabilidade com detail_type e atributos do envelope
        logger.debug(
            "Envelope parsed",
            extra={
                "correlation_id": correlation_id,
                "ticket_id": payload.ticket_id,
                "method": method,
                "detail_type": detail_type,
                **_extract_envelope_attrs(detail_type, payload.detail, flat_params),
            },
        )

        # Se envelope estruturado, extrair contexto para logs
        context_log = {}
        if detail_type == "structured" and isinstance(payload.detail, EnvelopeDetail):
            context_log = {
                "context": payload.detail.context,
                "action": payload.detail.action,
                "subject": payload.detail.subject,
                "payload_keys": list(payload.detail.payload.keys()),
                "payload_size": len(payload.detail.payload),
            }

        args, error = _map_flat_details(handler, flat_params)
        if error:
            logger.debug(
                "POST /envelope falhou no mapeamento de detalhes",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                    "method": method,
                    "detail_type": detail_type,
                    "error": error,
                    **context_log,
                },
            )
            return _sky_rpc_error_response(
                code=4220,
                message=error,
                ticket_id=payload.ticket_id,
                method=method,
                correlation_id=correlation_id,
            )

        if args:
            result = handler.handler(args)
        else:
            result = handler.handler()
        _ticket_store.pop(payload.ticket_id, None)
        if result.is_ok:
            logger.debug(
                "POST /envelope executado com sucesso",
                extra={
                    "correlation_id": correlation_id,
                    "ticket_id": payload.ticket_id,
                    "method": method,
                    "client_id": client_id,
                    "detail_type": detail_type,
                    **context_log,
                },
            )
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "id": payload.ticket_id,
                    "result": result.value,
                },
            )
        logger.debug(
            "POST /envelope falhou no handler",
            extra={
                "correlation_id": correlation_id,
                "ticket_id": payload.ticket_id,
                "method": method,
                "detail_type": detail_type,
                "error": str(result.error),
                **context_log,
            },
        )
        return _sky_rpc_error_response(
            code=4220,
            message=str(result.error),
            ticket_id=payload.ticket_id,
            method=method,
            correlation_id=correlation_id,
        )

    # ========== Sky-RPC v0.3 Discovery Endpoints ==========

    @router.get("/discover", response_model=SkyRpcDiscovery)
    async def discover_handlers(http_request: Request):
        """
        Lista todos os handlers RPC ativos (introspecção).

        RF007: /discover retorna metadados de todos handlers (method, kind,
               module, auth_required, schemas).
        """
        correlation_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))
        logger.debug("GET /discover chamado", extra={"correlation_id": correlation_id})

        discovery = skyrpc_registry.get_discovery()
        return discovery

    @router.post("/discover/reload", response_model=ReloadResponse)
    async def reload_registry(
        http_request: Request,
        packages: list[str] = Body(..., description="Lista de pacotes para rediscover"),
    ):
        """
        Recarrega o registry com novo código (admin only).

        RF013: /discover/reload permite reload dinâmico de handlers.
        RF014: Rollback automático em caso de erro.
        """
        correlation_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))
        logger.debug(
            "POST /discover/reload chamado",
            extra={"correlation_id": correlation_id, "packages": packages},
        )

        security = get_security_config()
        client_host = http_request.client.host if http_request.client else ""

        # TODO: Adicionar verificação de admin token/scope
        # Por enquanto, apenas localhost pode fazer reload
        if not _is_localhost(client_host):
            logger.debug(
                "POST /discover/reload negado (não localhost)",
                extra={"correlation_id": correlation_id, "client_host": client_host},
            )
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "error": "Reload allowed from localhost only",
                },
            )

        try:
            result = skyrpc_registry.reload(packages, preserve_on_error=True)
            logger.debug(
                "Reload completado",
                extra={
                    "correlation_id": correlation_id,
                    "added": result.added,
                    "removed": result.removed,
                    "total": result.total,
                },
            )
            return result
        except RuntimeError as e:
            logger.debug(
                "Reload falhou",
                extra={"correlation_id": correlation_id, "error": str(e)},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False,
                    "error": str(e),
                },
            )

    @router.get("/discover/{method}", response_model=SkyRpcHandler)
    async def discover_handler(method: str, http_request: Request):
        """
        Retorna metadados de um handler específico.

        RF009: /discover/{method} retorna detalhes de um handler específico.
        """
        correlation_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))
        logger.debug(
            f"GET /discover/{method} chamado",
            extra={"correlation_id": correlation_id, "method": method},
        )

        handler = skyrpc_registry.get(method)
        if not handler:
            return JSONResponse(
                status_code=404,
                content={
                    "ok": False,
                    "error": f"Handler not found: {method}",
                },
            )

        return SkyRpcHandler(
            method=handler.name,
            kind=Kind(handler.kind) if isinstance(handler.kind, str) else Kind.QUERY,
            module=getattr(handler, "module", "unknown"),
            description=handler.description,
            auth_required=getattr(handler, "auth_required", True),
            input_schema=handler.input_schema,
            output_schema=handler.output_schema,
        )

    # ========== Metrics Endpoint (Observabilidade Nível 1) ==========

    @router.get("/metrics")
    async def queue_metrics():
        """
        Retorna métricas da fila para observabilidade.

        Endpoint público para monitoring e tomada de decisão sobre quando migrar para Redis.

        Métricas incluem:
        - queue_size: Tamanho atual da fila
        - enqueue_count: Total de jobs enfileirados
        - jobs_per_hour: Throughput médio (últimas 24h)
        - enqueue_latency_p95_ms: Latência p95 de enqueue
        - backlog_age_seconds: Idade do job mais antigo
        - disk_usage_mb: Uso de disco em MB
        """
        try:
            from core.webhooks.application.handlers import get_job_queue

            job_queue = get_job_queue()
            metrics = await job_queue.get_metrics()

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "metrics": metrics,
                    "queue_type": type(job_queue).__name__,
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to get metrics: {str(e)}",
                extra={"error": str(e)},
            )
            # Retorna métricas vazias em vez de 500 (demo-friendly)
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "metrics": {
                        "queue_size": 0,
                        "processing": 0,
                        "completed": 0,
                        "failed": 0,
                        "total_enqueued": 0,
                        "total_completed": 0,
                        "total_failed": 0,
                        "success_rate": 0.0,
                    },
                    "queue_type": "unknown",
                    "error": str(e),
                }
            )

    # ========== Webhook Endpoints (PRD013) ==========

    @router.head("/webhooks/{source}")
    @router.post("/webhooks/{source}")
    async def receive_webhook(source: str, http_request: Request):
        """
        Recebe webhook de fonte externa (GitHub, Discord, etc).

        PRD013: Endpoint para webhooks que acionam agentes autônomos.
        Fluxo: Verify signature → Parse event → Create job → Return 202
        """
        correlation_id = getattr(http_request.state, "correlation_id", str(uuid.uuid4()))

        # Extrai headers relevantes PRIMEIRO (antes de consumir body)
        signature = http_request.headers.get("x-hub-signature-256", "")
        event_type_header = http_request.headers.get("x-github-event", "")

        # Lê payload body (só pode ser lido uma vez)
        try:
            body_bytes = await http_request.body()
        except Exception as e:
            logger.error(
                f"Failed to read request body: {str(e)}",
                extra={"correlation_id": correlation_id, "source": source},
            )
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Failed to read body"},
            )

        # Verifica assinatura HMAC
        from runtime.delivery.middleware import verify_webhook_signature

        error_response = await verify_webhook_signature(body_bytes, signature, source)
        if error_response:
            return error_response

        # Parse payload JSON
        try:
            payload = __import__("json").loads(body_bytes.decode())
        except Exception as e:
            logger.error(
                f"Failed to parse webhook payload: {str(e)}",
                extra={"correlation_id": correlation_id, "source": source},
            )
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Invalid JSON payload"},
            )

        # Constrói event_type completo combinando header + action do payload
        # GitHub envia X-GitHub-Event como "issues" e payload tem "action": "opened"
        # Precisamos combinar para obter "issues.opened"
        if source == "github" and event_type_header in ("issues", "pull_request", "issue_comment", "discussion", "discussion_comment"):
            action = payload.get("action", "opened")
            event_type = f"{event_type_header}.{action}"
        else:
            # Para eventos sem action (ping, etc) ou outras fontes, usa o valor do header
            event_type = event_type_header

        # Busca handler registrado
        handler_name = f"webhooks.{source}.receive"
        handler = registry.get(handler_name)

        if not handler:
            logger.error(
                f"Handler not found: {handler_name}",
                extra={"correlation_id": correlation_id, "source": source},
            )
            return JSONResponse(
                status_code=501,
                content={"ok": False, "error": "Handler not implemented"},
            )

        # Executa handler
        try:
            result = handler.handler({
                "payload": payload,
                "signature": signature,
                "event_type": event_type,
            })
        except Exception as e:
            logger.error(
                f"Handler execution failed: {str(e)}",
                extra={"correlation_id": correlation_id, "source": source, "handler": handler_name},
            )
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": "Handler execution failed"},
            )

        if result.is_ok:
            # Trata ping como caso especial (200 OK)
            if result.value == "ping":
                logger.info(
                    f"Ping event acknowledged",
                    extra={"correlation_id": correlation_id, "source": source},
                )
                return JSONResponse(
                    status_code=200,  # OK
                    content={"ok": True, "message": "pong"},
                )

            logger.info(
                f"Webhook enqueued successfully",
                extra={
                    "correlation_id": correlation_id,
                    "source": source,
                    "event_type": event_type,
                    "job_id": result.value,
                },
            )
            return JSONResponse(
                status_code=202,  # Accepted
                content={
                    "ok": True,
                    "job_id": result.value,
                    "status": "queued",
                },
            )
        else:
            logger.error(
                f"Handler returned error: {result.error}",
                extra={"correlation_id": correlation_id, "source": source},
            )
            return JSONResponse(
                status_code=422,
                content={"ok": False, "error": result.error},
            )

    return router
