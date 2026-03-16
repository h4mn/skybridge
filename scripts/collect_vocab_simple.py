#!/usr/bin/env python3
"""
Coleta vocabulário técnico do projeto para hotwords do Whisper.

Versão simplificada que extrai apenas strings e identificadores.
"""

import re
from collections import Counter
from pathlib import Path


def extract_simple_vocabulary(files) -> Counter:
    """Extrai vocabulário simples (strings e identificadores)."""
    vocabulary = Counter()

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 1. Identificadores Python (snake_case, PascalCase)
                identifiers = re.findall(r'\b[a-z][a-z_]{3,}\b', content, re.IGNORECASE)
                for ident in identifiers:
                    vocabulary[ident.lower()] += 1

                # 2. Strings literais (mensagens, comandos)
                strings = re.findall(r'"([^"]{4,})"', content)
                strings.extend(re.findall(r"'([^']{4,})'", content))
                for s in strings:
                    words = re.findall(r'[A-Za-z]{3,}', s)
                    for word in words:
                        vocabulary[word.lower()] += 1

        except Exception:
            pass  # Silencioso

    return vocabulary


def filter_technical_terms(vocabulary: Counter, min_freq: int = 3) -> list:
    """Filtra termos técnicos."""
    # Palavras comuns da língua e programação
    skip_words = {
        'self', 'this', 'that', 'with', 'from', 'have', 'will', 'when',
        'file', 'data', 'text', 'user', 'code', 'exec', 'list', 'dict',
        'true', 'false', 'none', 'null', 'void', 'just', 'like', 'get',
        'set', 'add', 'remove', 'call', 'make', 'time', 'date', 'name',
        'args', 'kwargs', 'type', 'class', 'func', 'def', 'return', 'import',
        'module', 'package', 'super', 'base', 'init', 'main', 'test', 'check',
    }

    technical = []
    for word, freq in vocabulary.most_common():
        if freq >= min_freq and word not in skip_words and len(word) >= 4:
            technical.append(word)

    return technical


def generate_hotwords(vocabulary: list, max_words: int = 100) -> str:
    """Gera string de hotwords."""
    # Remove duplicatas mantendo ordem
    seen = set()
    unique = []
    for word in vocabulary:
        if word not in seen:
            seen.add(word)
            unique.append(word)
        if len(unique) >= max_words:
            break

    return " ".join(unique)


def main():
    """Função principal."""
    # Encontra arquivos Python
    project_root = Path('src')
    python_files = list(project_root.rglob('*.py'))

    print(f"Analisando {len(python_files)} arquivos Python...")

    # Coleta vocabulário
    vocabulary = extract_simple_vocabulary(python_files)
    print(f"Vocabulário total: {len(vocabulary)} palavras únicas")

    # Mostra top 50
    print("\n=== TOP 50 PALAVRAS ===")
    for word, freq in vocabulary.most_common(50):
        print(f"  {word}: {freq}")

    # Filtra termos técnicos
    technical_terms = filter_technical_terms(vocabulary, min_freq=5)
    print(f"\nTermos técnicos (freq >= 5): {len(technical_terms)}")

    # Gera hotwords
    hotwords = generate_hotwords(technical_terms, max_words=100)
    print(f"\n=== HOTWORDS ({len(hotwords.split())} palavras) ===")
    print(hotwords[:500])  # Primeiros 500 chars

    # Salva
    Path('stt_hotwords.txt').write_text(hotwords, encoding='utf-8')
    print(f"\nSalvo em: stt_hotwords.txt ({len(hotwords.split())} palavras)")


if __name__ == '__main__':
    main()
