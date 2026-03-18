# coding: utf-8
"""
Teste manual da correção da tooltip duplicada.
"""

from datetime import datetime
from src.core.sky.chat.textual_ui.widgets.title import TitleStatic
from src.core.sky.chat.textual_ui.widgets.animated_verb import EstadoLLM
from src.core.sky.chat.textual_ui.widgets.title_history import TitleHistory


def test_tooltip_remove_duplicatas_consecutivas():
    """
    Testa se a tooltip remove duplicatas consecutivas (gerúndio + passado).
    """
    # Arrange: cria histórico com duplicatas
    history = TitleHistory()

    # Simula a sequência: processando → processou → analisando → analisou → testando → testou
    history.add(EstadoLLM(verbo="processando", predicado="sua solicitação"))
    history.add(EstadoLLM(verbo="processou", predicado="sua solicitação"))
    history.add(EstadoLLM(verbo="analisando", predicado="o código"))
    history.add(EstadoLLM(verbo="analisou", predicado="o código"))
    history.add(EstadoLLM(verbo="testando", predicado="a correção"))
    history.add(EstadoLLM(verbo="testou", predicado="a correção"))

    # Act: cria TitleStatic e atualiza tooltip
    title_static = TitleStatic("Teste")
    title_static.update_tooltip(history)

    # Assert: verifica se a tooltip não tem duplicatas
    tooltip = title_static.tooltip
    print(f"Tooltip gerada:\n{tooltip}\n")

    # Verifica se não aparecem duplicatas consecutivas
    assert "processando → processou" not in tooltip
    assert "analisando → analisou" not in tooltip
    assert "testando → testou" not in tooltip

    # Verifica se aparece apenas uma vez cada radical (preferencialmente o passado)
    # A lógica pega os últimos 10, remove duplicatas e pega até 5 únicos
    assert "processou" in tooltip or "processando" in tooltip
    assert "analisou" in tooltip or "analisando" in tooltip
    assert "testou" in tooltip or "testando" in tooltip

    # Conta quantas vezes cada radical aparece
    tooltip_lower = tooltip.lower()
    process_count = tooltip_lower.count("process")
    analis_count = tooltip_lower.count("analis")
    test_count = tooltip_lower.count("test")

    # Cada radical deve aparecer no máximo 1 vez
    assert process_count <= 1, f"Radical 'process' apareceu {process_count} vezes"
    assert analis_count <= 1, f"Radical 'analis' apareceu {analis_count} vezes"
    assert test_count <= 1, f"Radical 'test' apareceu {test_count} vezes"

    print("✅ Teste passou: Tooltip não tem duplicatas consecutivas!")


def test_tooltip_mantem_verbos_diferentes():
    """
    Testa se a tooltip mantém verbos diferentes mesmo com o mesmo radical.
    """
    # Arrange: cria histórico com verbos diferentes
    history = TitleHistory()

    # Adiciona verbos com radicais diferentes
    history.add(EstadoLLM(verbo="buscando", predicado="informações"))
    history.add(EstadoLLM(verbo="analisando", predicado="dados"))
    history.add(EstadoLLM(verbo="escrevendo", predicado="código"))
    history.add(EstadoLLM(verbo="testando", predicado="solução"))
    history.add(EstadoLLM(verbo="finalizando", predicado="tarefa"))

    # Act: cria TitleStatic e atualiza tooltip
    title_static = TitleStatic("Teste")
    title_static.update_tooltip(history)

    # Assert: verifica se todos os verbos aparecem
    tooltip = title_static.tooltip
    print(f"Tooltip gerada:\n{tooltip}\n")

    assert "buscando" in tooltip
    assert "analisando" in tooltip
    assert "escrevendo" in tooltip
    assert "testando" in tooltip
    assert "finalizando" in tooltip

    print("✅ Teste passou: Tooltip mantém verbos diferentes!")


def test_extrair_radical():
    """
    Testa a função _extrair_radical com vários casos.
    """
    # Arrange
    from src.core.sky.chat.textual_ui.widgets.title import TitleStatic

    # Act & Assert
    test_cases = [
        ("processando", "process"),
        ("processou", "process"),
        ("analisando", "analis"),
        ("analisou", "analis"),
        ("escrevendo", "escrev"),
        ("escreveu", "escrev"),
        ("corrigindo", "corrig"),
        ("corrigiu", "corrig"),
        ("emitindo", "emit"),
        ("emitiu", "emit"),
    ]

    for verbo, expected_radical in test_cases:
        radical = TitleStatic._extrair_radical(verbo)
        assert radical == expected_radical, f"Para '{verbo}': esperava '{expected_radical}', got '{radical}'"
        print(f"✅ {verbo} → {radical}")

    print("✅ Teste passou: Extração de radical funciona corretamente!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testando a correção da tooltip duplicada")
    print("=" * 60)
    print()

    test_extrair_radical()
    print()

    test_tooltip_remove_duplicatas_consecutivas()
    print()

    test_tooltip_mantem_verbos_diferentes()
    print()

    print("=" * 60)
    print("🎉 Todos os testes passaram!")
    print("=" * 60)
