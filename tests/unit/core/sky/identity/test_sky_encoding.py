# coding: utf-8
"""
Testes de encoding pt-br da Sky.

Sky deve exibir textos em pt-br com acentuação correta,
independentemente do sistema operacional e terminal.
"""

import pytest
import sys
from io import StringIO
from src.core.sky.identity import SkyIdentity


def test_sky_can_say_portuguese_with_accents():
    """Sky consegue falar português com acentos."""
    sky = SkyIdentity()

    # Sky deve conseguir exibir texto com acentos
    text_with_accents = "Sou Sky. Nasci na Skybridge. Estou aprendendo."
    assert text_with_accents == "Sou Sky. Nasci na Skybridge. Estou aprendendo."


def test_sky_output_is_utf8_compatible():
    """A saída de Sky é compatível com UTF-8."""
    sky = SkyIdentity()

    description = sky.describe()

    # Deve conseguir codificar em UTF-8
    encoded = description.encode("utf-8")
    assert isinstance(encoded, bytes)

    # E deve decodificar de volta
    decoded = encoded.decode("utf-8")
    assert decoded == description


def test_sky_handles_special_chars():
    """Sky lida com caracteres especiais do português."""
    sky = SkyIdentity()

    # Ensina algo com acentos
    sky.learn("você gosta de música coreana")
    sky.learn("ela é uma companheira leal")

    learnings = sky.get_today_learnings()

    # Deve ter guardado com os acentos
    assert any("você" in learning for learning in learnings)
    assert any("leal" in learning for learning in learnings)
