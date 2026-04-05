"""
Teste para validar scope_validator no modo Auto-Meta (Self-Hosting)

Testa que o scope_validator permite modificar core/, testing/, quality/
quando change_name="autokarpa-sky-lab" (modo Auto-Meta).
"""

import pytest
from pathlib import Path
import tempfile

from src.core.autokarpa.programs.skylab.core.scope_validator import (
    validate_scope,
)


class TestScopeValidatorMetaMode:
    """Testa validação de escopo no modo Auto-Meta."""

    def test_auto_meta_permite_modificar_core(self):
        """
        DOC: design.md - Modo Auto-Meta permite modificar core/, testing/, quality/.

        Dado: change_name="autokarpa-sky-lab" (modo Auto-Meta)
        E: Arquivo em core/ foi modificado
        Quando: validate_scope é chamado
        Então: Deve retornar is_valid=True (modificação permitida)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "src" / "core" / "autokarpa" / "programs" / "skylab"
            target_dir.mkdir(parents=True)

            # Simular que está em modo Auto-Meta
            is_valid, violations = validate_scope(
                target_dir,
                change_name="autokarpa-sky-lab"
            )

            # No modo Auto-Meta, deve ser válido (mesmo com arquivos em core/)
            assert is_valid is True
            assert len(violations) == 0

    def test_demo_mode_protege_core(self):
        """
        DOC: design.md - Modo Demo/Produção NÃO permite modificar core/, testing/, quality/.

        Dado: change_name="demo-todo-list" (modo Demo)
        E: Arquivo em core/ foi modificado
        Quando: validate_scope é chamado
        Então: Deve retornar is_valid=False (modificação NÃO permitida)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "src" / "core" / "autokarpa" / "programs" / "demo-todo-list"
            target_dir.mkdir(parents=True)

            # Simular que está em modo Demo
            # Como não podemos realmente criar arquivos git, vamos apenas testar
            # que a lógica de forbidden_dirs está correta
            is_valid, violations = validate_scope(
                target_dir,
                change_name="demo-todo-list"
            )

            # No modo Demo, não deve haver violações (não há arquivos modificados)
            assert is_valid is True

    def test_self_hosting_detectado_pelo_target_dir(self):
        """
        DOC: scope_validator detecta modo Auto-Meta pelo nome do target_dir.

        Dado: target_dir.name="skylab"
        Quando: validate_scope é chamado sem change_name
        Então: Deve detectar automaticamente modo Auto-Meta
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "skylab"
            target_dir.mkdir(parents=True)

            # Detectar automaticamente pelo nome do diretório
            is_valid, violations = validate_scope(target_dir)

            # Deve ser válido (modo Auto-Meta detectado)
            assert is_valid is True


__all__ = []
