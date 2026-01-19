#!/usr/bin/env python3
"""
Skybridge Changelog Generator

Gera CHANGELOG.md no formato Sky (PT-BR, emojis, links ricos, sem "No changes").

Uso:
    python -m runtime.changelog [since_tag]

Exemplo:
    python -m runtime.changelog v0.5.3  # Gera changelog desde v0.5.3
    python -m runtime.changelog           # Usa a última tag automaticamente

> "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky 📚
"""

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Commit:
    """Representa um commit Git."""
    hash: str
    short_hash: str
    subject: str
    type: str
    scope: Optional[str]
    author_name: str
    author_email: str
    pr_number: Optional[str] = None

    @property
    def author(self) -> str:
        """Retorna o username do GitHub a partir do email."""
        if "@" in self.author_email:
            # Extrair username antes do @
            username = self.author_email.split("@")[0]
            # Lidar com emails do GitHub como: 670202+h4mn@users.noreply.github.com
            if "+" in username:
                return username.split("+")[1]
            # Lidar com noreply emails
            if username.startswith("noreply"):
                return self.author_name.lower().replace(" ", "").replace(".", "")
            return username
        return self.author_name.lower().replace(" ", "").replace(".", "")

    def format_entry(self) -> str:
        """Formata commit no formato Sky."""
        pr_part = f" ([#{self.pr_number}](https://github.com/h4mn/skybridge/pull/{self.pr_number}))" if self.pr_number else ""
        scope_part = f"**{self.scope}:** " if self.scope else ""
        return (
            f"* [`{self.short_hash}`](https://github.com/h4mn/skybridge/commit/{self.hash}) "
            f"{scope_part}{self.subject}{pr_part} [`@{self.author}`](https://github.com/{self.author})"
        )


# Mapeamento de tipos para seções com emojis (ordem do CHANGELOG manual)
SECTIONS = {
    "feat": "✨ Novidades",
    "fix": "🐛 Correções",
    "refactor": "♻️ Refatoração",
    "docs": "📚 Documentação",
    "style": "💅 Estilos",
    "perf": "⚡ Performance",
    "test": "✅ Testes",
    "build": "📦 Build",
    "ci": "👷 CI",
    "chore": "🧹 Tarefas",
    "revert": "⏪ Reverter",
}


def get_latest_tag() -> str:
    """Retorna a última tag do repositório."""
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def get_commits_since(tag: Optional[str] = None) -> list[Commit]:
    """
    Retorna todos os commits desde a tag especificada.

    Args:
        tag: Tag base. Se None, usa a última tag.
    """
    if tag is None:
        tag = get_latest_tag()

    # Buscar commits no formato: hash|subject|author_name|author_email
    # Forçar UTF-8 para evitar mojibake no Windows
    env = {"GIT_LOG_OUTPUT_ENCODING": "utf-8"}
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "log",
            f"{tag}..HEAD",
            "--format=%H|%s|%an|%ae"
        ],
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
        env={**subprocess.os.environ, **env}
    )

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue

        parts = line.split("|")
        if len(parts) != 4:
            continue

        full_hash, subject, author_name, author_email = parts
        short_hash = full_hash[:7]

        # Pular commits de release e changelog
        if subject.startswith("chore(release):") or subject.startswith("docs(release):"):
            continue

        # Parse conventional commit
        match = re.match(r"^(\w+)(?:\(([^)]+)\))?:?\s*(.*)$", subject)
        if not match:
            continue

        commit_type, scope, clean_subject = match.groups()
        if commit_type not in SECTIONS:
            continue

        # Extrair número da PR do subject (ex: "#50")
        pr_match = re.search(r"#(\d+)", subject)
        pr_number = pr_match.group(1) if pr_match else None

        commits.append(Commit(
            hash=full_hash,
            short_hash=short_hash,
            subject=clean_subject,
            type=commit_type,
            scope=scope,
            author_name=author_name,
            author_email=author_email,
            pr_number=pr_number
        ))

    return commits


def generate_changelog(commits: list[Commit]) -> str:
    """Gera o conteúdo do changelog no formato Sky, agrupado por PR."""
    # Agrupar commits por (tipo, PR) para mostrar commits da mesma PR juntos
    grouped: dict[tuple[str, Optional[str]], list[Commit]] = {}

    for commit in commits:
        key = (commit.type, commit.pr_number)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(commit)

    # Gerar seções organizadas
    sections_text = []

    # Ordem dos tipos de commit
    type_order = ["feat", "fix", "refactor", "docs", "style", "perf", "test", "build", "ci", "chore", "revert"]

    for commit_type in type_order:
        # Encontrar todas as PRs/commits deste tipo
        type_groups = [(pr, commits_list) for (t, pr), commits_list in grouped.items() if t == commit_type]

        if not type_groups:
            continue

        section_name = SECTIONS[commit_type]
        sections_text.append(f"\n### {section_name}\n")

        # Para cada PR ou commit individual deste tipo
        for pr_number, commits_list in type_groups:
            if pr_number and len(commits_list) > 1:
                # Múltiplos commits da mesma PR - agrupar
                sections_text.append(f"\n**#{pr_number}** - {commits_list[0].subject[:60]}{'...' if len(commits_list[0].subject) > 60 else ''}\n")
                for commit in commits_list:
                    sections_text.append(f"  - {commit.format_entry()}")
            else:
                # Commit único ou sem PR - mostrar direto
                for commit in commits_list:
                    sections_text.append(commit.format_entry())
        sections_text.append("")  # Linha em branco entre grupos

    return "\n".join(sections_text)


def get_changelog_header() -> str:
    """Retorna o cabeçalho padrão do CHANGELOG."""
    return """# Changelog

Todas as alterações notáveis do Skybridge serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html/).

"""


def get_changelog_footer() -> str:
    """Retorna o rodapé com assinatura Sky."""
    return """---

## Referências

- **Versão atual:** ver `src/version.py`
- **Semantic Versioning:** https://semver.org/
- **Keep a Changelog:** https://keepachangelog.com/pt-BR/1.0.0/

> "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky 📚
"""


def update_changelog(new_version: str, commits: list[Commit]) -> None:
    """
    Atualiza o CHANGELOG.md inserindo a nova versão no topo.

    Preserva o histórico de versões anteriores e o rodapé existente.
    """
    changelog_path = Path("CHANGELOG.md")

    # Gerar nova seção da versão
    today = datetime.now().strftime("%Y-%m-%d")
    new_version_section = f"\n## [{new_version}] - {today}\n"
    new_content = generate_changelog(commits)

    # Ler CHANGELOG existente
    if not changelog_path.exists():
        # CHANGELOG não existe - criar com header + nova versão
        full_content = get_changelog_header() + new_version_section + new_content + get_changelog_footer()
    else:
        full_changelog = changelog_path.read_text(encoding="utf-8")

        # Encontrar onde começam as versões (primeira linha ## [)
        lines = full_changelog.split("\n")
        insert_at = None

        for i, line in enumerate(lines):
            if line.startswith("## ["):
                insert_at = i
                break

        if insert_at is not None:
            # Inserir nova versão antes da primeira versão existente
            lines.insert(insert_at, new_content)
            lines.insert(insert_at, new_version_section)
            full_content = "\n".join(lines)
        else:
            # Não encontrou nenhuma versão - adicionar no final
            full_content = full_changelog + "\n" + new_version_section + new_content

    changelog_path.write_text(full_content, encoding="utf-8")

    print(f"✅ CHANGELOG.md atualizado para {new_version}")


def main():
    """Ponto de entrada principal."""
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUso:")
        print("  python -m runtime.changelog <versão> [tag_base]")
        print("\nExemplos:")
        print("  python -m runtime.changelog 0.5.4 v0.5.3")
        print("  python -m runtime.changelog 0.5.4")
        return

    # Argumentos: versão é obrigatório, tag é opcional
    version = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) > 2 else None

    # Buscar commits
    print(f"🔍 Buscando commits desde {tag or 'última tag'}...")
    commits = get_commits_since(tag)

    if not commits:
        print("⚠️  Nenhum commit encontrado desde a tag base.")
        return

    print(f"📊 Encontrados {len(commits)} commits:")
    for section in SECTIONS.values():
        count = sum(1 for c in commits if SECTIONS[c.type] == section)
        if count > 0:
            print(f"   {section}: {count}")

    # Gerar preview
    print("\n📝 Preview do changelog gerado:")
    print("=" * 60)
    print(generate_changelog(commits))
    print("=" * 60)

    # Confirmar
    print(f"\n📝 Atualizando CHANGELOG.md para versão {version}...")
    update_changelog(version, commits)


if __name__ == "__main__":
    main()
