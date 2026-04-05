# -*- coding: utf-8 -*-
"""Handler para processar ConsultarOrdensQuery."""

from ..queries.consultar_ordens import ConsultarOrdensQuery, OrdensResult, OrdemItem
from ...ports.broker_port import BrokerPort
from ...ports.paper_state_port import PaperStatePort


class ConsultarOrdensHandler:
    """Handler para consultas de ordens.

    Lista ordens do portfolio com filtros opcionais.
    """

    def __init__(self, broker: BrokerPort, paper_state: PaperStatePort):
        self._broker = broker
        self._paper_state = paper_state

    async def handle(self, query: ConsultarOrdensQuery) -> OrdensResult:
        """Processa a query de ordens.

        Args:
            query: Query com filtros opcionais

        Returns:
            OrdensResult com lista de ordens filtradas
        """
        # Carrega ordens do estado
        estado = self._paper_state.carregar()
        ordens = estado.ordens

        # Aplica filtros
        ordens_filtradas = []
        for ordem_id, ordem in ordens.items():
            # Filtro por ticker
            if query.ticker and ordem.get("ticker") != query.ticker:
                continue
            # Filtro por lado
            if query.lado and ordem.get("lado") != query.lado:
                continue
            # Filtro por status
            if query.status and ordem.get("status") != query.status:
                continue

            ordens_filtradas.append(OrdemItem(
                id=ordem.get("id", ordem_id),
                ticker=ordem.get("ticker", ""),
                lado=ordem.get("lado", ""),
                quantidade=ordem.get("quantidade", 0),
                preco_execucao=ordem.get("preco_execucao", 0.0),
                valor_total=ordem.get("valor_total", 0.0),
                status=ordem.get("status", ""),
                timestamp=ordem.get("timestamp", ""),
            ))

        # Ordena por timestamp (mais recentes primeiro)
        ordens_filtradas.sort(key=lambda o: o.timestamp, reverse=True)

        # Aplica limite
        if query.limite:
            ordens_filtradas = ordens_filtradas[:query.limite]

        return OrdensResult(
            ordens=ordens_filtradas,
            total=len(ordens_filtradas),
        )
