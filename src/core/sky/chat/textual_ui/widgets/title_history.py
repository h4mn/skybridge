# coding: utf-8
"""
TitleHistory - Histórico de títulos animados durante a sessão de chat.

DOC: openspec/changes/sky-chat-animated-title-history
"""

from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

from .animated_verb import EstadoLLM


@dataclass
class TitleEntry:
    """
    Entrada do histórico de títulos.

    Atributos:
        estado: EstadoLLM exibido
        inicio: Timestamp de quando o estado começou a ser exibido
        fim: Timestamp de quando o estado parou de ser exibido (None se ativo)
    """
    estado: EstadoLLM
    inicio: datetime
    fim: datetime | None = None


class TitleHistory:
    """
    Histórico sequencial de títulos animados durante a sessão.

    Acumula cada EstadoLLM exibido no AnimatedTitle em ordem cronológica,
    permitindo consultar últimos N estados e gerar resumos de sessão.
    """

    def __init__(self) -> None:
        self._entries: list[TitleEntry] = []

    def add(self, estado: EstadoLLM) -> None:
        """
        Adiciona um novo estado ao histórico.

        Atualiza o campo `fim` da entrada anterior (se existir) para marcar
        o momento em que aquele estado parou de ser exibido.
        """
        agora = datetime.now()

        # Atualiza fim da entrada anterior
        if self._entries:
            self._entries[-1].fim = agora

        # Adiciona nova entrada
        self._entries.append(TitleEntry(estado=estado, inicio=agora))

    def get_last(self, n: int) -> list[TitleEntry]:
        """Retorna as últimas N entradas do histórico (mais recentes primeiro)."""
        return self._entries[-n:][::-1] if n > 0 else []

    @property
    def entries(self) -> list[TitleEntry]:
        """Retorna todas as entradas em ordem cronológica."""
        return self._entries.copy()

    def gerar_resumo(self) -> dict:
        """
        Gera um resumo estatístico da sessão baseado no histórico.

        Returns:
            Dict com:
                - tempo_por_emocao: {emoção: tempo_total_segundos}
                - contagem_revisoes: int (estados com direcao=-1)
                - top_estados: [(verbo, predicado, count), ...] top 3
                - tempo_total_sessao: float (segundos)
        """
        if not self._entries:
            return {
                "tempo_por_emocao": {},
                "contagem_revisoes": 0,
                "top_estados": [],
                "tempo_total_sessao": 0.0,
            }

        tempo_por_emocao: Counter[str] = Counter()
        contagem_revisoes = 0
        estados_counter: Counter[tuple[str, str]] = Counter()
        tempo_total = 0.0

        for entry in self._entries:
            estado = entry.estado
            fim = entry.fim or datetime.now()
            duracao = (fim - entry.ini).total_seconds()

            # Tempo por emoção
            tempo_por_emocao[estado.emocao] += duracao

            # Contagem de revisões (direção negativa)
            if estado.direcao == -1:
                contagem_revisoes += 1

            # Contagem de estados por (verbo, predicado)
            chave = (estado.verbo, estado.predicado)
            estados_counter[chave] += 1

            # Tempo total
            tempo_total += duracao

        # Top 3 estados mais frequentes
        top_estados = [
            (verbo, predicado, count)
            for (verbo, predicado), count in estados_counter.most_common(3)
        ]

        return {
            "tempo_por_emocao": dict(tempo_por_emocao),
            "contagem_revisoes": contagem_revisoes,
            "top_estados": top_estados,
            "tempo_total_sessao": tempo_total,
        }


__all__ = ["TitleHistory", "TitleEntry"]
