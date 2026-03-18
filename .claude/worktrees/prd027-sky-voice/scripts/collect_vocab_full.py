#!/usr/bin/env python3
"""
Coleta vocabulário técnico completo do projeto para hotwords do Whisper.

Meta: 250+ palavras únicas combinando:
- Identificadores Python (classes, funções, variáveis)
- Nomes de pastas/diretórios
- Strings técnicas
- Termos de domínio

Saída: stt_hotwords.txt (espaçados para Whisper)
"""

import re
import sys
from collections import Counter
from pathlib import Path


def extract_from_code(files) -> Counter:
    """Extrai identificadores do código Python."""
    vocab = Counter()

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Identificadores PascalCase, camelCase, snake_case
                identifiers = re.findall(r'\b[A-Z][a-zA-Z0-9]{2,}\b', content)
                for ident in identifiers:
                    # Converte PascalCase/camelCase para palavras
                    words = re.findall(r'[A-Z][a-z]+|[A-Z]+(?=[A-Z]|$)', ident)
                    for word in words:
                        vocab[word.lower()] += 1

                # Strings literais (termos técnicos)
                strings = re.findall(r'"([^"]{4,})"', content)
                strings.extend(re.findall(r"'([^']{4,})'", content))
                for s in strings:
                    # Extrai palavras (ignora verbos comuns)
                    words = re.findall(r'[a-z]{3,}', s.lower())
                    for word in words:
                        if word not in ['para', 'como', 'com', 'mais', 'arquivo']:
                            vocab[word] += 1

        except Exception:
            pass

    return vocab


def extract_from_directories(root_path: Path) -> Counter:
    """Extrai nomes de diretórios como vocabulário."""
    vocab = Counter()

    # Coleta todos os nomes de diretórios
    for dir_path in root_path.rglob('*'):
        if dir_path.is_dir():
            # Nome do diretório
            name = dir_path.name
            if len(name) >= 3 and name not in ['src', '__pycache__', '.git']:
                vocab[name.lower()] += 1

    return vocab


def merge_and_filter(vocab_code: Counter, vocab_dirs: Counter, min_freq: int = 2) -> list:
    """Mescla e filtra vocabulários."""
    combined = vocab_code + vocab_dirs

    # Palavras a ignorar (muito genéricas)
    skip_words = {
        'self', 'this', 'that', 'with', 'from', 'have', 'will', 'when',
        'file', 'data', 'text', 'user', 'code', 'exec', 'make', 'time', 'date',
        'args', 'kwargs', 'type', 'class', 'func', 'def', 'return', 'import', 'init',
        'main', 'test', 'check', 'call', 'send', 'recv', 'read', 'write', 'load',
        'save', 'open', 'close', 'start', 'stop', 'wait', 'done', 'work', 'task',
        'item', 'element', 'value', 'list', 'dict', 'set', 'get', 'set', 'add',
        'remove', 'find', 'search', 'sort', 'filter', 'map', 'reduce',
    }

    # Filtra e mantém ordem de frequência
    filtered = []
    seen = set()

    for word, freq in combined.most_common():
        if freq >= min_freq and word not in skip_words and len(word) >= 3:
            if word not in seen:
                seen.add(word)
                filtered.append(word)

        if len(filtered) >= 300:  # Pega pelo menos 300
            break

    return filtered


def generate_hotwords(vocabulary: list, max_words: int = 250) -> str:
    """Gera string de hotwords otimizada."""
    words = vocabulary[:max_words]

    # Organiza por categoria para melhor contexto
    categories = {
        'skybridge': [],
        'technical': [],
        'actions': [],
        'structure': [],
        'domain': [],
    }

    for word in words:
        word_lower = word.lower()
        if any(x in word_lower for x in ['sky', 'bridge', 'agent', 'job', 'webhook']):
            categories['skybridge'].append(word)
        elif any(x in word_lower for x in ['git', 'deploy', 'api', 'http', 'sql']):
            categories['technical'].append(word)
        elif any(x in word_lower for x in ['criar', 'fazer', 'executar', 'processar']):
            categories['actions'].append(word)
        elif any(x in word_lower for x in ['class', 'module', 'service', 'config']):
            categories['structure'].append(word)
        else:
            categories['domain'].append(word)

    # Junta categorias ( SkyBridge primeiro para bias forte)
    ordered = []
    for cat in ['skybridge', 'technical', 'actions',structure', 'domain']:
        ordered.extend(categories[cat])

    # Remove duplicatas mantendo ordem
    seen = set()
    unique = []
    for word in ordered:
        if word not in seen:
            seen.add(word)
            unique.append(word)

    return " ".join(unique[:max_words])


def main():
    """Função principal."""
    root_path = Path('src')
    python_files = list(root_path.rglob('*.py'))

    print(f"Analisando {len(python_files)} arquivos Python...")

    # Coleta vocabulários
    vocab_code = extract_from_code(python_files)
    vocab_dirs = extract_from_directories(root_path)

    print(f"Vocabulário código: {len(vocab_code)} palavras")
    print(f"Vocabulário diretórios: {len(vocab_dirs)} palavras")

    # Merge e filtro
    technical_terms = merge_and_filter(vocab_code, vocab_dirs, min_freq=3)
    print(f"Termos técnicos únicos: {len(technical_terms)}")

    # Mostra categorias
    print("\n=== EXEMPLOS POR CATEGORIA ===")
    skybridge_words = [w for w in technical_terms[:20] if any(x in w for x in ['sky', 'bridge', 'agent', 'webhook'])]
    technical_words = [w for w in technical_terms[:30] if any(x in w for x in ['git', 'api', 'http', 'deploy'])]
    domain_words = [w for w in technical_terms[:30] if any(x in w for x in ['chat', 'voice', 'kanban', 'memory'])]

    print(f"SkyBridge: {skybridge_words}")
    print(f"Technical: {technical_words}")
    print(f"Domain: {domain_words}")

    # Gera hotwords
    hotwords = generate_hotwords(technical_terms, max_words=250)
    word_count = len(hotwords.split())
    print(f"\n=== HOTWORDS ({word_count} palavras) ===")

    # Mostra amostra
    for i in range(0, min(len(hotwords), 300), 50):
        print(hotwords[i:i+50])

    # Salva
    output_file = Path('stt_hotwords.txt')
    output_file.write_text(hotwords, encoding='utf-8')
    print(f"\n✅ Salvo em: {output_file}")
    print(f"✅ Total: {word_count} palavras únicas")

    # Estatísticas
    print(f"\n=== ESTATÍSTICAS ===")
    print(f"Arquivos Python: {len(python_files)}")
    print(f"Palavras hotwords: {word_count}")
    print(f"Tamanho arquivo: {output_file.stat().st_size} bytes")
    print(f"Estimativa de overhead: +10-15% na latência")


if __name__ == '__main__':
    main()
