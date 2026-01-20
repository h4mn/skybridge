#!/usr/bin/env python3
"""
Skybridge Changelog Generator

Gera CHANGELOG.md no formato Sky (PT-BR, emojis, links ricos, sem "No changes").

Uso:
    python -m runtime.changelog [versão] [tag_base] [--apply]

Exemplos:
    python -m runtime.changelog                       # Preview com versão do src/version.py
    python -m runtime.changelog v0.5.3                # Preview desde v0.5.3
    python -m runtime.changelog 0.5.5 v0.5.4 --apply  # Aplica e escreve no CHANGELOG.md

Padrão: dry-run (apenas preview). Use --apply para escrever no arquivo.

> "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky 📚
"""

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


def get_project_version() -> str:
    """Retorna a versão do projeto a partir de src/version.py."""
    version_path = Path("src/version.py")
    if version_path.exists():
        for line in version_path.read_text(encoding="utf-8").split("\n"):
            if line.startswith("__version__"):
                # Extrair versão entre aspas, removendo sufixo -dev se existir
                version = line.split("=")[1].strip().strip('"').strip("'")
                return version.replace("-dev", "")
    raise FileNotFoundError("Não foi possível encontrar __version__ em src/version.py")


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

    def format_pr_header(self) -> str:
        """Formata cabeçalho de agrupamento por PR."""
        if not self.pr_number:
            return None
        return f"[**#{self.pr_number}**](https://github.com/h4mn/skybridge/pull/{self.pr_number}) - {self.subject[:60]}{'...' if len(self.subject) > 60 else ''}"


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


def get_github_token() -> Optional[str]:
    """Retorna o token do GitHub (GITHUB_TOKEN na CI ou variável de ambiente local)."""
    # Na CI, o GITHUB_TOKEN é automaticamente provisionado
    # Localmente, pode ser definido via variável de ambiente
    return os.environ.get("GITHUB_TOKEN")


def fetch_pr_commits(pr_number: str, repo: str = "h4mn/skybridge") -> list[dict]:
    """
    Busca todos os commits de uma PR via GitHub API.

    Args:
        pr_number: Número da PR (ex: "49")
        repo: Repositório no formato "owner/repo"

    Returns:
        Lista de commits da PR com hash, message, etc.
    """
    token = get_github_token()
    if not token:
        print(f"⚠️  GITHUB_TOKEN não encontrado. Pulando busca de commits da PR #{pr_number}")
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/commits"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  Erro ao buscar commits da PR #{pr_number}: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️  Erro ao conectar com GitHub API: {e}")
        return []


def extract_pr_and_clean_subject(subject: str) -> tuple[Optional[str], str]:
    """
    Extrai número da PR e remove referência do subject.

    Args:
        subject: Mensagem do commit (ex: "feat(webhooks): adicionar feature (#49)")

    Returns:
        Tupla (pr_number, clean_subject) onde pr_number pode ser None
    """
    # Extrair número da PR do subject
    pr_match = re.search(r"#(\d+)", subject)
    pr_number = pr_match.group(1) if pr_match else None

    # Remover TODAS as referências à PR do subject
    clean_subject = subject

    # Remover links markdown: [#NN](url) ou [NN](url)
    clean_subject = re.sub(r"\s*\[#?\d+\]\([^)]+\)", "", clean_subject)
    # Remover parênteses vazios que sobraram: ()
    clean_subject = re.sub(r"\s*\(\s*\)", "", clean_subject)
    # Remover referências à PR: (#NN) ou (#NN ) ou simplesmente (# NN)
    clean_subject = re.sub(r"\s*\(\s*#?\d+\s*\)", "", clean_subject)
    # Limpar espaços extras
    clean_subject = re.sub(r"\s{2,}", " ", clean_subject).strip()

    return pr_number, clean_subject


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
    Retorna todos os commits desde a tag especificada até HEAD.

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

        # Extrair número da PR e limpar o subject
        pr_number, clean_subject = extract_pr_and_clean_subject(clean_subject)

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


def get_commits_between(from_tag: Optional[str], to_tag: str) -> list[Commit]:
    """
    Retorna todos os commits entre duas tags (exclusivo).

    Args:
        from_tag: Tag inicial (exclusiva). Se None, começa do início.
        to_tag: Tag final (inclusiva).
    """
    git_range = f"{from_tag}..{to_tag}" if from_tag else to_tag

    # Buscar commits no formato: hash|subject|author_name|author_email
    env = {"GIT_LOG_OUTPUT_ENCODING": "utf-8"}
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.quotepath=false",
            "log",
            git_range,
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

        # Extrair número da PR e limpar o subject
        pr_number, clean_subject = extract_pr_and_clean_subject(clean_subject)

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


def generate_changelog_simple(commits: list[Commit]) -> str:
    """Gera o conteúdo do changelog no formato Sky simples (sem agrupamento por PR)."""
    # Agrupar commits apenas por tipo
    grouped: dict[str, list[Commit]] = {}

    for commit in commits:
        if commit.type not in grouped:
            grouped[commit.type] = []
        grouped[commit.type].append(commit)

    # Gerar seções organizadas
    sections_text = []

    # Ordem dos tipos de commit
    type_order = ["feat", "fix", "refactor", "docs", "style", "perf", "test", "build", "ci", "chore", "revert"]

    for commit_type in type_order:
        if commit_type not in grouped:
            continue

        section_name = SECTIONS[commit_type]
        sections_text.append(f"\n### {section_name}\n")

        # Mostrar todos os commits deste tipo em ordem
        for commit in grouped[commit_type]:
            sections_text.append(commit.format_entry())
        sections_text.append("")  # Linha em branco entre seções

    return "\n".join(sections_text)


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
            if pr_number:
                # Qualquer commit com PR - mostrar com cabeçalho clicável
                pr_header = commits_list[0].format_pr_header()
                if pr_header:
                    sections_text.append(f"\n{pr_header}\n")
                for commit in commits_list:
                    sections_text.append(commit.format_entry())
                sections_text.append("")  # Linha em branco após grupo com PR
            else:
                # Commit sem PR - mostrar direto
                for commit in commits_list:
                    sections_text.append(commit.format_entry())
        sections_text.append("")  # Linha em branco entre grupos

    return "\n".join(sections_text)


def get_existing_commit_hashes() -> set[str]:
    """
    Lê o CHANGELOG.md e retorna todos os hashes de commits já presentes.

    Returns:
        Set com os hashes curtos (7 caracteres) dos commits já no changelog.
    """
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        return set()

    content = changelog_path.read_text(encoding="utf-8")
    # Extrair hashes no formato [`abc1234`](https://github.com/...)
    import re
    matches = re.findall(r'\[`([a-f0-9]{7})`\]', content)
    return set(matches)


def filter_new_commits(commits: list[Commit]) -> list[Commit]:
    """
    Filtra commits que já existem no CHANGELOG.md.

    Args:
        commits: Lista de commits para filtrar.

    Returns:
        Lista de commits que ainda não estão no changelog.
    """
    existing_hashes = get_existing_commit_hashes()
    new_commits = [c for c in commits if c.short_hash not in existing_hashes]

    if len(commits) != len(new_commits):
        skipped = len(commits) - len(new_commits)
        print(f"⏭️  Ignorando {skipped} commit(s) já presente(s) no CHANGELOG.md")

    return new_commits


def enrich_commits_with_pr_data(commits: list[Commit], repo: str = "h4mn/skybridge") -> list[Commit]:
    """
    Enriquece commits com dados da GitHub API, buscando commits internos das PRs.

    Args:
        commits: Lista de commits originais (do git log).
        repo: Repositório no formato "owner/repo".

    Returns:
        Lista de commits enriquecida com commits internos das PRs.
    """
    # Agrupar commits por PR
    pr_groups: dict[Optional[str], list[Commit]] = {}
    for commit in commits:
        if commit.pr_number:
            if commit.pr_number not in pr_groups:
                pr_groups[commit.pr_number] = []
            pr_groups[commit.pr_number].append(commit)
        else:
            # Commit sem PR - mantém como está
            pr_groups[None] = pr_groups.get(None, [])
            pr_groups[None].append(commit)

    # Hashes já processados para evitar duplicatas
    processed_hashes = {c.short_hash for c in commits}

    # Para cada PR, buscar commits internos via API (mesmo com squash merge)
    enriched = list(commits)  # Começa com os commits originais

    for pr_number, pr_commits in pr_groups.items():
        if pr_number is None:
            continue  # Commit sem PR - não há nada para buscar na API

        print(f"🔍 Buscando commits internos da PR #{pr_number} via GitHub API...")
        api_commits = fetch_pr_commits(pr_number, repo)

        if not api_commits:
            continue

        # Adicionar commits internos que não estão na lista original
        for api_commit_data in api_commits:
            api_hash = api_commit_data['sha']
            short_hash = api_hash[:7]

            # Pular se já existe
            if short_hash in processed_hashes:
                continue

            # Parse do commit da API
            api_subject = api_commit_data['commit']['message'].split('\n')[0]  # Primeira linha
            api_author = api_commit_data['author']['login']
            api_email = api_commit_data['author'].get('email') or f"{api_author}@users.noreply.github.com"

            # Extrair tipo e scope
            match = re.match(r"^(\w+)(?:\(([^)]+)\))?:?\s*(.*)$", api_subject)
            if not match:
                continue

            commit_type, scope, clean_subject = match.groups()
            if commit_type not in SECTIONS:
                continue

            # Extrair PR e limpar (API não tem #NN no subject geralmente)
            pr_from_api, clean_subject = extract_pr_and_clean_subject(clean_subject)
            # Se API não trouxer PR, usar a PR conhecida
            final_pr_number = pr_from_api if pr_from_api else pr_number

            enriched.append(Commit(
                hash=api_hash,
                short_hash=short_hash,
                subject=clean_subject,
                type=commit_type,
                scope=scope,
                author_name=api_author,
                author_email=api_email,
                pr_number=final_pr_number
            ))
            processed_hashes.add(short_hash)
            print(f"  + [{short_hash}] {commit_type}({scope}): {clean_subject[:50]}...")

    # Ordenar por data do commit (mais recentes primeiro)
    enriched.sort(key=lambda c: c.hash, reverse=True)
    return enriched


def get_all_tags() -> list[str]:
    """
    Retorna todas as tags do repositório em ordem reversa (mais recente primeiro).

    Returns:
        Lista de tags ordenadas da mais recente para a mais antiga.
    """
    result = subprocess.run(
        ["git", "tag", "-l", "--sort=-v:refname"],
        capture_output=True,
        text=True,
        check=True
    )
    tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
    return tags


def get_tag_date(tag: str) -> str:
    """Retorna a data de uma tag no formato YYYY-MM-DD."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ci", tag],
        capture_output=True,
        text=True,
        check=True
    )
    # Formato: 2026-01-19 10:30:00 +0000 -> pegar apenas a data
    return result.stdout.strip().split(" ")[0]


def generate_full_changelog_from_git(detailed: bool = False) -> str:
    """
    Gera o changelog completo do git, percorrendo todas as tags.

    Args:
        detailed: Se True, usa API GitHub e agrupa por PR. Se False, modo simples.

    Returns:
        String com o changelog completo formatado.
    """
    tags = get_all_tags()

    if not tags:
        return "Nenhuma tag encontrada no repositório."

    sections = []

    # PRIMEIRO: adicionar commits não taggeados (desde a última tag até HEAD)
    latest_tag = tags[0]
    untagged_commits = get_commits_since(latest_tag)

    if untagged_commits:
        # Enriquecer com dados da API do GitHub apenas se detailed=True
        if detailed:
            untagged_commits = enrich_commits_with_pr_data(untagged_commits)
        sections.append(f"\n## [Pendente]\n")
        # Usar função simples ou detalhada dependendo da flag
        sections.append(generate_changelog(untagged_commits) if detailed else generate_changelog_simple(untagged_commits))

    # DEPOIS: para cada tag, pegar commits desde a tag anterior
    for i, tag in enumerate(tags):
        # Tag anterior (ou None para a primeira tag)
        prev_tag = tags[i + 1] if i + 1 < len(tags) else None

        # Pegar commits entre prev_tag (exclusivo) e tag (inclusivo)
        commits = get_commits_between(prev_tag, tag)

        if not commits:
            continue

        # Enriquecer com dados da API do GitHub apenas se detailed=True
        if detailed:
            commits = enrich_commits_with_pr_data(commits)

        # Data da tag
        tag_date = get_tag_date(tag)
        version = tag.lstrip('v')

        # Gerar seção da versão
        sections.append(f"\n## [{version}] - {tag_date}\n")
        sections.append(generate_changelog(commits) if detailed else generate_changelog_simple(commits))

    return "\n".join(sections)


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


def remove_pending_section() -> bool:
    """
    Remove a seção [Pendente] do CHANGELOG.md.

    Returns:
        True se a seção foi removida, False se não existia.
    """
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        return False

    content = changelog_path.read_text(encoding="utf-8")

    # Encontrar seção [Pendente]
    import re
    pattern = r'\n## \[Pendente\].*?(?=\n## \[|$)'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        return False

    # Remover a seção
    new_content = content[:match.start()] + content[match.end():]
    changelog_path.write_text(new_content, encoding="utf-8")

    return True


def update_changelog(new_version: str, commits: list[Commit], detailed: bool = False) -> None:
    """
    Atualiza o CHANGELOG.md inserindo a nova versão no topo.

    Args:
        new_version: Versão a ser criada.
        commits: Lista de commits para incluir.
        detailed: Se True, usa modo detalhado. Se False, usa modo simples.

    Preserva o histórico de versões anteriores e o rodapé existente.
    """
    changelog_path = Path("CHANGELOG.md")

    # Gerar nova seção da versão
    today = datetime.now().strftime("%Y-%m-%d")
    new_version_section = f"\n## [{new_version}] - {today}\n"
    new_content = generate_changelog(commits) if detailed else generate_changelog_simple(commits)

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
    parser = argparse.ArgumentParser(
        description="Skybridge Changelog Generator - Gera CHANGELOG.md no formato Sky",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m runtime.changelog                       # Preview simples com versão do src/version.py
  python -m runtime.changelog v0.5.3                # Preview simples desde v0.5.3
  python -m runtime.changelog 0.5.5 v0.5.4 --apply  # Aplica e escreve no CHANGELOG.md
  python -m runtime.changelog --from-git            # Gera changelog histórico completo do git
  python -m runtime.changelog --from-git --apply    # Reescreve CHANGELOG.md completo

Modo detalhado (com API GitHub e agrupamento por PR):
  python -m runtime.changelog --detailed            # Preview detalhado
  python -m runtime.changelog --from-git --detailed # Changelog histórico detalhado
  python -m runtime.changelog 0.5.5 v0.5.4 --detailed --apply

GitHub Actions:
  python -m runtime.changelog 0.6.0 v0.5.4 --from-gh --apply --detailed  # Remove [Pendente] e cria versão 0.6.0

Padrão: dry-run (apenas preview), modo simples (sem API GitHub). Use --apply para escrever no arquivo.
        """
    )
    parser.add_argument("version", nargs="?", help="Versão do release (ex: 0.5.4). Usado apenas sem --from-git")
    parser.add_argument("tag", nargs="?", help="Tag base (ex: v0.5.3). Usado apenas sem --from-git")
    parser.add_argument("--apply", action="store_true", help="Aplica as alterações e escreve no CHANGELOG.md")
    parser.add_argument("--from-git", action="store_true", help="Gera changelog histórico completo do git (ignora version/tag)")
    parser.add_argument("--from-gh", action="store_true", help="Modo GitHub Actions: remove [Pendente] antes de processar")
    parser.add_argument("--detailed", action="store_true", help="Modo detalhado: usa API GitHub e agrupa commits por PR")

    args = parser.parse_args()

    # Modo --from-git: gera changelog histórico completo
    if args.from_git:
        mode = "detalhado" if args.detailed else "simples"
        print(f"🔍 Gerando changelog histórico completo do git (modo {mode})...")
        full_changelog = generate_full_changelog_from_git(detailed=args.detailed)

        print("\n📝 Preview do changelog gerado:")
        print("=" * 60)
        print(full_changelog)
        print("=" * 60)

        if not args.apply:
            print(f"\n🔍 MODO DRY-RUN: CHANGELOG.md NÃO foi alterado")
            detailed_flag = " --detailed" if args.detailed else ""
            print(f"   Para aplicar, use: python -m runtime.changelog --from-git{detailed_flag} --apply")
            return

        # Aplicar: reescrever CHANGELOG.md completo
        changelog_path = Path("CHANGELOG.md")
        full_content = get_changelog_header() + full_changelog + "\n\n" + get_changelog_footer()
        changelog_path.write_text(full_content, encoding="utf-8")
        print(f"\n✅ CHANGELOG.md reescrito com histórico completo do git (modo {mode})")
        return

    # Modo --from-gh: remove [Pendente] antes de processar
    if args.from_gh:
        removed = remove_pending_section()
        if removed:
            print("🗑️  Seção [Pendente] removida do CHANGELOG.md")

    # Determinar versão
    if args.version:
        version = args.version.lstrip('v')  # Remover prefixo 'v' se presente
    else:
        try:
            version = get_project_version()
            print(f"📌 Versão detectada: {version}")
        except FileNotFoundError:
            print("❌ Não foi possível detectar a versão. Especifique a versão:")
            print("   python -m runtime.changelog 0.5.5 v0.5.4")
            return

    # Buscar commits
    mode = "detalhado" if args.detailed else "simples"
    print(f"🔍 Buscando commits desde {args.tag or 'última tag'} (modo {mode})...")
    commits = get_commits_since(args.tag)

    if not commits:
        print("⚠️  Nenhum commit encontrado desde a tag base.")
        return

    # Filtrar commits que já existem no CHANGELOG
    commits = filter_new_commits(commits)

    if not commits:
        print("⚠️  Nenhum commit novo para adicionar ao CHANGELOG.md")
        return

    # Enriquecer com dados da GitHub API (apenas se detailed=True)
    if args.detailed:
        commits = enrich_commits_with_pr_data(commits)

    print(f"📊 Encontrados {len(commits)} commits novos:")
    for section in SECTIONS.values():
        count = sum(1 for c in commits if SECTIONS[c.type] == section)
        if count > 0:
            print(f"   {section}: {count}")

    # Gerar preview
    print("\n📝 Preview do changelog gerado:")
    print("=" * 60)
    changelog_content = generate_changelog(commits) if args.detailed else generate_changelog_simple(commits)
    print(changelog_content)
    print("=" * 60)

    # Modo dry-run (padrão): não escreve no arquivo
    if not args.apply:
        print(f"\n🔍 MODO DRY-RUN: CHANGELOG.md NÃO foi alterado")
        print(f"   Versão: {version}")
        detailed_flag = " --detailed" if args.detailed else ""
        from_gh_flag = " --from-gh" if args.from_gh else ""
        print(f"   Para aplicar, use: python -m runtime.changelog {version} {args.tag or ''}{from_gh_flag}{detailed_flag} --apply")
        return

    # Aplicar: escrever no arquivo
    print(f"\n📝 Atualizando CHANGELOG.md para versão {version}...")
    update_changelog(version, commits, detailed=args.detailed)


if __name__ == "__main__":
    main()
