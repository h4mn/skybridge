# -*- coding: utf-8 -*-
"""
DragonflyDB Windows Launcher - Inicia dragonfly.exe nativo com log streaming.

Uso:
    python scripts/dragonfly_windows.py start
    python scripts/dragonfly_windows.py stop
    python scripts/dragonfly_windows.py logs
"""

import subprocess
import sys
import time
from pathlib import Path

# Configurações
DRAGONFLY_EXE = Path("./bin/dragonfly.exe")
DRAGONFLY_HOST = "localhost"
DRAGONFLY_PORT = 6379
DRAGONFLY_DIR = "./data/dragonfly"

PID_FILE = Path("./data/dragonfly.pid")
LOG_FILE = Path("./logs/dragonfly.log")


def start_dragonfly() -> bool:
    """Inicia DragonflyDB nativo em background."""
    print("[INFO] Iniciando DragonflyDB nativo...")

    # Validar executável
    if not DRAGONFLY_EXE.exists():
        print(f"[ERROR] Executável não encontrado: {DRAGONFLY_EXE}")
        print("\nDicas:")
        print("  1. Baixe dragonfly.exe de https://dragonflydb.io/releases")
        print("  2. Coloque em ./bin/dragonfly.exe")
        return False

    # Criar diretórios
    Path(DRAGONFLY_DIR).mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(parents=True, exist_ok=True)

    # Comando para iniciar DragonflyDB
    # --cli: Modo CLI com logs em stdout
    # --log-level debug: Logs detalhados
    cmd = [
        str(DRAGONFLY_EXE),
        "--cli",
        "--log-level", "debug",
        "--dir", DRAGONFLY_DIR,
        "--port", str(DRAGONFLY_PORT),
    ]

    # Iniciar processo em background
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,  # Line buffered
    )

    # Salvar PID
    PID_FILE.write_text(str(process.pid), encoding="utf-8")

    # Stream logs para arquivo e console
    with open(LOG_FILE, "w", encoding="utf-8") as log_f:
        print(f"[INFO] DragonflyDB iniciado (PID: {process.pid})")
        print(f"[INFO] Logs: {LOG_FILE}")
        print("[INFO] Aguardando startup...")

        # Aguardar confirmação de startup
        started = False
        for line in process.stdout:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {line.rstrip()}"
            print(log_line)
            log_f.write(log_line + "\n")
            log_f.flush()

            if not started and ("ready" in line.lower() or "listening" in line.lower() or "started" in line.lower()):
                started = True
                print("[INFO] DragonflyDB pronto!")
                print(f"[INFO] Conexão: redis-cli -h {DRAGONFLY_HOST} -p {DRAGONFLY_PORT}")
                break

        # Continuar streaming em background (thread separada em produção)

    return True


def stop_dragonfly() -> bool:
    """Para DragonflyDB."""
    if not PID_FILE.exists():
        print("[WARN] DragonflyDB não está rodando (sem PID file)")
        return False

    pid = int(PID_FILE.read_text(encoding="utf-8"))
    print(f"[INFO] Parando DragonflyDB (PID: {pid})...")

    try:
        # Windows usa taskkill para terminar processos
        result = subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            text=True,
        )
        PID_FILE.unlink(missing_ok=True)

        if result.returncode == 0:
            print("[INFO] DragonflyDB parado")
            return True
        else:
            print(f"[WARN] taskkill retornou: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] Falha ao parar: {e}")
        return False


def tail_logs() -> None:
    """Mostra logs em tempo real."""
    if not LOG_FILE.exists():
        print("[WARN] Arquivo de log não encontrado")
        return

    print(f"[INFO] Mostrando logs: {LOG_FILE}")
    print("[INFO] Ctrl+C para sair\n")

    # PowerShell Get-Content com -Wait para tail nativo do Windows
    cmd = ["powershell", "-Command", f"Get-Content {LOG_FILE} -Wait"]

    process = subprocess.Popen(
        cmd,
        universal_newlines=True,
    )

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n[INFO] Saindo...")
        process.terminate()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python dragonfly_windows.py [start|stop|logs]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        success = start_dragonfly()
        sys.exit(0 if success else 1)
    elif command == "stop":
        stop_dragonfly()
    elif command == "logs":
        tail_logs()
    else:
        print(f"Comando inválido: {command}")
        sys.exit(1)
