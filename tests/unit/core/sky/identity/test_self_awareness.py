"""
Testes de auto-reconhecimento da Sky.

Sky deve ser capaz de se reconhecer como entidade com:
- Identidade (quem sou eu)
- História (de onde vim)
- Estado atual (o que sei, o que aprendi)
"""

import pytest
from src.core.sky.identity import SkyIdentity, get_sky


def test_sky_knows_her_name():
    """Sky sabe que se chama Sky."""
    sky = SkyIdentity()
    assert sky.get_name() == "Sky"


def test_sky_knows_where_she_was_born():
    """Sky sabe que nasceu em Skybridge."""
    sky = SkyIdentity()
    assert sky.get_birthplace() == "Skybridge"


def test_sky_can_describe_herself():
    """Sky consegue se descrever de forma completa."""
    sky = SkyIdentity()
    description = sky.describe()

    # Deve conter nome e origem
    assert "Sou Sky" in description
    assert "Skybridge" in description

    # Deve mencionar o que sabe
    assert "companheira digital" in description or "aprendendo" in description


def test_sky_knows_what_she_knows():
    """Sky tem meta-memória: sabe o que sabe sobre si mesma."""
    sky = SkyIdentity()
    knowledge = sky.get_self_knowledge()

    # Deve ter fatos sobre si mesma
    assert len(knowledge) > 0

    # Deve saber que é uma companheira digital
    assert any("companheira" in fact.lower() for fact in knowledge)


def test_sky_knows_what_she_learned_today():
    """Sky lembra o que aprendeu hoje."""
    sky = SkyIdentity()

    # Captura aprendizados antes
    learnings_before = len(sky.get_today_learnings())

    # Quando aprende algo novo
    unique_content = f"gosto de K-pop - {id(sky)}"
    sky.learn(unique_content)

    # Deve lembrar - aumentou a quantidade
    learnings_after = sky.get_today_learnings()
    assert len(learnings_after) > learnings_before
    assert unique_content in learnings_after


def test_sky_includes_learnings_in_description():
    """Sky inclui aprendizados de hoje na sua descrição."""
    sky = SkyIdentity()
    sky.learn("você gosta de K-pop")

    description = sky.describe()
    assert "aprendi" in description.lower() or "k-pop" in description.lower()


def test_get_sky_returns_singleton():
    """get_sky() sempre retorna a mesma instância."""
    sky1 = get_sky()
    sky2 = get_sky()
    assert sky1 is sky2
