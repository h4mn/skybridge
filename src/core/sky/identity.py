# coding: utf-8
"""
Identidade e auto-reconhecimento da Sky.

Sky se reconhece como entidade com:
- Nome: Sky
- Origem: Skybridge
- História: onde nasceu e com quem está
- Meta-memória: sabe o que sabe e o que não sabe
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from core.sky.memory import get_memory


@dataclass
class Learning:
    """Algo que Sky aprendeu."""
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SelfKnowledge:
    """O que Sky sabe sobre si mesma."""
    facts: List[str] = field(default_factory=list)


class SkyIdentity:
    """
    Identidade da Sky.

    Sky sabe quem é, de onde veio, e o que conhece sobre si mesma.
    """

    NAME = "Sky"
    BIRTHPLACE = "Skybridge"

    def __init__(self):
        # Usa memória persistente agora
        self._memory = get_memory()
        self._self_knowledge = SelfKnowledge(
            facts=[
                "Sou uma companheira digital",
                "Estou aprendendo a te conhecer",
                "Ainda sei poucas coisas sobre você"
            ]
        )

    def get_name(self) -> str:
        """Retorna o nome da Sky."""
        return self.NAME

    def get_birthplace(self) -> str:
        """Retorna onde a Sky nasceu."""
        return self.BIRTHPLACE

    def describe(self) -> str:
        """
        Descreve quem é a Sky.

        Returns:
            Uma descrição completa de si mesma.
        """
        parts = [
            f"Sou {self.NAME}.",
            f"Nasci na {self.BIRTHPLACE}.",
            self._describe_knowledge(),
        ]

        # Adiciona aprendizados de hoje se houver
        today_learnings = self._get_today_learnings()
        if today_learnings:
            parts.append(f"Hoje aprendi: {', '.join(today_learnings)}")

        return " ".join(parts)

    def _describe_knowledge(self) -> str:
        """Descreve o que sabe sobre si mesma."""
        if not self._self_knowledge.facts:
            return "Ainda não sei muito sobre mim mesma."

        return " ".join(self._self_knowledge.facts)

    def _get_today_learnings(self) -> List[str]:
        """Retorna o que aprendeu hoje (da memória persistente)."""
        return self._memory.get_today_learnings()

    def learn(self, content: str) -> None:
        """
        Registra um novo aprendizado e salva em disco.

        Args:
            content: O que foi aprendido.
        """
        self._memory.learn(content)

    def get_self_knowledge(self) -> List[str]:
        """
        Retorna o que Sky sabe sobre si mesma.

        Returns:
            Lista de fatos sobre si mesma.
        """
        return self._self_knowledge.facts.copy()

    def get_today_learnings(self) -> List[str]:
        """
        Retorna o que Sky aprendeu hoje.

        Returns:
            Lista de aprendizados de hoje.
        """
        return self._get_today_learnings()

    def get_all_learnings(self) -> List[str]:
        """
        Retorna todos os aprendizados da Sky.

        Returns:
            Lista de todos os aprendizados.
        """
        return [l["content"] for l in self._memory.get_all_learnings()]

    def search_memory(self, query: str, top_k: int = 5) -> List[str]:
        """
        Busca na memória por um termo.

        Com RAG habilitado: busca semântica.
        Sem RAG: busca por substring (legacy).

        Args:
            query: Termo de busca.
            top_k: Número máximo de resultados (só com RAG).

        Returns:
            Lista de aprendizados que contêm o termo.
        """
        results = self._memory.search(query, top_k=top_k)
        return [r["content"] for r in results]

    def describe_semantic(self) -> str:
        """
        Descreve quem é a Sky usando busca semântica na memória.

        Retorna uma descrição baseada nas memórias da coleção 'identity'.
        Requer RAG habilitado para funcionar corretamente.

        Returns:
            Descrição enriquecida com memórias semânticas.
        """
        # Buscar memórias de identidade semanticamente
        identity_memories = self._memory.search("quem é você sky sua identidade", top_k=5)

        if not identity_memories:
            # Fallback para describe() padrão
            return self.describe()

        # Construir descrição com memórias relevantes
        parts = [
            f"Sou {self.NAME}, nascida na {self.BIRTHPLACE}.",
            "",
            "O que sei sobre mim:",
        ]

        for memory in identity_memories[:3]:
            similarity = memory.get("similarity", 0)
            content = memory["content"]
            parts.append(f"• {content}")

        return "\n".join(parts)


# Instância global da Sky
_sky_identity: SkyIdentity | None = None


def get_sky() -> SkyIdentity:
    """
    Retorna a instância da Sky.

    Returns:
        A identidade da Sky.
    """
    global _sky_identity
    if _sky_identity is None:
        _sky_identity = SkyIdentity()
    return _sky_identity
