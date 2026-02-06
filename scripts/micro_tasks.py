#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerenciador de Micro-Tarefas Skybridge.

Script interativo para escolher tarefas rápidas (5-15 min)
durante intervalos de desenvolvimento.

Uso:
    python scripts/micro_tasks.py

Modos:
    -l, --list    Lista todas as tarefas disponíveis
    -r, --random  Escolhe tarefa aleatória
    -c, --category Escolhe tarefa de categoria específica
    -s, --stats  Mostra estatísticas
"""

import random
import argparse
from pathlib import Path
from typing import Optional

# Arquivo de micro-tarefas
MICRO_TASKS_FILE = Path("docs/MICRO_TASKS.md")


class MicroTaskManager:
    """Gerenciador de micro-tarefas."""

    def __init__(self, tasks_file: Path = MICRO_TASKS_FILE):
        """Inicializa gerenciador."""
        self.tasks_file = tasks_file
        self.tasks = self._parse_tasks()

    def _parse_tasks(self) -> list[dict]:
        """Parse tarefas do arquivo markdown."""
        tasks = []
        current_category = None
        current_subsection = None

        content = self.tasks_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        for line in lines:
            line = line.strip()

            # Categorias principais (##)
            if line.startswith("## "):
                current_category = line.replace("## ", "").split("(")[0].strip()
                current_subsection = None

            # Subseções (###)
            elif line.startswith("### "):
                current_subsection = line.replace("### ", "").split("(")[0].strip()

            # Tarefas (checkboxes)
            elif line.startswith("- [ ] ") or line.startswith("- [x] "):
                is_done = "[x]" in line
                task_text = line.replace("- [ ] ", "").replace("- [x] ", "")
                # Remove markdown links se houver
                if "`" in task_text:
                    task_text = task_text.split("`")[1] if "`" in task_text else task_text

                tasks.append({
                    "category": current_category,
                    "subsection": current_subsection,
                    "task": task_text.strip(),
                    "done": is_done,
                    "line": line
                })

        return tasks

    def list_tasks(
        self,
        category: Optional[str] = None,
        show_done: bool = False,
        limit: int = 10
    ) -> list[dict]:
        """
        Lista tarefas disponíveis.

        Args:
            category: Filtrar por categoria
            show_done: Incluir tarefas completadas
            limit: Máximo de tarefas a retornar

        Returns:
            Lista de tarefas
        """
        tasks = [t for t in self.tasks if not t["done"] or show_done]

        if category:
            tasks = [t for t in tasks if category.lower() in t["category"].lower()]

        return tasks[:limit]

    def random_task(self, category: Optional[str] = None) -> Optional[dict]:
        """
        Escolhe tarefa aleatória.

        Args:
            category: Filtrar por categoria

        Returns:
            Tarefa aleatória ou None
        """
        tasks = self.list_tasks(category=category)

        if not tasks:
            return None

        return random.choice(tasks)

    def get_stats(self) -> dict:
        """
        Retorna estatísticas das tarefas.

        Returns:
            Dict com contagem por categoria
        """
        categories = {}
        for task in self.tasks:
            cat = task["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "done": 0}
            categories[cat]["total"] += 1
            if task["done"]:
                categories[cat]["done"] += 1

        total_tasks = len(self.tasks)
        total_done = sum(cat["done"] for cat in categories.values())

        return {
            "categories": categories,
            "total": total_tasks,
            "done": total_done,
            "pending": total_tasks - total_done,
            "completion_rate": f"{(total_done/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
        }


def print_task(task: dict, show_index: bool = False, index: int = 0):
    """Imprime tarefa formatada."""
    if show_index:
        print(f"{index}. ", end="")

    cat = task["category"]
    sub = task["subsection"]
    task_text = task["task"]

    # Emojis por categoria
    emojis = {
        "⚡ Quick Wins": "⚡",
        "🔍 Exploração Skybridge": "🔍",
        "🧹 Limpeza Técnica": "🧹",
        "📚 Aprendizado Rápido": "📚",
        "🐛 Debugging Leve": "🐛",
        "📝 Planejamento": "📝",
        "🎮 Micro-Projetos": "🎮",
        "🎲 Aleatório": "🎲"
    }

    emoji = emojis.get(cat, "📌")

    print(f"{emoji} **{cat}**")
    if sub:
        print(f"   ↳ {sub}")
    print(f"   ↳ {task_text}")
    print()


def main():
    """Ponto de entrada."""
    parser = argparse.ArgumentParser(
        description="Gerenciador de Micro-Tarefas Skybridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
╔════════════════════════════════════════════════════════════════════════════╗
║                        EXEMPLOS DE USO                                    ║
╚════════════════════════════════════════════════════════════════════════════╝
  Tarefa aleatória:
    python scripts/micro_tasks.py -r

  Tarefa de categoria específica:
    python scripts/micro_tasks.py -c "Quick Wins"
    python scripts/micro_tasks.py -c "Exploração Skybridge"

  Listar todas as tarefas disponíveis:
    python scripts/micro_tasks.py -l

  Ver estatísticas:
    python scripts/micro_tasks.py -s

  Mostrar esta mensagem de ajuda:
    python scripts/micro_tasks.py -h
    python scripts/micro_tasks.py --help

╔════════════════════════════════════════════════════════════════════════════╝
                        CATEGORIAS DISPONÍVEIS
  ⚡ Quick Wins           - Tarefas rápidas (5 min) com dopamina imediata
  🔍 Exploração Skybridge - Aprenda algo novo do código (10-15 min)
  🧹 Limpeza Técnica      - Pague dívida técnica de forma segura (15 min)
  📚 Aprendizado Rápido    - Melhore habilidades (tutoriais, artigos)
  🐛 Debugging Leve        - Investigue issues sem pressão (10-15 min)
  📝 Planejamento         - Prepare a próxima sessão de coding (10 min)
  🎮 Micro-Projetos        - Projetinhos maiores (30-60 min)
  🎲 Aleatório            - Escolha aleatória quando não souber o que fazer

╔════════════════════════════════════════════════════════════════════════════╝
                        DICAS DE OURO
  ⏱️  Respeite o tempo limite (5-15 min)
  🚀 Não interrompa deep work se estiver produtivo
  📝 Capture output: sempre anote o que aprendeu/fez
  💡 Divida em partes se tarefa levar >15 min
  🎯 Seja gentil: não critique código alheio em micro-tarefas
  😄 Divirta-se: micro-tarefas devem ser LEVES, não estressantes

                        ARQUIVOS
  docs/MICRO_TASKS.md - Documentação completa do sistema
  scripts/micro_tasks.py - Este script
        """
    )

    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="Lista tarefas disponíveis"
    )
    parser.add_argument(
        "-r", "--random",
        action="store_true",
        help="Escolhe tarefa aleatória"
    )
    parser.add_argument(
        "-c", "--category",
        type=str,
        help="Filtrar por categoria (ex: 'Quick Wins', 'Exploração')"
    )
    parser.add_argument(
        "-s", "--stats",
        action="store_true",
        help="Mostra estatísticas"
    )

    args = parser.parse_args()

    # Cria gerenciador
    manager = MicroTaskManager()

    # Modo: Stats
    if args.stats:
        stats = manager.get_stats()
        print("\n📊 Estatísticas das Micro-Tarefas:\n")

        for cat, data in stats["categories"].items():
            done = data["done"]
            total = data["total"]
            rate = f"{(done/total*100):.0f}%" if total > 0 else "0%"
            print(f"{cat}: {done}/{total} ({rate})")

        print(f"\nTotal: {stats['done']} concluídas de {stats['total']}")
        print(f"Pending: {stats['pending']}")
        print(f"Taxa de conclusão: {stats['completion_rate']}")
        return

    # Modo: List
    if args.list:
        category = args.category
        tasks = manager.list_tasks(category=category, show_done=False, limit=20)

        print(f"\n📋 Micro-Tarefas Disponíveis")
        if category:
            print(f"   Categoria: {category}")
        print(f"   Total: {len(manager.list_tasks(category=category, show_done=True))}\n")

        for i, task in enumerate(tasks, 1):
            print_task(task, show_index=True, index=i)

        if not tasks:
            print("   (nenhuma tarefa encontrada)")
        return

    # Modo: Random
    task = manager.random_task(category=args.category)

    if task:
        print("\n🎲 Micro-Tarefa Aleatória para Você:\n")
        print_task(task)
        print(f"⏱️  Tempo estimado: 5-15 min")
        print(f"💡 Dica: Divida em partes se levar >15 min")
    else:
        category_msg = f" (categoria: {args.category})" if args.category else ""
        print(f"\n❌ Nenhuma tarefa disponível{category_msg}")
        print("💡 Tente 'python scripts/micro_tasks.py -l' para ver todas as opções")


if __name__ == "__main__":
    main()
