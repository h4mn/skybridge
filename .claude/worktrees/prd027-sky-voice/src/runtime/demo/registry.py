# -*- coding: utf-8 -*-
"""
Demo Registry — Registro centralizado de demos.

Gerencia o catálogo de todas as demos disponíveis no sistema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from runtime.demo.base import BaseDemo, DemoCategory


class DemoRegistry:
    """
    Registro centralizado de demos.

    Utiliza padrão Singleton para manter um único catálogo
    de todas as demos disponíveis no sistema.

    Exemplo de registro::

        @DemoRegistry.register
        class MyDemo(BaseDemo):
            demo_id = "my-demo"
            ...

    Exemplo de uso::

        # Lista todas as demos
        all_demos = DemoRegistry.list_all()

        # Lista por categoria
        trello_demos = DemoRegistry.list_by_category(DemoCategory.TRELLO)

        # Busca por ID
        demo_class = DemoRegistry.get("trello-flow")
    """

    _demos: dict[str, Type[BaseDemo]] = {}

    @classmethod
    def register(cls, demo_class: Type[BaseDemo]) -> Type[BaseDemo]:
        """
        Decorador para registrar uma demo.

        Args:
            demo_class: Classe da demo a ser registrada.

        Returns:
            A própria classe (para uso como decorator).

        Raises:
            ValueError: Se demo_id já estiver registrado.
        """
        if demo_class.demo_id in cls._demos:
            raise ValueError(f"Demo ID '{demo_class.demo_id}' já registrado")

        if demo_class.demo_id is NotImplemented:
            raise ValueError(f"Demo {demo_class.__name__} não define demo_id")

        cls._demos[demo_class.demo_id] = demo_class
        return demo_class

    @classmethod
    def get(cls, demo_id: str) -> Type[BaseDemo] | None:
        """
        Obtém uma classe de demo por ID.

        Args:
            demo_id: ID da demo desejada.

        Returns:
            Classe da demo ou None se não encontrada.
        """
        return cls._demos.get(demo_id)

    @classmethod
    def list_all(cls) -> dict[str, Type[BaseDemo]]:
        """
        Lista todas as demos registradas.

        Returns:
            Dicionário mapeando demo_id → classe.
        """
        return cls._demos.copy()

    @classmethod
    def list_by_category(cls, category: "DemoCategory") -> list[Type[BaseDemo]]:
        """
        Lista demos por categoria.

        Args:
            category: Categoria desejada.

        Returns:
            Lista de classes de demo da categoria.
        """
        return [d for d in cls._demos.values() if d.category == category]

    @classmethod
    def list_by_tag(cls, tag: str) -> list[Type[BaseDemo]]:
        """
        Lista demos por tag.

        Args:
            tag: Tag desejada.

        Returns:
            Lista de classes de demo com a tag.
        """
        return [d for d in cls._demos.values() if tag in d.tags]

    @classmethod
    def list_by_issue(cls, issue_number: int) -> list[Type[BaseDemo]]:
        """
        Lista demos relacionadas a uma issue específica.

        Permite que agentes descubram demos relevantes para a issue
        que estão trabalhando.

        Args:
            issue_number: Número da issue do GitHub.

        Returns:
            Lista de classes de demo relacionadas à issue.

        Exemplo:
            # Demo está relacionada às issues 36, 38, 40
            class MyDemo(BaseDemo):
                related_issues = [36, 38, 40]

            # Busca demos da issue 38
            demos = DemoRegistry.list_by_issue(38)  # [MyDemo]
        """
        result = []
        for demo_class in cls._demos.values():
            demo_instance = demo_class()
            if issue_number in demo_instance.related_issues:
                result.append(demo_class)
        return result

    @classmethod
    def get_issue_mapping(cls) -> dict[int, list[str]]:
        """
        Retorna mapeamento de issue → demo_ids.

        Útil para descobrir quais issues têm demos associadas.

        Returns:
            Dicionário mapeando issue_number → lista de demo_ids.
        """
        mapping: dict[int, list[str]] = {}

        for demo_id, demo_class in cls._demos.items():
            # Cria instância para acessar related_issues
            try:
                demo_instance = demo_class()
                # Usa getattr com valor padrão caso seja Field ou outro valor não iterável
                related_issues = getattr(demo_instance, 'related_issues', [])
                if not isinstance(related_issues, list):
                    related_issues = []
            except Exception:
                related_issues = []

            for issue in related_issues:
                if issue not in mapping:
                    mapping[issue] = []
                mapping[issue].append(demo_id)

        return mapping

    @classmethod
    def count(cls) -> int:
        """
        Retorna o número total de demos registradas.

        Returns:
            Número de demos.
        """
        return len(cls._demos)

    @classmethod
    def categories(cls) -> list["DemoCategory"]:
        """
        Lista todas as categorias que têm demos.

        Returns:
            Lista de categorias com pelo menos uma demo.
        """
        from runtime.demo.base import DemoCategory

        return [
            cat for cat in DemoCategory
            if cls.list_by_category(cat)
        ]

    @classmethod
    def clear(cls) -> None:
        """
        Limpa o registro (útil para testes).

        Warning:
            Não use em produção. Apenas para testes unitários.
        """
        cls._demos.clear()

    @classmethod
    def demo_info(cls, demo_id: str) -> dict | None:
        """
        Retorna informações sobre uma demo.

        Args:
            demo_id: ID da demo.

        Returns:
            Dicionário com informações ou None se não encontrada.
        """
        demo_class = cls.get(demo_id)
        if not demo_class:
            return None

        # Cria instância temporária para obter metadados dinâmicos
        demo_instance = demo_class()

        return {
            "id": demo_class.demo_id,
            "name": demo_class.demo_name,
            "description": demo_class.description,
            "category": demo_class.category.value,
            "tags": demo_class.tags,
            "required_configs": demo_class.required_configs,
            "estimated_duration": demo_class.estimated_duration_seconds,
            "flow": str(demo_instance.define_flow()),
        }

    @classmethod
    def all_info(cls) -> list[dict]:
        """
        Retorna informações de todas as demos.

        Returns:
            Lista de dicionários com informações de cada demo.
        """
        return [
            info for demo_id in cls._demos
            if (info := cls.demo_info(demo_id)) is not None
        ]


# Importar DemoCategory aqui para evitar import circular
from runtime.demo.base import DemoCategory
