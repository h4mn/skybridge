#!/usr/bin/env python3
"""Setup do State Repository YouTube.

Configura o schema SQLite para persistência de estado do YouTube Copilot.

Uso:
    python -m scripts.setup_youtube_state
    python scripts/setup_youtube_state.py
    sb youtube setup
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.youtube.infrastructure.youtube_state_setup import (
    setup_youtube_state,
    verify_youtube_state,
    get_youtube_state_path
)


def main():
    """Setup do YouTube State Repository."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Setup do YouTube State Repository"
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Caminho para o banco SQLite (padrão: data/youtube_copilot.db)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recria tabelas (PERDE DADOS)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Apenas verifica o estado atual"
    )

    args = parser.parse_args()

    # Determinar caminho do banco
    db_path = args.db_path or get_youtube_state_path()

    print(f"🔧 YouTube State Repository")
    print(f"   Caminho: {db_path}")

    if args.verify:
        # Apenas verificar
        print(f"\n🔍 Verificando estado atual...")
        status = verify_youtube_state(db_path)

        if not status["exists"]:
            print(f"❌ Banco não existe: {db_path}")
            return 1

        if status.get("error"):
            print(f"❌ Erro: {status['error']}")
            return 1

        print(f"✅ Estado válido!")
        print(f"   Tabelas: {', '.join(status['tables'])}")
        print(f"   Vídeos: {status.get('video_count', 0)}")
        print(f"   Playlists: {status.get('playlist_count', 0)}")
        return 0

    # Setup
    if args.force:
        print(f"⚠️  Modo FORCE: tabelas serão recriadas!")
        response = input("Continuar? (s/N): ")
        if response.lower() != 's':
            print("❌ Cancelado")
            return 1

    print(f"\n🔧 Configurando schema...")
    setup_youtube_state(db_path, force_recreate=args.force)

    # Verificar
    print(f"\n🔍 Verificando...")
    status = verify_youtube_state(db_path)

    if status.get("error"):
        print(f"❌ Erro na verificação: {status['error']}")
        return 1

    print(f"✅ Setup concluído com sucesso!")
    print(f"   Tabelas: {', '.join(status['tables'])}")
    print(f"   Vídeos: {status.get('video_count', 0)}")
    print(f"   Playlists: {status.get('playlist_count', 0)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
