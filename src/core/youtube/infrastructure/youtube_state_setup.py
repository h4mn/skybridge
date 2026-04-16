"""Setup do State Repository YouTube.

Cria e inicializa o schema SQLite para persistência de estado.
Uso:
    from core.youtube.infrastructure.youtube_state_setup import setup_youtube_state

    # Setup com caminho padrão
    setup_youtube_state()

    # Setup com caminho customizado
    setup_youtube_state(db_path="custom/path/youtube.db")
"""

from pathlib import Path
from typing import Optional
import sqlite3


def setup_youtube_state(
    db_path: str = "data/youtube_copilot.db",
    force_recreate: bool = False
) -> None:
    """
    Configura o schema do State Repository YouTube.

    Cria as tabelas necessárias se não existirem.
    Idempotente: pode ser chamado múltiplas vezes.

    Args:
        db_path: Caminho para o arquivo SQLite
        force_recreate: Se True, recria tabelas (CUIDADO: perde dados)
    """
    # Criar diretório se não existe
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # Conectar ao banco
    conn = sqlite3.connect(db_path)

    try:
        # Schema da tabela video_state
        video_state_schema = """
            CREATE TABLE IF NOT EXISTS video_state (
                video_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                channel TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                playlist_id TEXT NOT NULL,
                added_at TIMESTAMP,
                synced_at TIMESTAMP,
                notified_at TIMESTAMP,
                transcribed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                thumbnail TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_video_playlist
                ON video_state(playlist_id);

            CREATE INDEX IF NOT EXISTS idx_video_status
                ON video_state(status);

            CREATE INDEX IF NOT EXISTS idx_video_notified
                ON video_state(notified_at) WHERE notified_at IS NULL;
        """

        # Schema da tabela playlist_sync
        playlist_sync_schema = """
            CREATE TABLE IF NOT EXISTS playlist_sync (
                playlist_id TEXT PRIMARY KEY,
                last_sync_at TIMESTAMP NOT NULL,
                total_videos INTEGER NOT NULL,
                new_videos_found INTEGER DEFAULT 0,
                error_message TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """

        # Executar schemas
        if force_recreate:
            # Recriar tabelas
            conn.execute("DROP TABLE IF EXISTS video_state")
            conn.execute("DROP TABLE IF EXISTS playlist_sync")

        conn.executescript(video_state_schema)
        conn.executescript(playlist_sync_schema)

        # Commit das mudanças
        conn.commit()

        print(f"✅ YouTube State Repository configurado: {db_path}")
        print(f"   Tabelas criadas: video_state, playlist_sync")

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erro ao setup YouTube State Repository: {e}")
    finally:
        conn.close()


def verify_youtube_state(
    db_path: str = "data/youtube_copilot.db"
) -> dict:
    """
    Verifica se o schema está configurado corretamente.

    Args:
        db_path: Caminho para o arquivo SQLite

    Returns:
        Dict com status da verificação
    """
    if not Path(db_path).exists():
        return {
            "exists": False,
            "tables": [],
            "error": "Banco de dados não existe"
        }

    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.cursor()

        # Verificar tabelas
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]

        # Verificar se tabelas esperadas existem
        expected_tables = {"video_state", "playlist_sync"}
        missing_tables = expected_tables - set(tables)

        if missing_tables:
            return {
                "exists": True,
                "tables": tables,
                "error": f"Tabelas faltando: {missing_tables}"
            }

        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM video_state")
        video_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM playlist_sync")
        playlist_count = cursor.fetchone()[0]

        return {
            "exists": True,
            "tables": tables,
            "video_count": video_count,
            "playlist_count": playlist_count,
            "status": "ok"
        }

    except Exception as e:
        return {
            "exists": True,
            "tables": [],
            "error": str(e)
        }
    finally:
        conn.close()


def get_youtube_state_path(
    env_var: str = "YOUTUBE_STATE_DB",
    default: str = "data/youtube_copilot.db"
) -> str:
    """
    Retorna o caminho do banco de dados de estado YouTube.

    Args:
        env_var: Variável de ambiente a verificar
        default: Caminho padrão se não definido

    Returns:
        Caminho do banco de dados
    """
    import os
    return os.getenv(env_var, default)


if __name__ == "__main__":
    """Setup direto via python -m."""
    import sys

    db_path = get_youtube_state_path()

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print(f"🔧 Configurando YouTube State Repository...")
    print(f"   Caminho: {db_path}")

    setup_youtube_state(db_path)

    # Verificar setup
    print(f"\n🔍 Verificando setup...")
    status = verify_youtube_state(db_path)

    if status.get("error"):
        print(f"❌ Erro: {status['error']}")
        sys.exit(1)

    print(f"✅ Setup verificado com sucesso!")
    print(f"   Vídeos: {status.get('video_count', 0)}")
    print(f"   Playlists: {status.get('playlist_count', 0)}")
