# -*- coding: utf-8 -*-
"""
Adapter - Paper State com persistência em JSON.

Implementa PaperStatePort com:
- Migração automática v1 → v2
- Backup de arquivo v1 antes de migrar
- Schema unificado consolidando broker + repository
"""

import json
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from ...ports.paper_state_port import PaperStateData, PaperStatePort, PaperStateVersion


class JsonFilePaperState(PaperStatePort):
    """
    Implementação de PaperStatePort com persistência em arquivo JSON.

    Esta é a única fonte de verdade para o paper_state.json.
    Resolve conflitos entre JsonFilePaperBroker e JsonFilePortfolioRepository.

    NOTA: Não usa cache em memória para evitar stale reads quando múltiplas
    instâncias (broker, repository) acessam o mesmo arquivo. Sempre lê do disco.
    """

    DEFAULT_FILE = "paper_state.json"
    BACKUP_SUFFIX = ".v1.bak"

    def __init__(self, file_path: str | Path | None = None):
        self._file_path = Path(file_path) if file_path else Path(self.DEFAULT_FILE)

    def carregar(self) -> PaperStateData:
        """
        Carrega o estado do paper trading.

        - Se arquivo não existe, cria novo estado v3
        - Se existe em v1, migra para v2 → v3 com backup
        - Se existe em v2, migra para v3
        - Sempre lê do disco (sem cache) para evitar stale reads entre instâncias
        """
        if not self._file_path.exists():
            # Cria estado inicial v3
            estado = PaperStateData()
            self.salvar(estado)
            return estado

        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            version = data.get("version", PaperStateVersion.V1)

            if version < PaperStateVersion.CURRENT:
                # Migração em cadeia: v1 → v2 → v3
                if version < PaperStateVersion.V2:
                    data = self._migrar_v1_para_v2(data)
                if version < PaperStateVersion.V3:
                    data = self._migrar_v2_para_v3(data)

            return PaperStateData.from_dict(data)

        except (json.JSONDecodeError, KeyError, ValueError):
            # Arquivo corrompido, cria novo estado
            estado = PaperStateData()
            self.salvar(estado)
            return estado

    def _migrar_v1_para_v2(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migra schema v1 para v2.

        v1 broker: {saldo, saldo_inicial, ordens, posicoes}
        v1 repo: {portfolios, default_id}

        v2 unifica ambos em um único schema.
        """
        # Backup do arquivo original
        self._criar_backup_v1()

        # Merge dos dados existentes
        migrado = {
            "version": PaperStateVersion.V2,
            "updated_at": datetime.now().isoformat(),
            "saldo": data.get("saldo", 100000),
            "saldo_inicial": data.get("saldo_inicial", 100000),
            "ordens": data.get("ordens", {}),
            "posicoes": data.get("posicoes", {}),
            "portfolios": data.get("portfolios", {}),
            "default_id": data.get("default_id"),
        }

        # Salva estado migrado
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(migrado, f, indent=2, ensure_ascii=False)

        return migrado

    def _migrar_v2_para_v3(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migra schema v2 para v3.

        v2: {saldo, saldo_inicial, ordens, posicoes, portfolios}
        v3: {cashbook, base_currency, saldo_inicial, ordens, posicoes, portfolios}

        Migration: saldo → cashbook.entries["BRL"]
        """
        migrado = {
            "version": PaperStateVersion.V3,
            "updated_at": datetime.now().isoformat(),
            "saldo_inicial": data.get("saldo_inicial", 100000),
            "base_currency": "BRL",
            "cashbook": {
                "base_currency": "BRL",
                "entries": {
                    "BRL": {
                        "amount": str(data.get("saldo", "100000")),
                        "conversion_rate": "1"
                    }
                }
            },
            "ordens": data.get("ordens", {}),
            "posicoes": data.get("posicoes", {}),
            "portfolios": data.get("portfolios", {}),
            "default_id": data.get("default_id"),
        }

        # Salva estado migrado
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump(migrado, f, indent=2, ensure_ascii=False)

        return migrado

    def _criar_backup_v1(self) -> None:
        """Cria backup do arquivo v1 antes de migrar."""
        backup_path = self._file_path.with_suffix(self.BACKUP_SUFFIX)
        if self._file_path.exists() and not backup_path.exists():
            shutil.copy2(self._file_path, backup_path)

    def salvar(self, estado: PaperStateData) -> None:
        """
        Salva o estado no arquivo JSON com write atômico.

        Estratégia: escreve em .tmp, depois renomeia (atômico em POSIX e Windows).
        Evita corrupção se o processo morrer durante a escrita.

        Atualiza updated_at automaticamente.
        Não usa cache - sempre escreve no disco.
        """
        estado.updated_at = datetime.now().isoformat()

        # DEBUG: Mostra estado ANTES de salvar
        data_dict = estado.to_dict()
        print(f"[SALVAR] cashbook keys no dict: {list(data_dict['cashbook'].keys())}")
        print(f"[SALVAR] BRL amount: {data_dict['cashbook']['entries']['BRL']['amount']}")

        # Write atômico: tmp + rename
        tmp_path = self._file_path.with_suffix('.tmp')
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)

        # rename é atômico em POSIX e Windows (substitui o destino)
        tmp_path.replace(self._file_path)

        # DEBUG: Verifica se o arquivo foi salvo corretamente
        with open(self._file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            print(f"[SALVAR] arquivo salvo - cashbook keys: {list(saved_data['cashbook'].keys())}")
            if len(saved_data['cashbook']) > 2:
                print(f"[SALVAR] ⚠️  ARQUIVO CORROMPIDO APÓS SALVAR!")

    def resetar(self, saldo_inicial: Optional[Decimal] = None) -> PaperStateData:
        """
        Reseta o estado para valores iniciais.

        Args:
            saldo_inicial: Novo saldo inicial (opcional, padrão 100000)
        """
        novo_saldo = saldo_inicial if saldo_inicial is not None else Decimal("100000")
        estado = PaperStateData(
            saldo_inicial=novo_saldo,
            base_currency="BRL",
            cashbook={
                "base_currency": "BRL",
                "entries": {
                    "BRL": {"amount": str(novo_saldo), "conversion_rate": "1"}
                }
            },
        )
        self.salvar(estado)
        return estado
