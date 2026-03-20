# -*- coding: utf-8 -*-
"""
Testes para o Feature Toggle da Voice API.

DOC: openspec/changes/voice-api-isolation/tasks.md - Fase 1, Task 1.4
"""

import os
import pytest

from core.sky.voice.feature_toggle import (
    is_voice_api_enabled,
    get_voice_api_port,
    get_voice_api_url,
)


class TestVoiceAPIFeatureToggle:
    """
    Testes do feature toggle SKYBRIDGE_VOICE_API_ENABLED.
    """

    def test_default_is_disabled(self):
        """
        DOC: feature toggle - Default é desabilitado.

        Comportamento:
        - Sem variável de ambiente → False
        - Protege contra ativação acidental
        """
        # Remove variável se existir
        if "SKYBRIDGE_VOICE_API_ENABLED" in os.environ:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

        # Assert: default é False
        assert is_voice_api_enabled() is False

    def test_enabled_with_1(self):
        """
        DOC: feature toggle - "1" habilita.

        Comportamento:
        - SKYBRIDGE_VOICE_API_ENABLED=1 → True
        """
        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "1"

        try:
            assert is_voice_api_enabled() is True
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

    def test_enabled_with_true(self):
        """
        DOC: feature toggle - "true" habilita.

        Comportamento:
        - SKYBRIDGE_VOICE_API_ENABLED=true → True
        - Case-insensitive
        """
        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "true"

        try:
            assert is_voice_api_enabled() is True
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

    def test_enabled_with_yes(self):
        """
        DOC: feature toggle - "yes" habilita.

        Comportamento:
        - SKYBRIDGE_VOICE_API_ENABLED=yes → True
        """
        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "yes"

        try:
            assert is_voice_api_enabled() is True
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

    def test_case_insensitive(self):
        """
        DOC: feature toggle - Case-insensitive.

        Comportamento:
        - "TRUE", "True", "TrUe" → True
        - "0", "false", "no" → False
        """
        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "TRUE"

        try:
            assert is_voice_api_enabled() is True
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "false"

        try:
            assert is_voice_api_enabled() is False
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

    def test_disabled_with_0(self):
        """
        DOC: feature toggle - "0" desabilita.

        Comportamento:
        - SKYBRIDGE_VOICE_API_ENABLED=0 → False
        - Também funciona com qualquer valor não reconhecido
        """
        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "0"

        try:
            assert is_voice_api_enabled() is False
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]

    def test_disabled_with_any_value(self):
        """
        DOC: feature toggle - Valores não reconhecidos desabilitam.

        Comportamento:
        - "abc", "2", "on" → False (só 1/true/yes habilitam)
        - Fail-safe: default é desabilitado
        """
        os.environ["SKYBRIDGE_VOICE_API_ENABLED"] = "abc"

        try:
            assert is_voice_api_enabled() is False
        finally:
            del os.environ["SKYBRIDGE_VOICE_API_ENABLED"]


class TestVoiceAPIConfig:
    """
    Testes de configuração da Voice API.
    """

    def test_default_port(self):
        """
        DOC: config - Porta default é 8765.

        Comportamento:
        - Sem variável → 8765
        """
        if "VOICE_API_PORT" in os.environ:
            del os.environ["VOICE_API_PORT"]

        assert get_voice_api_port() == 8765

    def test_custom_port(self):
        """
        DOC: config - Porta customizada.

        Comportamento:
        - VOICE_API_PORT=9999 → 9999
        """
        os.environ["VOICE_API_PORT"] = "9999"

        try:
            assert get_voice_api_port() == 9999
        finally:
            del os.environ["VOICE_API_PORT"]

    def test_invalid_port_uses_default(self):
        """
        DOC: config - Porta inválida usa default.

        Comportamento:
        - VOICE_API_PORT=abc → 8765 (fallback)
        - Fail-safe: não crasha com valor inválido
        """
        os.environ["VOICE_API_PORT"] = "abc"

        try:
            assert get_voice_api_port() == 8765
        finally:
            del os.environ["VOICE_API_PORT"]

    def test_default_url(self):
        """
        DOC: config - URL default é localhost:8765.

        Comportamento:
        - Sem variáveis → http://127.0.0.1:8765
        """
        if "VOICE_API_HOST" in os.environ:
            del os.environ["VOICE_API_HOST"]
        if "VOICE_API_PORT" in os.environ:
            del os.environ["VOICE_API_PORT"]

        assert get_voice_api_url() == "http://127.0.0.1:8765"

    def test_custom_url(self):
        """
        DOC: config - URL customizada.

        Comportamento:
        - VOICE_API_HOST=localhost → http://localhost:8765
        - VOICE_API_PORT=9000 → porta customizada
        """
        os.environ["VOICE_API_HOST"] = "localhost"
        os.environ["VOICE_API_PORT"] = "9000"

        try:
            assert get_voice_api_url() == "http://localhost:9000"
        finally:
            del os.environ["VOICE_API_HOST"]
            del os.environ["VOICE_API_PORT"]
