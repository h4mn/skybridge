# coding: utf-8
"""
Stage - Configuração de um estágio de bootstrap.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Stage:
    """
    Configuração de um estágio de bootstrap.

    Attributes:
        name: Nome identificador do estágio (ex: "environment", "embedding")
        description: Descrição amigável para exibir na barra de progresso
        weight: Peso relativo do estágio (para cálculo de progresso total)
    """

    name: str
    description: str
    weight: float = 1.0

    def with_size_info(self, size_mb: Optional[float] = None) -> "Stage":
        """
        Retorna uma cópia do Stage com informação de tamanho na descrição.

        Args:
            size_mb: Tamanho em MB, ou None para vazio/novo

        Returns:
            Novo Stage com descrição atualizada.
        """
        if size_mb is None:
            new_desc = f"{self.description} (novo)"
        elif size_mb == 0:
            new_desc = f"{self.description} (0 MB)"
        else:
            new_desc = f"{self.description} ({size_mb:.1f} MB)"

        return Stage(
            name=self.name,
            description=new_desc,
            weight=self.weight,
        )

    def with_collections_info(self, collections: list[str]) -> "Stage":
        """
        Retorna uma cópia do Stage com nomes das coleções na descrição.

        Args:
            collections: Lista de nomes de coleções

        Returns:
            Novo Stage com descrição atualizada.
        """
        if not collections:
            new_desc = f"{self.description} (criando defaults)"
        else:
            collections_str = ", ".join(collections)
            new_desc = f"{self.description} ({collections_str})"

        return Stage(
            name=self.name,
            description=new_desc,
            weight=self.weight,
        )
