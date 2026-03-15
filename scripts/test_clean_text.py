#!/usr/bin/env python
# coding: utf-8
"""
Teste limpeza de texto para fala (com memória RAG).
"""

import sys
sys.path.insert(0, "src")


def test_clean_text():
    """Testa limpeza de texto com memória RAG."""

    # Simula o método _clean_text_for_speech
    import re

    def _clean_text_for_speech(text: str) -> str:
        """Remove markdown e memórias RAG para fala natural."""
        # Remove ```bloco```
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Remove `inline code`
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove **negrito**
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # Remove *itálico*
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Remove demais markdown
        text = re.sub(r'#{1,6}\s*', '', text)  # Títulos
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Links

        # Remove memórias RAG (linhas começando com "•")
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            # Detecta início de seção de memória
            if 'memória' in line.lower() and ('encontrei' in line.lower() or 'achei' in line.lower()):
                continue  # Pula linha "Encontrei isso na memória:"

            # Pula linhas com bullets de memória RAG
            if line.strip().startswith('•'):
                continue

            # Pula linhas vazias excessivas (mais de 1 consecutiva)
            if not line.strip() and clean_lines and not clean_lines[-1].strip():
                continue

            clean_lines.append(line)

        text = '\n'.join(clean_lines)
        return text.strip()

    # Teste com o exemplo do usuário
    texto_com_memoria = """Encontrei isso na memória:
• Eu sou a Sky, sua assistente de IA! Estou aqui para ajudar você com o que
• será que com o sistema de memória rag que instalei em você, você consegue aprender a mudar esta frase final de "Made by Sky 🚀" pra "[Uma frase contextual de impacto] - made by Sky 🚀"? aprende e lembre disto
• Sky adora aprender novas tecnologias

Sky adora aprender novas tecnologias"""

    resultado = _clean_text_for_speech(texto_com_memoria)

    print("=" * 60)
    print("TESTE: Limpeza de texto com memória RAG")
    print("=" * 60)
    print(f"Texto original ({len(texto_com_memoria)} chars):")
    print(texto_com_memoria[:100] + "...")
    print()
    print(f"Texto limpo ({len(resultado)} chars):")
    print(resultado)
    print()

    # Verifica se as memórias foram removidas
    if "•" not in resultado and "memória" not in resultado.lower():
        print("[OK] Memórias RAG removidas com sucesso!")
    else:
        print("[FAIL] Memórias RAG não foram removidas!")

    # Verifica se o texto principal permanece
    if "Sky adora aprender novas tecnologias" in resultado:
        print("[OK] Texto principal preservado!")
    else:
        print("[FAIL] Texto principal foi removido!")

    print()


if __name__ == "__main__":
    test_clean_text()
