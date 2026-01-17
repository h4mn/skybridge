# -*- coding: utf-8 -*-
"""
Health Query — Query para verificar o status da API.

Endpoint simples para validar que o sistema está funcionando.
"""

from datetime import datetime
from typing import TypedDict

from kernel import Result
from kernel.registry.decorators import query


class HealthData(TypedDict):
    """Dados de resposta do health check."""
    status: str
    version: str
    timestamp: str
    service: str


@query(
    name="health",
    description="Health check endpoint",
    tags=["system"],
    output_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "version": {"type": "string"},
            "timestamp": {"type": "string"},
            "service": {"type": "string"},
        },
    },
)
def health_query() -> Result[HealthData, str]:
    """
    Query handler para health check.

    Returns:
        Result com dados de saúde do sistema.
    """
    try:
        return Result.ok({
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": "Skybridge API",
        })
    except Exception as e:
        return Result.err(f"Health check failed: {str(e)}")
