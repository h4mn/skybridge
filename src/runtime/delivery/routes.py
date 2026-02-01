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

    # ========== WebUI Endpoints (PRD014) ==========

    @router.get("/webhooks/jobs")
    async def list_webhook_jobs(
        limit: int = Query(100, ge=1, le=1000, description="Número máximo de jobs a retornar"),
        status: str | None = Query(None, description="Filtrar por status"),
    ):
        """
        Lista todos os jobs de webhook para o WebUI.

        PRD014: Endpoint para o Dashboard listar jobs.
        """
        try:
            from core.webhooks.application.handlers import get_job_queue

            job_queue = get_job_queue()

            # Tenta obter métricas da fila
            metrics = {}
            if hasattr(job_queue, 'get_metrics'):
                metrics = await job_queue.get_metrics()

            # Lista os jobs usando o novo método list_jobs
            jobs = []
            if hasattr(job_queue, 'list_jobs'):
                jobs = await job_queue.list_jobs(limit=limit, status_filter=status)

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "jobs": jobs,
                    "metrics": metrics,
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to list jobs: {str(e)}",
                extra={"error": str(e)},
            )
            return JSONResponse(
                status_code=200,
                content={"ok": True, "jobs": [], "metrics": {}},
            )

    @router.get("/webhooks/worktrees")
    async def list_worktrees(request):
        """
        Lista todos os worktrees ativos para o WebUI.

        PRD014: Endpoint para o Dashboard listar worktrees.
        DOC: ADR024 - Lista worktrees do workspace ativo (X-Workspace header).
        """
        try:
            from pathlib import Path
            from runtime.config.config import get_workspace_queue_dir
            import json

            # ADR024: Usa worktrees do workspace atual
            # Worktrees ficam em workspace/{workspace_id}/worktrees/
            workspace_id = getattr(request.state, 'workspace', 'core')
            worktrees_path = Path.cwd() / "workspace" / workspace_id / "worktrees"

            worktrees = []
            if worktrees_path.exists():
                for item in worktrees_path.iterdir():
                    if item.is_dir() and item.name.startswith("skybridge-github-"):
                        # Lê snapshot se existir
                        snapshot_path = item / ".sky" / "snapshot.json"
                        snapshot = None
                        if snapshot_path.exists():
                            try:
                                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
                            except Exception:
                                pass

                        # Determina status baseado no snapshot
                        status = "UNKNOWN"
                        if snapshot:
                            status = snapshot.get("status", "UNKNOWN").upper()

                        worktrees.append({
                            "name": item.name,
                            "path": str(item),
                            "status": status,
                            "snapshot": snapshot,
                        })

            return JSONResponse(
                status_code=200,
                content={"ok": True, "worktrees": worktrees},
            )
        except Exception as e:
            logger.error(
                f"Failed to list worktrees: {str(e)}",
                extra={"error": str(e)},
            )
            return JSONResponse(
                status_code=200,
                content={"ok": True, "worktrees": []},
            )

    @router.get("/webhooks/worktrees/{worktree_name}")
    async def get_worktree_details(worktree_name: str, request):
        """
        Retorna detalhes completos de um worktree para o WebUI.

        PRD014: Endpoint para o modal de detalhes do worktree.
        DOC: ADR024 - Retorna worktree do workspace ativo (X-Workspace header).
        """
        try:
            from pathlib import Path
            import json

            # ADR024: Usa worktrees do workspace atual
            workspace_id = getattr(request.state, 'workspace', 'core')
            worktree_path = Path.cwd() / "workspace" / workspace_id / "worktrees" / worktree_name

            if not worktree_path.exists():
                return JSONResponse(
                    status_code=404,
                    content={"ok": False, "error": f"Worktree not found: {worktree_name}"},
                )

            # Lê agent log
            agent_log_path = worktree_path / ".sky" / "agent.log"
            agent_log = None
            if agent_log_path.exists():
                try:
                    agent_log = agent_log_path.read_text(encoding="utf-8")
                except Exception:
                    pass

            # Lê snapshot
            snapshot_path = worktree_path / ".sky" / "snapshot.json"
            snapshot = None
            if snapshot_path.exists():
                try:
                    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
                except Exception:
                    pass

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "name": worktree_name,
                    "path": str(worktree_path),
                    "agent_log": agent_log,
                    "snapshot": snapshot,
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to get worktree details: {str(e)}",
                extra={"error": str(e), "worktree": worktree_name},
            )
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)},
            )

    @router.delete("/webhooks/worktrees/{worktree_name}")
    async def delete_worktree(worktree_name: str, password: str | None = None, request=None):
        """
        Remove um worktree para o WebUI.

        PRD014: Endpoint para limpar worktrees do Dashboard com proteções de segurança.
        DOC: ADR024 - Remove worktree do workspace ativo (X-Workspace header).

        Segurança:
        - Requer senha configurada em WEBUI_DELETE_PASSWORD
        - Só permite deletar worktrees com status COMPLETED ou FAILED
        - Registra log de auditoria
        """
        try:
            from pathlib import Path
            from runtime.config.config import get_webhook_config
            import json
            from datetime import datetime

            config = get_webhook_config()

            # 1. Verifica se senha está configurada
            if not config.delete_password:
                return JSONResponse(
                    status_code=403,
                    content={"ok": False, "error": "Delete password not configured. Set WEBUI_DELETE_PASSWORD env var."},
                )

            # 2. Valida senha
            if password != config.delete_password:
                logger.warning(
                    f"Failed delete attempt for worktree {worktree_name}: invalid password",
                    extra={"worktree": worktree_name},
                )
                return JSONResponse(
                    status_code=401,
                    content={"ok": False, "error": "Invalid password"},
                )

            # ADR024: Usa worktrees do workspace atual
            workspace_id = getattr(request.state, 'workspace', 'core') if request else 'core'
            worktree_path = Path.cwd() / "workspace" / workspace_id / "worktrees" / worktree_name

            if not worktree_path.exists():
                return JSONResponse(
                    status_code=404,
                    content={"ok": False, "error": f"Worktree not found: {worktree_name}"},
                )

            # 3. Lê status atual do snapshot
            snapshot_path = worktree_path / ".sky" / "snapshot.json"
            status = "UNKNOWN"
            if snapshot_path.exists():
                try:
                    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
                    status = snapshot.get("status", "UNKNOWN").upper()
                except Exception:
                    pass

            # 4. Só permite deletar COMPLETED ou FAILED
            if status not in ("COMPLETED", "FAILED"):
                logger.warning(
                    f"Delete attempt denied for worktree {worktree_name}: status is {status}",
                    extra={"worktree": worktree_name, "status": status},
                )
                return JSONResponse(
                    status_code=409,  # Conflict
                    content={
                        "ok": False,
                        "error": f"Cannot delete worktree with status '{status}'. Only COMPLETED or FAILED can be deleted.",
                        "status": status
                    },
                )

            # 5. Log de auditoria
            logger.info(
                f"Deleting worktree {worktree_name} with status {status}",
                extra={"worktree": worktree_name, "status": status, "timestamp": datetime.utcnow().isoformat()},
            )

            # 6. Remove worktree usando git worktree remove
            import subprocess
            result = subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": result.stderr},
                )

            return JSONResponse(
                status_code=200,
                content={"ok": True, "message": f"Worktree {worktree_name} removed"},
            )
        except Exception as e:
            logger.error(
                f"Failed to delete worktree: {str(e)}",
                extra={"error": str(e), "worktree": worktree_name},
            )
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)},
            )

    @router.get("/observability/logs")
    async def get_logs(tail: int = 100, level: str | None = None):
        """
        Retorna logs recentes para o WebUI.

        PRD014: Endpoint para busca histórica de logs.
        """
        try:
            from pathlib import Path
            from datetime import datetime

            from runtime.config.config import get_workspace_logs_dir
            log_file = get_workspace_logs_dir() / f"{datetime.now():%Y-%m-%d}.log"

            if not log_file.exists():
                return JSONResponse(status_code=200, content={"ok": True, "lines": []})

            lines = log_file.read_text(encoding="utf-8").splitlines()

            # Filtra por nível se especificado
            if level:
                lines = [l for l in lines if f"[{level.upper()}]" in l]

            return JSONResponse(
                status_code=200,
                content={"ok": True, "lines": lines[-tail:]},
            )
        except Exception as e:
            logger.error(
                f"Failed to get logs: {str(e)}",
                extra={"error": str(e)},
            )
            return JSONResponse(
                status_code=200,
                content={"ok": True, "lines": []},
            )

    @router.get("/observability/logs/stream")
    async def stream_logs():
        """
        Stream logs em tempo real via SSE para o WebUI.

        PRD014: Endpoint SSE para streaming de logs.
        """
        from fastapi.responses import StreamingResponse
        import asyncio

        async def log_generator():
            """Gerador que lê novas linhas do log."""
            from pathlib import Path
            from datetime import datetime

            from runtime.config.config import get_workspace_logs_dir
            log_file = get_workspace_logs_dir() / f"{datetime.now():%Y-%m-%d}.log"
            last_position = 0

            if log_file.exists():
                last_position = log_file.stat().st_size

            while True:
                if log_file.exists():
                    current_size = log_file.stat().st_size

                    if current_size > last_position:
                        # Lê novas linhas
                        with open(log_file, "rb") as f:
                            f.seek(last_position)
                            new_lines = f.read().decode("utf-8")

                        for line in new_lines.splitlines():
                            if line.strip():
                                yield f"data: {line}\n\n"

                        last_position = current_size

                await asyncio.sleep(0.5)  # Poll a cada 500ms

        return StreamingResponse(log_generator(), media_type="text/event-stream")

    @router.get("/observability/events/stream")
    async def stream_events(workspace: str | None = Query(None, description="Workspace ID (query parameter para SSE)")):
        """
        Stream eventos de domínio em tempo real via SSE para o WebUI.

        PRD014: Endpoint SSE para streaming de eventos do EventBus.
        Permite monitorar JobStartedEvent, JobCompletedEvent, etc.
        DOC: ADR024 - Aceita workspace via query parameter (EventSource não suporta headers).

        NOTA: Cria InMemoryEventBus local se global não disponível,
        pois o worker roda em thread separada.
        """
        from fastapi.responses import StreamingResponse
        import asyncio
        import json
        from runtime.workspace.workspace_context import set_current_workspace

        # Define workspace do contexto baseado no query parameter
        # (EventSource não suporta headers, então usamos query param)
        if workspace:
            set_current_workspace(workspace)

        async def event_generator():
            """Gerador que entrega novos eventos do EventBus."""
            from infra.domain_events.in_memory_event_bus import InMemoryEventBus
            from core.domain_events.domain_event import DomainEvent
            from kernel import get_event_bus, clear_event_bus, set_event_bus

            logger.info(f"[SSE] Cliente conectado ao stream de eventos (workspace={workspace or 'default'})")

            # Tenta obter EventBus global, mas cria local se necessário
            # (o worker roda em thread separada e pode não estar disponível)
            try:
                event_bus = get_event_bus()
                logger.info(f"[SSE] EventBus global obtido: {type(event_bus).__name__}")
            except RuntimeError:
                logger.info("[SSE] EventBus global não disponível, criando localmente")
                event_bus = InMemoryEventBus()
                set_event_bus(event_bus)

            if not isinstance(event_bus, InMemoryEventBus):
                # Cria EventBus local se o global não for InMemoryEventBus
                logger.warning(f"[SSE] EventBus não é InMemoryEventBus: {type(event_bus)}, criando local")
                event_bus = InMemoryEventBus()
                set_event_bus(event_bus)

            # Envia histórico inicial
            history = event_bus.get_history(limit=50)
            logger.info(f"[SSE] Enviando histórico: {len(history)} eventos")
            for event_dict in history:
                yield f"event: history\ndata: {json.dumps(event_dict)}\n\n"

            # Contador para novos eventos
            last_count = len(event_bus.get_history())
            logger.info(f"[SSE] Histórico enviado, last_count={last_count}")

            # Poll por novos eventos
            iteration = 0
            while True:
                current_history = event_bus.get_history()
                current_count = len(current_history)

                # Se houver novos eventos, envia
                if current_count > last_count:
                    new_events = current_history[:current_count - last_count]
                    logger.info(f"[SSE] Enviando {len(new_events)} novos eventos (iteração {iteration})")
                    for event_dict in new_events:
                        logger.debug(f"[SSE] Evento: {event_dict.get('event_type')}")
                        yield f"event: domain_event\ndata: {json.dumps(event_dict)}\n\n"
                    last_count = current_count

                iteration += 1
                await asyncio.sleep(0.5)  # Poll a cada 500ms

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.post("/observability/events/generate-fake")
    async def generate_fake_events(count: int = 10):
        """
        Gera eventos fake de domínio para testes do WebUI.

        Útil para testar a interface de eventos sem processar jobs reais.
        """
        try:
            from kernel import get_event_bus
            from core.domain_events.job_events import (
                JobCreatedEvent,
                JobStartedEvent,
                JobCompletedEvent,
                JobFailedEvent,
            )

            event_bus = get_event_bus()

            # Gera eventos fake variados
            fake_events = []

            # JobCreatedEvent
            for i in range(count):
                job_id = f"fake-job-{i}"
                fake_events.append(JobCreatedEvent(
                    job_id=job_id,
                    issue_number=100 + i,
                    repository="h4mn/skybridge",
                    worktree_path=f"/fake/worktree-{i}",
                ))

                # JobStartedEvent
                fake_events.append(JobStartedEvent(
                    job_id=job_id,
                    issue_number=100 + i,
                    repository="h4mn/skybridge",
                    agent_type="claude-sdk",
                ))

                # JobCompletedEvent ou JobFailedEvent (alternado)
                if i % 3 == 0:
                    fake_events.append(JobCompletedEvent(
                        job_id=job_id,
                        issue_number=100 + i,
                        repository="h4mn/skybridge",
                        worktree_path=f"/fake/worktree-{i}",
                        files_modified=i + 1,
                        duration_seconds=30.0 + i,
                    ))
                else:
                    fake_events.append(JobFailedEvent(
                        job_id=job_id,
                        issue_number=100 + i,
                        repository="h4mn/skybridge",
                        error_message="Fake error for testing",
                        error_type="FakeError",
                        duration_seconds=15.0,
                        retry_count=0,
                    ))

            # Publica todos os eventos
            for event in fake_events:
                await event_bus.publish(event)

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "message": f"Generated {len(fake_events)} fake events",
                    "count": len(fake_events),
                }
            )
        except Exception as e:
            logger.error(f"Erro ao gerar eventos fake: {e}")
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)}
            )

    @router.post("/observability/github/create-issue")
    async def create_github_issue(request: Request):
        """
        Cria uma nova issue no GitHub.

        Endpoint simples para criar issues diretamente via API REST.
        Útil para CLI ou automações.

        Body:
            title: Título da issue
            body: Corpo/descrição da issue
            labels: Labels (opcional, default=["automated"])
        """
        from fastapi import Request
        import os

        try:
            # Parse body
            body_data = await request.json()
            title = body_data.get("title")
            desc = body_data.get("body", "")
            labels = body_data.get("labels", ["automated"])

            if not title:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "error": "title is required"}
                )

            # Importa cliente GitHub
            from infra.github.github_api_client import create_github_client

            token = os.getenv("GITHUB_TOKEN")
            if not token:
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": "GITHUB_TOKEN not configured"}
                )

            repo = os.getenv("GITHUB_REPO", "h4mn/skybridge")

            # Cria cliente e issue
            client = create_github_client(token=token)
            result = await client.create_issue(
                repo=repo,
                title=title,
                body=desc,
                labels=labels
            )
            await client.close()

            if result.is_err:
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": result.error}
                )

            issue_data = result.value
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "issue_number": issue_data.get("issue_number"),
                    "issue_url": issue_data.get("issue_url"),
                    "labels": issue_data.get("labels", []),
                }
            )

        except Exception as e:
            logger.error(f"Erro ao criar issue: {e}")
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)}
            )

    @router.delete("/observability/events/history")
    async def clear_events_history():
        """
        Limpa o histórico de eventos do EventBus.

        Útil para limpar a tela de eventos e começar a monitorar do zero.
        """
        try:
            from kernel import get_event_bus

            event_bus = get_event_bus()
            previous_count = len(event_bus.get_history())

            # Limpa o histórico
            if hasattr(event_bus, 'clear_history'):
                event_bus.clear_history()
            else:
                # Fallback para InMemoryEventBus
                from infra.domain_events.in_memory_event_bus import InMemoryEventBus
                if isinstance(event_bus, InMemoryEventBus):
                    event_bus._history.clear()

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "message": f"Cleared {previous_count} events from history",
                    "previous_count": previous_count,
                }
            )
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)}
            )

    # ========== Log File Endpoints for Logs.tsx ==========

    @router.get("/logs/files")
    async def list_log_files():
        """
        Lista todos os arquivos de log disponíveis para o WebUI.

        PRD014: Endpoint para a página de Logs listar arquivos.
        """
        try:
            from pathlib import Path

            from runtime.config.config import get_workspace_logs_dir
            logs_dir = get_workspace_logs_dir()

            if not logs_dir.exists():
                return JSONResponse(
                    status_code=200,
                    content={"ok": True, "files": []}
                )

            files = []
            for log_file in sorted(logs_dir.glob("*.log"), reverse=True):
                stat = log_file.stat()
                # Converte timestamp Unix (segundos) para ISO string
                from datetime import datetime
                modified_dt = datetime.fromtimestamp(stat.st_mtime)
                files.append({
                    "name": log_file.name,
                    "size": stat.st_size,
                    "modified": modified_dt.isoformat()
                })

            return JSONResponse(
                status_code=200,
                content={"ok": True, "files": files}
            )
        except Exception as e:
            logger.error(
                f"Failed to list log files: {str(e)}",
                extra={"error": str(e)},
            )
            return JSONResponse(
                status_code=200,
                content={"ok": True, "files": []},
            )

    @router.get("/logs/file/{filename}")
    async def get_log_file(
        filename: str,
        page: int = Query(1, ge=1, description="Número da página"),
        per_page: int = Query(500, ge=1, le=50000, description="Itens por página"),
        level: str | None = Query(None, description="Filtrar por nível (DEBUG/INFO/WARNING/ERROR/CRITICAL)"),
        search: str | None = Query(None, description="Buscar termo nos logs")
    ):
        """
        Retorna entradas de log de um arquivo específico com paginação e filtros.

        PRD014: Endpoint para a página de Logs exibir entradas.

        Logs são retornados em ordem reversa (mais recentes primeiro).
        Mensagens com códigos ANSI são convertidas para HTML.
        """
        try:
            from pathlib import Path
            from datetime import datetime
            from runtime.delivery.log_utils import parse_log_line, strip_ansi_codes

            from runtime.config.config import get_workspace_logs_dir
            logs_dir = get_workspace_logs_dir()
            log_file = logs_dir / filename

            # Verifica se o arquivo está dentro do diretório de logs (segurança)
            if not str(log_file.resolve()).startswith(str(logs_dir.resolve())):
                return JSONResponse(
                    status_code=403,
                    content={"ok": False, "error": "Acesso negado"}
                )

            if not log_file.exists():
                return JSONResponse(
                    status_code=404,
                    content={"ok": False, "error": f"Arquivo não encontrado: {filename}"}
                )

            # Lê todas as linhas do arquivo
            lines = log_file.read_text(encoding="utf-8").splitlines()

            # Parse cada linha usando o utilitário
            entries = []
            for line in lines:
                parsed = parse_log_line(line)
                if parsed:
                    entries.append(parsed)

            # Inverte ordem: mais recentes primeiro
            entries.reverse()

            # Aplica filtros (busca em mensagem sem ANSI)
            if level:
                entries = [e for e in entries if e["level"].upper() == level.upper()]

            if search:
                search_lower = search.lower()
                entries = [
                    e for e in entries
                    if search_lower in strip_ansi_codes(e["message"]).lower()
                    or search_lower in e["logger"].lower()
                ]

            # Paginação
            total = len(entries)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_entries = entries[start_idx:end_idx]

            # Retorna entradas com message_html para renderização
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "entries": paginated_entries,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total + per_page - 1) // per_page
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to get log file: {str(e)}",
                extra={"error": str(e), "filename": filename},
            )
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)},
            )

    # ========== Webhook Endpoints (PRD013) ==========

    # TODO(REMOVE): Remover rota de fallback após 03/02/2026
    # Rota temporária para compatibilidade com webhooks configurados sem /api
    # Algumas instalações antigas têm webhooks apontando para /webhooks/{source}
    # em vez de /api/webhooks/{source}. Esta rota processa essas requisições.
    @router.head("/webhooks/{source}")
    @router.post("/webhooks/{source}")
    async def receive_webhook_fallback(source: str, http_request: Request):
        """
        Rota de fallback para webhooks sem prefixo /api.

        ATENÇÃO: Esta rota é temporária e deve ser removida após 03/02/2026.
        Webhooks devem ser configurados com /api/webhooks/{source}.
        """
        # Log de aviso para monitorar uso da URL antiga
        logger.warning(
            f"Webhook recebido em URL sem /api: /webhooks/{source} - "
            f"Por favor atualize a configuração do webhook para /api/webhooks/{source}"
        )

        # Processa normalmente delegando para o handler principal
        return await receive_webhook(source, http_request)

    @router.head("/api/webhooks/{source}")
    @router.post("/api/webhooks/{source}")
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

    # ========== Agents Endpoints (Página de Agents) ==========

    @router.get("/agents/executions")
    async def list_agent_executions(
        limit: int = Query(100, ge=1, le=1000, description="Número máximo de execuções a retornar"),
    ):
        """
        Lista todas as execuções de agentes para o WebUI.

        PRD: Página de Agents (Agent Spawns)
        """
        try:
            from core.webhooks.application.handlers import get_agent_execution_store

            store = get_agent_execution_store()
            executions = store.list_all(limit=limit)
            metrics = store.get_metrics()

            # Converte para dict
            executions_data = [exec.to_dict() for exec in executions]

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "executions": executions_data,
                    "metrics": metrics,
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to list agent executions: {str(e)}",
                extra={"error": str(e)},
            )
            return JSONResponse(
                status_code=200,
                content={"ok": True, "executions": [], "metrics": {}},
            )

    @router.get("/agents/executions/{job_id}")
    async def get_agent_execution(job_id: str):
        """
        Retorna detalhes de uma execução de agente.

        PRD: Página de Agents (Agent Spawns)
        """
        try:
            from core.webhooks.application.handlers import get_agent_execution_store

            store = get_agent_execution_store()
            execution = store.get(job_id)

            if execution is None:
                return JSONResponse(
                    status_code=404,
                    content={"ok": False, "error": f"Execution not found: {job_id}"},
                )

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "execution": execution.to_dict(),
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to get agent execution: {str(e)}",
                extra={"error": str(e), "job_id": job_id},
            )
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)},
            )

    @router.get("/agents/executions/{job_id}/messages")
    async def get_agent_execution_messages(job_id: str):
        """
        Retorna mensagens capturadas do stream de uma execução.

        PRD: Página de Agents (Agent Spawns)
        Por enquanto retorna stdout completo.
        """
        try:
            from core.webhooks.application.handlers import get_agent_execution_store

            store = get_agent_execution_store()
            execution = store.get(job_id)

            if execution is None:
                return JSONResponse(
                    status_code=404,
                    content={"ok": False, "error": f"Execution not found: {job_id}"},
                )

            # Por enquanto, retorna stdout como lista de linhas
            # Futuro: extrair mensagens estruturadas do stream
            messages = execution.stdout.splitlines() if execution.stdout else []

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "job_id": job_id,
                    "messages": messages,
                    "stdout": execution.stdout,
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to get agent execution messages: {str(e)}",
                extra={"error": str(e), "job_id": job_id},
            )
            return JSONResponse(
                status_code=500,
                content={"ok": False, "error": str(e)},
            )

    @router.get("/agents/metrics")
    async def get_agent_metrics():
        """
        Retorna métricas de execuções de agentes.

        PRD: Página de Agents (Agent Spawns)
        """
        try:
            from core.webhooks.application.handlers import get_agent_execution_store

            store = get_agent_execution_store()
            metrics = store.get_metrics()

            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "metrics": metrics,
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to get agent metrics: {str(e)}",
                extra={"error": str(e)},
            )
            return JSONResponse(
                status_code=200,
                content={"ok": True, "metrics": {}},
            )

    return router
