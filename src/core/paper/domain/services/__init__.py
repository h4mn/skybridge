"""
Serviços de Domínio - Paper Trading

Serviços de domínio encapsulam regras de negócio puras
que não pertencem a nenhuma entidade específica.

Serviços implementados:
- ValidadorDeOrdem: Valida regras para criação de ordens

Serviços planejados:
- ExecutorDeOrdem: Executa ordens contra o mercado
- CalculadorDeRisco: Calcula risco total do portfolio
- GeradorDeRelatorio: Gera relatórios de performance

Exemplo:
    validador = ValidadorDeOrdem(...)
    try:
        evento = await validador.validar_e_criar_ordem(
            ticker="PETR4.SA",
            lado=Lado.COMPRA,
            quantidade=100
        )
    except ValidacaoError as e:
        print(f"Ordem rejeitada: {e.motivo}")
"""

from .validador_ordem import (
    ValidadorDeOrdem,
    ValidacaoError,
    MotivoRejeicao,
)

__all__ = [
    "ValidadorDeOrdem",
    "ValidacaoError",
    "MotivoRejeicao",
]
