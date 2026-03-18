#!/usr/bin/env python3
"""
Coleta vocabulário técnico do projeto para hotwords do Whisper.

Analisa arquivos Python e extrai:
- Identificadores (nomes de classes, funções, variáveis)
- Strings literais (mensagens, comandos)
- Docstrings

Gera lista otimizada para hotwords do STT.
"""

import ast
import os
import re
from collections import Counter
from pathlib import Path
from typing import Set, List


def extract_python_vocabulary(files: List[Path]) -> Counter:
    """Extrai vocabulário de arquivos Python."""
    vocabulary = Counter()

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))

                # 1. Nomes de classes, funções, variáveis
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        vocabulary[node.name] += 3  # Classes têm peso maior
                    elif isinstance(node, ast.FunctionDef):
                        vocabulary[node.name] += 2
                    elif isinstance(node, ast.Name):
                        if isinstance(node.id, str):
                            vocabulary[node.id] += 1

                # 2. Strings literais
                strings = re.findall(r'"([^"]{4,})"', content)
                strings.extend(re.findall(r"'([^']{4,})'", content))
                for s in strings:
                    words = re.findall(r'[A-Za-z]{3,}', s)
                    for word in words:
                        vocabulary[word.lower()] += 1

                # 3. Docstrings
                for node in ast.walk(tree):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        words = re.findall(r'[A-Za-z]{3,}', docstring)
                        for word in words:
                            vocabulary[word.lower()] += 1

        except Exception as e:
            print(f"Erro ao processar {file_path}: {e}")

    return vocabulary


def filter_technical_terms(vocabulary: Counter, min_freq: int = 2) -> List[str]:
    """Filtra termos técnicos do vocabulário geral."""
    # Remove palavras comuns da língua
    common_words = {
        'self', 'def', 'class', 'return', 'import', 'from', 'async', 'await',
        'true', 'false', 'none', 'not', 'and', 'with', 'from', 'have', 'this',
        'that', 'from', 'with', 'have', 'will', 'can', 'just', 'like', 'get', 'set',
    }

    technical_terms = []
    for word, freq in vocabulary.most_common():
        if freq >= min_freq and word not in common_words and len(word) >= 4:
            technical_terms.append(word)

    return technical_terms


def generate_hotwords(vocabulary: List[str], max_words: int = 100) -> str:
    """Gera string de hotwords para Whisper."""
    # Pega as N palavras mais frequentes
    top_words = vocabulary[:max_words]

    # Remove duplicatas mantendo ordem
    seen = set()
    unique_words = []
    for word in top_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)

    # Junta com espaços (formato esperado pelo Whisper)
    return " ".join(unique_words)


def generate_initial_prompt(project_path: Path) -> str:
    """Gera initial prompt contextualizado."""
    prompt = """A Sky é uma assistente de IA técnica que auxilia em engenharia de software,
desenvolvimento, análise de código, deploy, testes e documentação. O contexto é de programação
Python moderna, arquitetura de software, git, CLI, APIs, bancos de dados e IA/ML. A Sky fala
português brasileiro de forma clara, técnica e profissional."""

    return " ".join(prompt.split())  # Remove múltiplos espaços


def main():
    """Função principal."""
    import sys
    sys.path.insert(0, 'src')

    # Encontra arquivos Python
    project_root = Path('src')
    python_files = list(project_root.rglob('*.py'))

    print(f"Analisando {len(python_files)} arquivos Python...")

    # Coleta vocabulário
    vocabulary = extract_python_vocabulary(python_files)
    print(f"Vocabulário total: {len(vocabulary)} palavras únicas")

    # Filtra termos técnicos
    technical_terms = filter_technical_terms(vocabulary, min_freq=3)
    print(f"Termos técnicos (freq >= 3): {len(technical_terms)}")

    # Gera hotwords
    hotwords = generate_hotwords(technical_terms, max_words=100)
    print(f"\n=== HOTWORDS ({len(hotwords.split())} palavras) ===")
    print(hotwords)

    # Salva em arquivo
    output_file = Path('stt_hotwords.txt')
    output_file.write_text(hotwords, encoding='utf-8')
    print(f"\nSalvo em: {output_file}")

    # Gera initial prompt
    initial_prompt = generate_initial_prompt(Path('.'))
    print(f"\n=== INITIAL PROMPT ===")
    print(initial_prompt)

    prompt_file = Path('stt_initial_prompt.txt')
    prompt_file.write_text(initial_prompt, encoding='utf-8')
    print(f"Salvo em: {prompt_file}")


if __name__ == '__main__':
    main()
