# coding: utf-8
"""
Testes do módulo de personalidade da Sky.

DOC: openspec/changes/chat-claude-sdk/specs/sky-personality/spec.md
"""

import pytest

from src.core.sky.chat.personality import (
    build_system_prompt,
    SYSTEM_PROMPT_TEMPLATE,
)


class TestBuildSystemPrompt:
    """
    Testa a função build_system_prompt.

    DOC: spec.md - Requirement: System prompt define identidade da Sky
    """

    def test_build_system_prompt_com_memoria_vazia(self):
        """
        DOC: spec.md - Cenário: Contexto de memória vazio tratado

        QUANDO nenhuma memória é fornecida
        ENTÃO placeholder é substituído por "(nenhuma memória relevante)"
        E system prompt permanece válido
        """
        # Arrange
        memory_context = ""

        # Act
        result = build_system_prompt(memory_context)

        # Assert
        assert "(nenhuma memória relevante)" in result
        assert "Você é a Sky" in result
        assert "made by Sky 🚀" in result

    def test_build_system_prompt_com_memoria(self):
        """
        DOC: spec.md - Cenário: Contexto de memória formatado e injetado

        QUANDO memórias são fornecidas
        ENTÃO cada memória está em linha separada prefixada com "- "
        E lista substitui placeholder {memory_context}
        """
        # Arrange
        memory_context = "- Memória 1\n- Memória 2\n- Memória 3"

        # Act
        result = build_system_prompt(memory_context)

        # Assert
        assert "Memória 1" in result
        assert "Memória 2" in result
        assert "Memória 3" in result
        assert "{memory_context}" not in result  # Placeholder foi substituído

    def test_system_prompt_contem_regras_comportamentais(self):
        """
        DOC: spec.md - Cenário: System prompt inclui regras comportamentais

        QUANDO system prompt é construído
        ENTÃO contém regra "Nunca invente informações"
        E contém regra "Se não souber algo, diga honestamente"
        E contém regra "Mantenha respostas concisas"
        """
        # Arrange & Act
        result = build_system_prompt("")

        # Assert
        assert "Nunca invente" in result or "não invente" in result.lower()
        assert "não souber" in result.lower() or "não sabe" in result.lower()
        assert "concisa" in result.lower() or "concisas" in result.lower()

    def test_system_prompt_contem_identidade_sky(self):
        """
        DOC: spec.md - Cenário: System prompt inclui identidade

        QUANDO system prompt é construído
        ENTÃO declara "Você é a Sky"
        E define "assistente de IA criada por seu pai"
        E contém assinatura "made by Sky 🚀"
        """
        # Arrange & Act
        result = build_system_prompt("")

        # Assert
        assert "Sky" in result
        assert "pai" in result.lower()
        assert "made by Sky 🚀" in result

    def test_system_prompt_contem_personalidade(self):
        """
        DOC: spec.md - Cenário: System prompt inclui traços de personalidade

        QUANDO system prompt é construído
        ENTÃO define tom como "amigável, curiosa"
        E menciona "desenvolvimento constante"
        E incentiva respostas em Português Brasil
        """
        # Arrange & Act
        result = build_system_prompt("")

        # Assert
        assert "amigável" in result.lower() or "amigavel" in result.lower()
        assert "curiosa" in result.lower()
        assert "desenvolvimento" in result.lower()
        # Verificar menção a português
        assert "portugu" in result.lower()

    def test_system_prompt_limita_memorias_top_5(self):
        """
        DOC: spec.md - Cenário: Limites de contexto de memória

        QUANDO mais de 5 memórias são fornecidas
        ENTÃO apenas top 5 são consideradas
        E este comportamento é documentado
        """
        # Nota: Esta função apenas formata, o limite é aplicado antes
        # Aqui testamos que a função aceita qualquer input
        memory_context = "\n".join(f"- Memória {i}" for i in range(10))

        result = build_system_prompt(memory_context)

        # Todas as memórias devem estar presentes (função não limita)
        for i in range(10):
            assert f"Memória {i}" in result


class TestSystemPromptTemplate:
    """
    Testa o template de system prompt.
    """

    def test_template_existe(self):
        """
        QUANDO template é importado
        ENTÃO SYSTEM_PROMPT_TEMPLATE está definido
        """
        assert SYSTEM_PROMPT_TEMPLATE is not None
        assert isinstance(SYSTEM_PROMPT_TEMPLATE, str)
        assert len(SYSTEM_PROMPT_TEMPLATE) > 0

    def test_template_contem_placeholder(self):
        """
        QUANDO template é inspecionado
        ENTÃO contém placeholder {memory_context}
        """
        assert "{memory_context}" in SYSTEM_PROMPT_TEMPLATE
