#!/usr/bin/env python3
"""
Track Orchestrator - Executa lógica /track sem raciocínio LLM.

Elimina bottleneck de raciocínio intermediário.
Script decide e executa; skill só formata output.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

STATE_FILE = Path(__file__).parent / "data" / "state.json"
EVENTS_LOG = Path(__file__).parent / "data" / "events.log"

# Cache de projects
PROJECT_CACHE = {
    "skybridge": 219139925,
    "skybridge-core": 219139925,
    "sky": 219139932,
    "agentic": 219139997,
}
WORKSPACE_ID = 20989145


def load_state():
    """Carrega estado local (último timer, contexto)."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    """Salva estado local."""
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_event(event_type, message):
    """Registra evento no log para debug."""
    timestamp = datetime.now().isoformat()
    log_line = f"{timestamp} | {event_type} | {message}\n"

    EVENTS_LOG.parent.mkdir(exist_ok=True)
    with open(EVENTS_LOG, "a", encoding="utf-8") as f:
        f.write(log_line)


def get_project_id(project_name):
    """Retorna project ID do cache ou None se não encontrado."""
    return PROJECT_CACHE.get(project_name)


def should_resume():
    """Decide se deve retomar último timer baseado em tempo parado."""
    state = load_state()
    if not state or "last_stop" not in state:
        return False, None

    last_stop = datetime.fromisoformat(state["last_stop"])
    stopped_duration = datetime.now() - last_stop

    # Se parado há > 10min E trabalhou ≥ 50min (3000s): retoma
    last_duration_seconds = state.get("last_duration", 0)
    if stopped_duration > timedelta(minutes=10) and last_duration_seconds >= 3000:
        return True, state.get("last_timer")

    return False, None


def cmd_status():
    """Reporta status atual."""
    state = load_state()
    return {
        "action": "report",
        "running": state.get("running", False),
        "context": state.get("context", {})
    }


def cmd_resume(toggl_is_running=None, optimistic=False):
    """
    Retoma último timer se conditions met.
    Se toggl_is_running for fornecido, verifica consistência primeiro.
    Se optimistic=True, retorna start_otimista (timer iniciado primeiro, verify depois).
    """
    # Optimistic mode: retornar ação otimista
    if optimistic:
        should, last_timer = should_resume()
        if not should:
            return {"action": "wait", "message": "Break não terminou ou ciclo incompleto"}

        project = last_timer.get("project", "skybridge")
        return {
            "action": "start_optimistic",
            "mode": "optimistic",
            "project": project,
            "project_id": get_project_id(project),
            "tags": last_timer.get("tags", ["skybridge"]),
            "description": last_timer.get("description", "Trabalho"),
            "workspace_id": WORKSPACE_ID,
            "verify_after": True,
            "rollback_on_error": True
        }

    # Se fornecido status do Toggl, verificar auto-restart
    if toggl_is_running is not None:
        restart_action = consistency_check(toggl_is_running)
        if restart_action:
            return restart_action

    should, last_timer = should_resume()
    if not should:
        return {"action": "wait", "message": "Break não terminou ou ciclo incompleto"}

    project = last_timer.get("project", "skybridge")
    return {
        "action": "start",
        "project": project,
        "project_id": get_project_id(project),
        "tags": last_timer.get("tags", ["skybridge"]),
        "description": last_timer.get("description", "Trabalho"),
        "workspace_id": WORKSPACE_ID
    }


def consistency_check(toggl_is_running):
    """
    Verifica consistência entre estado local e realidade do Toggl.
    Retorna ação de auto-restart se detectar parada inesperada.
    """
    state = load_state()

    # Se state diz que está rodando mas Toggl diz que não: auto-restart
    if state.get("running", False) and not toggl_is_running:
        log_event("auto_restart", "Timer parado inesperadamente, reiniciado")
        project = state.get("last_timer", {}).get("project", "skybridge")
        return {
            "action": "auto_restart",
            "reason": "Timer parado inesperadamente (possível conflito Desktop/Chrome)",
            "project": project,
            "project_id": get_project_id(project),
            "tags": state.get("last_timer", {}).get("tags", ["skybridge"]),
            "description": state.get("last_timer", {}).get("description", "Trabalho"),
            "workspace_id": WORKSPACE_ID
        }

    return None


def cmd_start(toggl_is_running=None, optimistic=False):
    """
    Inicia novo timer inferido do contexto.
    Se toggl_is_running for fornecido, verifica consistência primeiro.
    Se optimistic=True, retorna start_otimista (timer iniciado primeiro, verify depois).
    """
    # Optimistic mode: retornar ação otimista
    if optimistic:
        project = "skybridge"
        return {
            "action": "start_optimistic",
            "mode": "optimistic",
            "project": project,
            "project_id": get_project_id(project),
            "tags": ["skybridge"],
            "description": "Trabalho",
            "workspace_id": WORKSPACE_ID,
            "verify_after": True,
            "rollback_on_error": True
        }

    # Se fornecido status do Toggl, verificar auto-restart
    if toggl_is_running is not None:
        restart_action = consistency_check(toggl_is_running)
        if restart_action:
            return restart_action

    project = "skybridge"
    return {
        "action": "start",
        "project": project,
        "project_id": get_project_id(project),
        "tags": ["skybridge"],
        "description": "Trabalho",
        "workspace_id": WORKSPACE_ID
    }


def cmd_start_optimistic():
    """
    Optimistic start: retorna ação imediata para perceived performance.
    Verificações ocorrem em background via skill.

    Retorno indica que skill deve iniciar timer PRIMEIRO, depois verificar.
    """
    state = load_state()
    project = state.get("last_timer", {}).get("project", "skybridge")

    return {
        "action": "start_optimistic",
        "mode": "optimistic",
        "project": project,
        "project_id": get_project_id(project),
        "tags": state.get("last_timer", {}).get("tags", ["skybridge"]),
        "description": state.get("last_timer", {}).get("description", "Trabalho"),
        "workspace_id": WORKSPACE_ID,
        "verify_after": True,  # Skill deve verificar após iniciar
        "rollback_on_error": True  # Se verify falhar, parar timer
    }


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    # Parse --toggl-running flag
    toggl_is_running = None
    if "--toggl-running" in sys.argv:
        idx = sys.argv.index("--toggl-running")
        if idx + 1 < len(sys.argv):
            toggl_is_running = sys.argv[idx + 1].lower() == "true"

    # Parse --optimistic flag
    optimistic = "--optimistic" in sys.argv

    if cmd == "status":
        result = cmd_status()
    elif cmd == "resume":
        result = cmd_resume(toggl_is_running, optimistic=optimistic)
    elif cmd == "start":
        result = cmd_start(toggl_is_running, optimistic=optimistic)
    elif cmd == "start-optimistic":
        result = cmd_start_optimistic()
    else:
        result = {"error": f"Comando desconhecido: {cmd}"}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
