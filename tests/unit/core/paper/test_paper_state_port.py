# -*- coding: utf-8 -*-
"""Testes unitarios para PaperStatePort e JsonFilePaperState.

Testes:
- carregar estado vazio cria schema v3
- migrar v1 -> 2 -> v3 preserva dados
- broker e repository nao conflitam
"""
import json
import tempfile
from decimal import Decimal
from pathlib import Path
import pytest

from src.core.paper.ports.paper_state_port import PaperStateData
from src.core.paper.adapters.persistence.json_file_paper_state import JsonFilePaperState


class TestPaperStateData:
    """Testes para a dataclass PaperStateData."""

    def test_to_dict_serializa_corretamente(self):
        """Teste: to_dict serializa corretamente."""
        estado = PaperStateData(
            saldo_inicial=Decimal("100000"),
            base_currency="BRL",
            cashbook={
                "base_currency": "BRL",
                "entries": {
                    "BRL": {"amount": "50000", "conversion_rate": "1"}
                }
            },
        )

        data = estado.to_dict()

        assert data["version"] == 3
        assert data["saldo"] == 50000.0  # calculado do cashbook
        assert data["saldo_inicial"] == 100000.0
        assert data["base_currency"] == "BRL"
        assert data["ordens"] == {}
        assert data["posicoes"] == {}
        assert data["portfolios"] == {}

    def test_from_dict_v3_deserializa_corretamente(self):
        """Teste: from_dict deserializa v3 corretamente."""
        data = {
            "version": 3,
            "base_currency": "BRL",
            "cashbook": {
                "base_currency": "BRL",
                "entries": {
                    "BRL": {"amount": "50000", "conversion_rate": "1"},
                    "USD": {"amount": "1000", "conversion_rate": "5.7"},
                }
            },
            "saldo_inicial": 100000.0,
            "ordens": {"ordem-1": {"ticker": "PETR4.SA"}},
            "posicoes": {"PETR4.SA": {"quantidade": 100}},
            "portfolios": {"portfolio-1": {"nome": "Principal"}},
            "default_id": "portfolio-1",
        }

        estado = PaperStateData.from_dict(data)

        assert estado.version == 3
        assert estado.saldo == Decimal("55700")  # 50000 + 1000*5.7
        assert estado.saldo_inicial == Decimal("100000")
        assert "ordem-1" in estado.ordens
        assert "PETR4.SA" in estado.posicoes
        assert "portfolio-1" in estado.portfolios
        assert estado.default_id == "portfolio-1"

    def test_from_dict_legacy_v2_migra_para_v3(self):
        """Teste: from_dict migra v2 -> v3 automaticamente."""
        data = {
            "version": 2,
            "saldo": 50000.0,
            "saldo_inicial": 100000.0,
            "ordens": {},
            "posicoes": {},
        }

        estado = PaperStateData.from_dict(data)

        # Deve ter criado cashbook automaticamente
        assert estado.saldo == Decimal("50000")
        assert "entries" in estado.cashbook
        assert "BRL" in estado.cashbook.get("entries", {})


class TestJsonFilePaperState:
    """Testes para JsonFilePaperState."""

    def test_carregar_estado_vazio_cria_schema_v3(self):
        """Teste: carregar estado vazio cria schema v3."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"
            state = JsonFilePaperState(state_file)

            estado = state.carregar()

            assert estado.version == 3
            assert estado.saldo == Decimal("100000")  # default
            assert estado.saldo_inicial == Decimal("100000")
            assert estado.ordens == {}
            assert estado.posicoes == {}

            # Verifica arquivo foi criado
            assert state_file.exists()
            with open(state_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["version"] == 3

    def test_migrar_v1_para_v3_preserva_dados(self):
        """Teste: migrar v1 -> v3 preserva dados."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"

            # Cria arquivo v1
            v1_data = {
                "version": 1,
                "saldo": 50000.0,
                "saldo_inicial": 100000.0,
                "ordens": {"ordem-1": {"ticker": "PETR4.SA", "lado": "COMPRA"}},
                "posicoes": {"PETR4.SA": {"quantidade": 100, "preco_medio": 30.0}},
            }

            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(v1_data, f, indent=2)

            # Carrega e verifica migracao
            state = JsonFilePaperState(state_file)
            estado = state.carregar()

            # Dados foram preservados
            assert estado.version == 3
            assert estado.saldo == Decimal("50000")
            assert estado.saldo_inicial == Decimal("100000")
            assert "ordem-1" in estado.ordens
            assert estado.ordens["ordem-1"]["ticker"] == "PETR4.SA"
            assert "PETR4.SA" in estado.posicoes
            assert estado.posicoes["PETR4.SA"]["quantidade"] == 100

            # Verifica backup foi criado
            backup_file = state_file.with_suffix(".v1.bak")
            assert backup_file.exists()

    def test_salvar_atualiza_updated_at(self):
        """Teste: salvar atualiza updated_at."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"
            state = JsonFilePaperState(state_file)

            estado = state.carregar()
            # Modifica cashbook no formato correto
            estado.cashbook["entries"]["BRL"]["amount"] = "45000"
            state.salvar(estado)

            # Recarrega e verifica updated_at
            estado2 = state.carregar()
            assert estado2.saldo == Decimal("45000")
            assert estado2.updated_at != ""

    def test_resetar_estado(self):
        """Teste: resetar limpa o estado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"
            state = JsonFilePaperState(state_file)

            # Cria estado com dados
            estado = state.carregar()
            estado.cashbook["entries"]["BRL"]["amount"] = "30000"
            estado.ordens = {"ordem-1": {"ticker": "PETR4.SA"}}
            state.salvar(estado)

            # Reseta
            novo_estado = state.resetar(Decimal("50000"))

            assert novo_estado.saldo == Decimal("50000")
            assert novo_estado.saldo_inicial == Decimal("50000")
            assert novo_estado.ordens == {}
            assert novo_estado.posicoes == {}

    def test_multiplas_instancias_sem_stale_cache(self):
        """Teste: multiplas instancias nao tem stale cache."""
        # Este era o bug original: se broker e repository usav instancias
        # separadas de JsonFilePaperState, cada um lia a cache interno
        # e nao via changes do outro. Agora sempre le do disco.
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"

            # Instancia do broker
            broker_state = JsonFilePaperState(state_file)
            estado_broker = broker_state.carregar()
            # Modifica cashbook (saldo agora e property calculada)
            estado_broker.cashbook["entries"]["BRL"]["amount"] = "40000"
            estado_broker.ordens["ordem-1"] = {"ticker": "PETR4.SA"}
            broker_state.salvar(estado_broker)

            # Instancia separada do repository (simula DI do FastAPI)
            repo_state = JsonFilePaperState(state_file)
            estado_repo = repo_state.carregar()

            # Repository DEVE ver as mudancas do broker (nao stale cache)
            assert estado_repo.saldo == Decimal("40000")
            assert "ordem-1" in estado_repo.ordens

            # Repository faz suas mudancas
            estado_repo.portfolios["portfolio-1"] = {"nome": "Principal"}
            repo_state.salvar(estado_repo)

            # Broker recarrega e ve as mudancas do repository
            estado_broker = broker_state.carregar()
            assert "portfolio-1" in estado_broker.portfolios
            # E NAO perdeu as ordens
            assert "ordem-1" in estado_broker.ordens
            assert estado_broker.saldo == Decimal("40000")


class TestBrokerRepositoryNaoConflitam:
    """Teste: broker e repository nao conflitam no mesmo arquivo."""

    def test_broker_e_repository_compartilham_estado(self):
        """Teste: broker e repository compartilham estado sem sobrescrever dados."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"
            state = JsonFilePaperState(state_file)
            # Simula escrita do broker
            estado = state.carregar()
            # Modifica cashbook (saldo agora e property calculada)
            estado.cashbook["entries"]["BRL"]["amount"] = "40000"
            estado.ordens["ordem-1"] = {
                "id": "ordem-1",
                "ticker": "PETR4.SA",
                "lado": "COMPRA",
                "quantidade": 100,
            }
            state.salvar(estado)

            # Simula leitura do repository (portfolios preservados)
            estado2 = state.carregar()
            estado2.portfolios["portfolio-1"] = {
                "id": "portfolio-1",
                "nome": "Principal",
            }
            state.salvar(estado2)

            # Verifica que dados do broker foram preservados
            estado_final = state.carregar()
            assert estado_final.saldo == Decimal("40000")
            assert "ordem-1" in estado_final.ordens
            assert "portfolio-1" in estado_final.portfolios


class TestWriteAtomico:
    """Testes para write atomico (tmp + rename)."""

    def test_arquivo_tmp_nao_permanence_apos_sucesso(self):
        """Teste: arquivo .tmp e limpo apos salvar() bem-sucedido."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"
            state = JsonFilePaperState(state_file)

            estado = state.carregar()
            # Modifica cashbook no formato correto
            if "entries" not in estado.cashbook:
                estado.cashbook["entries"] = {}
            estado.cashbook["entries"]["BRL"] = {"amount": "50000", "conversion_rate": "1"}
            state.salvar(estado)

            # .tmp nao deve existir apos sucesso
            tmp_file = state_file.with_suffix(".tmp")
            assert not tmp_file.exists()

    def test_arquivo_original_preservado_se_escrita_falhar(self):
        """Teste: arquivo original permanece intacto se escrita do .tmp falhar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "paper_state.json"
            state = JsonFilePaperState(state_file)

            # Cria estado inicial
            estado = state.carregar()
            # Modifica cashbook no formato correto
            if "entries" not in estado.cashbook:
                estado.cashbook["entries"] = {}
            estado.cashbook["entries"]["BRL"] = {"amount": "80000", "conversion_rate": "1"}
            state.salvar(estado)

            # Salva estado original para comparar
            with open(state_file, "r", encoding="utf-8") as f:
                conteudo_original = f.read()

            # Mock json.dump para simular falha durante escrita do .tmp
            import builtins
            original_open = builtins.open
            falhou = False

            def mock_open_arquivo(path, *args, **kwargs):
                if ".tmp" in str(path):
                    # Simula falha ao abrir .tmp
                    raise IOError("Simulacao de falha de I/O")
                return original_open(path, *args, **kwargs)

            builtins.open = mock_open_arquivo
            try:
                state.salvar(PaperStateData(
                    cashbook={"base_currency": "BRL", "entries": {"BRL": {"amount": "99999", "conversion_rate": "1"}}}
                ))
            except IOError:
                falhou = True
            finally:
                builtins.open = original_open

            assert falhou, "Deveria ter falhado"
            # Arquivo original deve estar intacto
            with open(state_file, "r", encoding="utf-8") as f:
                conteudo_pos_falha = f.read()

            assert conteudo_original == conteudo_pos_falha
            # Saldo continua 80000, nao 99999
            estado_final = state.carregar()
            assert estado_final.saldo == Decimal("80000")
