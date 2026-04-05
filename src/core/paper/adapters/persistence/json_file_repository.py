# -*- coding: utf-8 -*-
"""Adapter - Repositório JSON para persistência delegada ao PaperStatePort."""

from datetime import datetime
from typing import Dict, Optional

from ...ports.repository_port import PortfolioRepositoryPort
from ...ports.paper_state_port import PaperStatePort
from ...domain.entities.portfolio import Portfolio


class JsonFilePortfolioRepository(PortfolioRepositoryPort):
    """Repositório com persistência delegada ao PaperStatePort.

    Esta versão NÃO escreve diretamente no arquivo JSON.
    Toda persistência é delegada ao PaperStatePort injetado.

    Isso resolve o conflito de múltiplos writers no paper_state.json.
    """

    def __init__(self, paper_state: PaperStatePort):
        self._paper_state = paper_state
        self._portfolios: Dict[str, Portfolio] = {}
        self._default_id: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Carrega portfolios do PaperStatePort."""
        estado = self._paper_state.carregar()

        for pid, pdata in estado.portfolios.items():
            self._portfolios[pid] = Portfolio(
                id=pdata["id"],
                nome=pdata["nome"],
                saldo_inicial=pdata["saldo_inicial"],
                saldo_atual=pdata["saldo_atual"],
                criado_em=datetime.fromisoformat(pdata["criado_em"]),
            )

        self._default_id = estado.default_id
        if not self._default_id and self._portfolios:
            self._default_id = next(iter(self._portfolios.keys()))

    def _save(self) -> None:
        """Salva portfolios no PaperStatePort preservando outros dados."""
        estado = self._paper_state.carregar()

        # Atualiza apenas portfolios e default_id, preserva resto
        estado.portfolios = {
            pid: {
                "id": p.id,
                "nome": p.nome,
                "saldo_inicial": p.saldo_inicial,
                "saldo_atual": p.saldo_atual,
                "criado_em": p.criado_em.isoformat(),
            }
            for pid, p in self._portfolios.items()
        }
        estado.default_id = self._default_id

        self._paper_state.salvar(estado)

    def find_by_id(self, portfolio_id: str) -> Portfolio:
        if portfolio_id not in self._portfolios:
            raise ValueError(f"Portfolio {portfolio_id} não encontrado")
        return self._portfolios[portfolio_id]

    def find_default(self) -> Portfolio:
        if not self._default_id:
            raise ValueError("Nenhum portfolio padrão definido")
        return self._portfolios[self._default_id]

    def save(self, portfolio: Portfolio) -> None:
        self._portfolios[portfolio.id] = portfolio
        self._save()
