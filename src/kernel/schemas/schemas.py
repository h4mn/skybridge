# -*- coding: utf-8 -*-
"""
Schemas Pydantic para Sky-RPC v0.3

Baseado em SPEC004 e docs/spec/contexts/common.yaml
"""

from typing import Any, Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


class Kind(str, Enum):
    """Tipo de operação RPC."""
    QUERY = "query"
    COMMAND = "command"


class EnvelopeDetailString(str):
    """Formato legado de detalhe (v0.1/v0.2) - string simples."""
    pass


class EnvelopeDetailStruct(BaseModel):
    """Formato estruturado de detalhes (v0.3)."""
    context: str = Field(..., description="Contexto do domínio (ex: fileops, tasks)")
    action: str = Field(..., description="Ação a ser executada")
    subject: Optional[str] = Field(None, description="Sujeito da operação (contexto-dependente)")
    scope: Optional[str] = Field(None, description="Escopo da operação (ex: tenant:sky)")
    options: Optional[dict[str, Any]] = Field(default_factory=dict, description="Opções específicas")
    payload: Optional[dict[str, Any]] = Field(None, description="Payload adicional (opcional em v0.3)")

    @field_validator('context')
    @classmethod
    def context_must_not_have_underscore(cls, v: str) -> str:
        if '_' in v:
            raise ValueError("Context must use dots (context.action), not underscores")
        return v


class EnvelopeRequest(BaseModel):
    """Envelope de requisição Sky-RPC v0.3."""
    ticket_id: str = Field(..., description="UUID do ticket obtido via GET /ticket")
    detail: Union[EnvelopeDetailStruct, EnvelopeDetailStruct]

    @field_validator('ticket_id')
    @classmethod
    def validate_ticket_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("ticket_id must be a valid UUID")
        return v


class Error(BaseModel):
    """Erro padrão Sky-RPC."""
    code: int = Field(..., description="Código do erro (Sky-RPC ou HTTP)")
    message: str = Field(..., description="Mensagem de erro legível")
    details: Optional[dict[str, Any]] = Field(None, description="Detalhes adicionais")


class EnvelopeResponse(BaseModel):
    """Resposta padrão de envelope Sky-RPC."""
    ok: bool = Field(..., description="Indica se a operação foi bem-sucedida")
    id: str = Field(..., description="UUID correlacionado com a requisição")
    result: Optional[dict[str, Any]] = Field(None, description="Resultado da operação (presente quando ok=true)")
    error: Optional[Error] = Field(None, description="Erro (presente quando ok=False)")


class TicketResponse(BaseModel):
    """Resposta de criação de ticket."""
    ok: bool
    ticket: Optional["Ticket"] = None


class Ticket(BaseModel):
    """Ticket de execução."""
    id: str = Field(..., description="UUID do ticket")
    method: str = Field(..., description="Método solicitado")
    expires_in: int = Field(..., description="Tempo até expiração (segundos)")
    accepts: str = Field("application/json", description="Content-Type aceito")


class SkyRpcHandler(BaseModel):
    """Metadados de um handler RPC."""
    method: str = Field(..., description="Nome canônico (ex: fileops.read)")
    kind: Kind = Field(..., description="Tipo de operação")
    module: str = Field(..., description="Caminho do módulo Python")
    description: Optional[str] = Field(None, description="Descrição do handler")
    auth_required: bool = Field(True, description="Se requer autenticação")
    input_schema: Optional[dict[str, Any]] = Field(None, description="JSON Schema do input")
    output_schema: Optional[dict[str, Any]] = Field(None, description="JSON Schema do output")


class SkyRpcDiscovery(BaseModel):
    """Resposta de descoberta de handlers."""
    version: str = Field("0.3.0", description="Versão do Sky-RPC")
    discovery: dict[str, SkyRpcHandler] = Field(default_factory=dict, description="Mapa de handlers")
    total: Optional[int] = Field(None, description="Total de handlers ativos")

    @field_validator('total', mode='before')
    @classmethod
    def calculate_total(cls, v: Optional[int], info: Any) -> int:
        if v is None:
            return len(info.data.get('discovery', {}))
        return v


class ReloadResponse(BaseModel):
    """Resposta de reload do registry."""
    ok: bool
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    total: int
    version: str = "0.3.0"


class HealthStatus(str, Enum):
    """Status de saúde."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class CheckStatus(str, Enum):
    """Status de um check."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class HealthCheck(BaseModel):
    """Um check específico."""
    status: CheckStatus
    description: Optional[str] = None
    observed_value: Optional[str] = None
    observed_unit: Optional[str] = None


class HealthResponse(BaseModel):
    """Resposta de health check."""
    status: HealthStatus
    version: Optional[str] = None
    uptime: Optional[float] = None
    checks: Optional[dict[str, HealthCheck]] = None
