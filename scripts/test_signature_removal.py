#!/usr/bin/env python
# coding: utf-8
"""
Teste remoção de assinaturas do texto para fala.
"""

import sys
import io

# Configura stdout para UTF-8 (Windows)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, "src")


def test_signature_removal():
    """Testa remoção de assinaturas."""

    import re

    def _clean_text_for_speech(text: str) -> str:
        """Remove markdown, metadados e assinaturas para fala natural."""
        # Remove blocos de código completos
        text = re.sub(r'```[\s\S]*?```', '', text)

        # Remove `inline code` mas mantém o conteúdo
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # Remove **negrito** mas mantém o conteúdo
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

        # Remove *itálico* mas mantém o conteúdo
        text = re.sub(r'\*([^*]+)\*', r'\1', text)

        # Remove títulos markdown
        text = re.sub(r'#{1,6}\s+', '', text)

        # Remove links mas mantém o texto
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

        # Remove assinaturas "made by Sky" e emojis isolados no final
        text = re.sub(r'\s*[-–—]?\s*made by\s+Sky[\s\U0001F300-\U0001F9FF]*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'>\s*"?\s*made by\s+Sky[^"]*"?$', '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Remove memórias RAG de forma mais inteligente
        lines = text.split('\n')
        clean_lines = []
        in_memory_section = False

        for line in lines:
            # Detecta início de seção de memória
            if 'memória' in line.lower() and ('encontrei' in line.lower() or 'achei' in line.lower()):
                in_memory_section = True
                continue

            # Detecta fim da seção de memória
            if in_memory_section and line.strip() and not line.strip().startswith('•'):
                in_memory_section = False

            # Pula linhas da seção de memória
            if in_memory_section or line.strip().startswith('•'):
                continue

            # Pula linhas que são apenas assinatura/emojis
            if re.match(r'^[\s\U0001F300-\U0001F9FF]*made by\s+Sky', line, re.IGNORECASE):
                continue

            # Remove linhas vazias duplicadas (mais de 2 consecutivas)
            if not line.strip() and clean_lines and not clean_lines[-1].strip():
                prev_prev = clean_lines[-2] if len(clean_lines) >= 2 else ""
                if not prev_prev.strip():
                    continue

            clean_lines.append(line)

        text = '\n'.join(clean_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    print("=" * 60)
    print("TESTE: Remoção de assinaturas")
    print("=" * 60)

    # Teste 1: Texto com assinatura no final
    texto1 = """Esta é uma resposta completa da Sky, com todo o conteúdo importante que o usuário deveria ouvir.

🧠 made by Sky 🚀"""

    resultado1 = _clean_text_for_speech(texto1)

    print(f"\nTeste 1: Assinatura no final")
    print(f"Original: {repr(texto1[-50:])}")
    print(f"Limpo: {repr(resultado1[-50:])}")
    print(f"Assinatura removida: {'OK' if 'made by Sky' not in resultado1 else 'FAIL'}")
    print(f"Conteúdo preservado: {'OK' if 'resposta completa' in resultado1 else 'FAIL'}")

    # Teste 2: Texto com assinatura no meio
    texto2 = """Parte 1 da resposta

> "made by Sky"

Parte 2 da resposta"""

    resultado2 = _clean_text_for_speech(texto2)

    print(f"\nTeste 2: Assinatura no meio")
    print(f"Original: {repr(texto2)}")
    print(f"Limpo: {repr(resultado2)}")
    print(f"Assinatura removida: {'OK' if 'made by Sky' not in resultado2 else 'FAIL'}")
    print(f"Partes preservadas: {'OK' if 'Parte 1' in resultado2 and 'Parte 2' in resultado2 else 'FAIL'}")

    # Teste 3: Texto com memória RAG + assinatura
    texto3 = """Encontrei isso na memória:
• Sky é uma assistente de IA
• Sky adora aprender

Resposta completa da Sky aqui.

🧠 made by Sky 🚀"""

    resultado3 = _clean_text_for_speech(texto3)

    print(f"\nTeste 3: Memória RAG + assinatura")
    print(f"Original: {len(texto3)} chars")
    print(f"Limpo: {len(resultado3)} chars")
    print(f"Memória removida: {'OK' if '•' not in resultado3 and 'memória' not in resultado3.lower() else 'FAIL'}")
    print(f"Assinatura removida: {'OK' if 'made by Sky' not in resultado3 else 'FAIL'}")
    print(f"Resposta preservada: {'OK' if 'Resposta completa' in resultado3 else 'FAIL'}")

    print()


if __name__ == "__main__":
    test_signature_removal()
