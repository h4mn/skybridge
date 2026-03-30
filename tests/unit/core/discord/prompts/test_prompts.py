# -*- coding: utf-8 -*-
"""
Testes de Prompts - Sistema de prompts Discord.

Valida geração de prompts do módulo Discord.
"""

import pytest

from src.core.discord.prompts import (
    get_identity_prompt,
    get_context_prompt,
    get_tools_guide_prompt,
    get_security_prompt,
    get_discord_system_prompt,
)
from src.core.discord.prompts.templates import (
    get_saudacao_padrao,
    get_erro_padrao,
    get_progresso_em_andamento,
)


class TestPromptsModulos:
    """Testes de prompts de módulos."""

    def test_identity_prompt_nao_vazio(self):
        """Testa que prompt de identidade não é vazio."""
        prompt = get_identity_prompt()
        assert len(prompt) > 0
        assert "SkyBridge" in prompt

    def test_context_prompt_contem_tools(self):
        """Testa que prompt de contexto menciona tools."""
        prompt = get_context_prompt()
        assert "chat_id" in prompt
        assert "message_id" in prompt

    def test_tools_guide_menciona_send_progress(self):
        """Testa que guia menciona send_progress com tracking_id."""
        prompt = get_tools_guide_prompt()
        assert "send_progress" in prompt
        assert "tracking_id" in prompt

    def test_security_prompt_menciona_seguranca(self):
        """Testa que prompt de segurança menciona regras."""
        prompt = get_security_prompt()
        assert "NUNCA" in prompt
        assert "SEMPRE" in prompt

    def test_system_prompt_combina_todos(self):
        """Testa que system prompt combina todos os prompts."""
        prompt = get_discord_system_prompt()
        assert "SkyBridge" in prompt  # identidade
        assert "chat_id" in prompt  # contexto
        assert "send_progress" in prompt  # tools
        assert "NUNCA" in prompt  # segurança


class TestPromptTemplates:
    """Testes de templates de prompt."""

    def test_saudacao_padrao(self):
        """Testa saudação padrão."""
        saudacao = get_saudacao_padrao()
        assert "Olá" in saudacao
        assert "SkyBridge" in saudacao

    def test_erro_padrao(self):
        """Testa erro padrão."""
        erro = get_erro_padrao("Algo deu ruim")
        assert "Algo deu ruim" in erro
        assert "❌" in erro

    def test_progresso_em_andamento(self):
        """Testa progresso em andamento."""
        progresso = get_progresso_em_andamento("Título", "███░░░░░░░░░░░░░░░░", 25, "Processando...")
        assert "Título" in progresso
        assert "25%" in progresso
        assert "Processando..." in progresso
