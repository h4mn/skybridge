#!/usr/bin/env python3
"""
Teste de mock do Ralph Loop com simulação de sessões

Este teste simula o funcionamento do Ralph Loop incluindo:
- Captura de session_id via UserPromptSubmit hook
- Criação do arquivo de estado
- Simulação do Stop hook com diferentes sessões
- Verificação de isolamento entre sessões
"""

import os
import json
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
import uuid
from datetime import datetime


class RalphLoopMockSession:
    """Mock de uma sessão Claude Code com Ralph Loop"""

    def __init__(self, project_dir: Path, session_id: str, prompt: str,
                 max_iterations: int = 0, completion_promise: Optional[str] = None):
        self.project_dir = project_dir
        self.session_id = session_id
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.completion_promise = completion_promise
        self.state_file = project_dir / ".claude" / f"ralph-loop.{session_id}.md"
        self.cache_dir = project_dir / ".claude" / "cache"
        self.cache_file = self.cache_dir / "ralph-session-id.txt"

    def simulate_user_prompt_submit_hook(self):
        """Simula o UserPromptSubmit hook escrevendo session_id no cache"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(self.session_id)
        print(f"   ✅ UserPromptSubmit: session_id {self.session_id[:8]}* escrito no cache")

    def simulate_setup_script(self):
        """Simula o setup-ralph-loop.sh criando o arquivo de estado"""
        # Simular leitura do cache
        if not self.cache_file.exists():
            raise RuntimeError("Cache não existe - UserPromptSubmit hook não executou?")

        cached_session_id = self.cache_file.read_text().strip()
        if cached_session_id != self.session_id:
            raise RuntimeError(f"Session_id no cache não corresponde: {cached_session_id[:8]}* != {self.session_id[:8]}*")

        # Criar arquivo de estado
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        completion_promise_yaml = f'"{self.completion_promise}"' if self.completion_promise else "null"

        content = f"""---
active: true
iteration: 1
session_id: {self.session_id}
max_iterations: {self.max_iterations}
completion_promise: {completion_promise_yaml}
started_at: "{datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}
---

{self.prompt}
"""
        self.state_file.write_text(content)
        print(f"   ✅ Setup: arquivo criado {self.state_file.name}")

    def simulate_stop_hook(self, last_output: str = "") -> Dict:
        """
        Simula o stop-hook.sh

        Retorna:
            Dict com: decision, reason, systemMessage
        """
        if not self.state_file.exists():
            return {"decision": "allow", "reason": "No active loop"}

        # Ler frontmatter
        frontmatter = {}
        in_frontmatter = False
        for line in self.state_file.read_text().split('\n'):
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()

        iteration = int(frontmatter.get('iteration', '1'))
        max_iterations = int(frontmatter.get('max_iterations', '0'))
        completion_promise = frontmatter.get('completion_promise', 'null').strip('"')
        state_session = frontmatter.get('session_id', '')

        # Verificar isolamento de sessão
        if state_session and state_session != self.session_id:
            return {"decision": "allow", "reason": "Different session"}

        # Verificar max iterations
        if max_iterations > 0 and iteration >= max_iterations:
            print(f"   🛑 Max iterations ({max_iterations}) reached")
            self.state_file.unlink()
            return {"decision": "allow", "reason": "Max iterations reached"}

        # Verificar completion promise
        if completion_promise and completion_promise != "null":
            # Simular extração de <promise> tag
            if f"<promise>{completion_promise}</promise>" in last_output:
                print(f"   ✅ Completion promise detected: {completion_promise}")
                self.state_file.unlink()
                return {"decision": "allow", "reason": f"Promise: {completion_promise}"}

        # Continuar loop
        next_iteration = iteration + 1

        # Atualizar iteration no arquivo
        content = self.state_file.read_text()
        updated_content = content.replace(f"iteration: {iteration}", f"iteration: {next_iteration}")
        self.state_file.write_text(updated_content)

        # Extrair prompt
        prompt_lines = []
        skip = True
        for line in self.state_file.read_text().split('\n'):
            if line.strip() == '---' and skip:
                skip = False
                continue
            if not skip:
                prompt_lines.append(line)
        prompt_text = '\n'.join(prompt_lines).strip()

        if completion_promise and completion_promise != "null":
            system_msg = f"🔄 Ralph iteration {next_iteration} | To stop: output <promise>{completion_promise}</promise>"
        else:
            system_msg = f"🔄 Ralph iteration {next_iteration} | No completion promise set"

        return {
            "decision": "block",
            "reason": prompt_text,
            "systemMessage": system_msg
        }

    def cleanup(self):
        """Remove arquivos criados"""
        if self.state_file.exists():
            self.state_file.unlink()
        if self.cache_file.exists():
            self.cache_file.unlink()


def test_single_session_loop():
    """Teste 1: Loop básico de uma sessão"""
    print("\n📝 Teste 1: Loop básico de uma sessão")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        session_id = str(uuid.uuid4())

        session = RalphLoopMockSession(
            project_dir=project_dir,
            session_id=session_id,
            prompt="Testar o loop",
            max_iterations=3
        )

        # Simular setup
        session.simulate_user_prompt_submit_hook()
        session.simulate_setup_script()

        # Simular 2 iterações
        for i in range(2):
            result = session.simulate_stop_hook()
            if result["decision"] == "block":
                print(f"   Iteração {i+2}: {result['systemMessage']}")
            else:
                print(f"   ❌ Loop terminou cedo: {result['reason']}")
                return False

        # Terceira iteração deve atingir max_iterations
        result = session.simulate_stop_hook()
        if result["decision"] == "allow" and "Max iterations" in result["reason"]:
            print(f"   ✅ Loop completou após 3 iterações")
            return True
        else:
            print(f"   ❌ Loop não terminou corretamente")
            return False


def test_multi_session_isolation():
    """Teste 2: Isolamento entre múltiplas sessões"""
    print("\n📝 Teste 2: Isolamento entre múltiplas sessões")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Criar 2 sessões
        session_a = RalphLoopMockSession(
            project_dir=project_dir,
            session_id=str(uuid.uuid4()),
            prompt="Tarefa A",
            max_iterations=2
        )

        session_b = RalphLoopMockSession(
            project_dir=project_dir,
            session_id=str(uuid.uuid4()),
            prompt="Tarefa B",
            max_iterations=2
        )

        # Setup de ambas
        session_a.simulate_user_prompt_submit_hook()
        session_a.simulate_setup_script()
        session_b.simulate_user_prompt_submit_hook()
        session_b.simulate_setup_script()

        # Verificar que ambas criaram arquivos diferentes
        if session_a.state_file == session_b.state_file:
            print(f"   ❌ As sessões usaram o mesmo arquivo!")
            return False

        if not session_a.state_file.exists():
            print(f"   ❌ Arquivo da sessão A não existe")
            return False

        if not session_b.state_file.exists():
            print(f"   ❌ Arquivo da sessão B não existe")
            return False

        print(f"   ✅ Sessão A: {session_a.state_file.name}")
        print(f"   ✅ Sessão B: {session_b.state_file.name}")

        # Simular stop hook para cada sessão
        result_a = session_a.simulate_stop_hook()
        result_b = session_b.simulate_stop_hook()

        if result_a["decision"] != "block":
            print(f"   ❌ Sessão A não está bloqueando: {result_a['reason']}")
            return False

        if result_b["decision"] != "block":
            print(f"   ❌ Sessão B não está bloqueando: {result_b['reason']}")
            return False

        # Verificar que cada sessão tem seu próprio iteration
        state_a = session_a.state_file.read_text()
        state_b = session_b.state_file.read_text()

        iteration_a = int([line for line in state_a.split('\n') if 'iteration:' in line][0].split(':')[1].strip())
        iteration_b = int([line for line in state_b.split('\n') if 'iteration:' in line][0].split(':')[1].strip())

        if iteration_a != 2:
            print(f"   ❌ Iteração da sessão A incorreta: {iteration_a}")
            return False

        if iteration_b != 2:
            print(f"   ❌ Iteração da sessão B incorreta: {iteration_b}")
            return False

        print(f"   ✅ Iterações independentes: A={iteration_a}, B={iteration_b}")
        return True


def test_completion_promise():
    """Teste 3: Completion promise termina o loop"""
    print("\n📝 Teste 3: Completion promise")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        session_id = str(uuid.uuid4())

        session = RalphLoopMockSession(
            project_dir=project_dir,
            session_id=session_id,
            prompt="Criar uma API REST",
            completion_promise="API PRONTA"
        )

        session.simulate_user_prompt_submit_hook()
        session.simulate_setup_script()

        # Primeira iteração - sem promise
        result = session.simulate_stop_hook(last_output="Trabalhando na API...")
        if result["decision"] != "block":
            print(f"   ❌ Loop terminou sem promise")
            return False

        # Segunda iteração - com promise
        result = session.simulate_stop_hook(last_output="A API está pronta! <promise>API PRONTA</promise>")
        if result["decision"] != "allow":
            print(f"   ❌ Loop não terminou com promise")
            return False

        # Verificar que arquivo foi removido
        if session.state_file.exists():
            print(f"   ❌ Arquivo não foi removido após completion")
            return False

        print(f"   ✅ Loop terminou com completion promise")
        return True


def test_wrong_session_doesnt_block():
    """Teste 4: Sessão errada não bloqueia"""
    print("\n📝 Teste 4: Sessão errada não bloqueia")

    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Sessão A cria o loop
        session_a = RalphLoopMockSession(
            project_dir=project_dir,
            session_id=str(uuid.uuid4()),
            prompt="Tarefa A"
        )
        session_a.simulate_user_prompt_submit_hook()
        session_a.simulate_setup_script()

        # Sessão B tenta executar stop hook
        session_b_wrong = RalphLoopMockSession(
            project_dir=project_dir,
            session_id=str(uuid.uuid4()),  # Session_id diferente!
            prompt="Tarefa B"
        )

        # O stop hook da sessão B não deve bloquear porque o arquivo pertence à A
        result = session_b_wrong.simulate_stop_hook()

        if result["decision"] != "allow":
            print(f"   ❌ Sessão B bloqueou erroneamente")
            return False

        if "Different session" not in result["reason"]:
            print(f"   ❌ Razão incorreta: {result['reason']}")
            return False

        print(f"   ✅ Sessão B não bloqueou (arquivo pertence à A)")
        return True


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 Ralph Loop - Testes de Mock com Sessões")
    print("=" * 60)

    tests = [
        ("Loop básico de uma sessão", test_single_session_loop),
        ("Isolamento entre múltiplas sessões", test_multi_session_isolation),
        ("Completion promise", test_completion_promise),
        ("Sessão errada não bloqueia", test_wrong_session_doesnt_block),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Erro no teste '{name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")

    print(f"\n🎯 Total: {passed}/{total} testes passaram")

    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        return 1


if __name__ == "__main__":
    exit(main())
