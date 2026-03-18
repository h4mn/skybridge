#!/usr/bin/env python
# coding: utf-8
"""
Teste limpeza de texto para fala - versão melhorada.

Objetivo: Preservar toda a resposta principal, removendo apenas memórias RAG.
"""

import sys
sys.path.insert(0, "src")


def test_clean_text():
    """Testa limpeza de texto com resposta completa."""

    # Simula o método _clean_text_for_speech
    import re

    def _clean_text_for_speech(text: str) -> str:
        """Remove markdown e metadados para fala natural."""
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

            # Remove linhas vazias duplicadas
            if not line.strip() and clean_lines and not clean_lines[-1].strip():
                prev_prev = clean_lines[-2] if len(clean_lines) >= 2 else ""
                if not prev_prev.strip():
                    continue

            clean_lines.append(line)

        text = '\n'.join(clean_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    # Teste 1: Exemplo do usuário
    print("=" * 60)
    print("TESTE 1: Resposta com memória RAG")
    print("=" * 60)

    texto_usuario = """Encontrei isso na memória:
• Eu sou a Sky, sua assistente de IA! Estou aqui para ajudar você com o que
• será que com o sistema de memória rag que instalei em você, você consegue aprender a mudar esta frase final de "Made by Sky 🚀" pra "[Uma frase contextual de impacto] - made by Sky 🚀"? aprende e lembre disto
• Sky adora aprender novas tecnologias

Sky adora aprender novas tecnologias, especialmente quando elas ajudam a criar experiências mais interessantes para os usuários!"""

    resultado = _clean_text_for_speech(texto_usuario)

    print(f"Original: {len(texto_usuario)} chars")
    print(f"Limpo: {len(resultado)} chars")
    print(f"\nTexto limpo:\n{resultado}")
    print()

    # Verificações
    checks = [
        ("Memórias removidas", "•" not in resultado and "memória" not in resultado.lower()),
        ("Resposta preservada", "Sky adora aprender novas tecnologias" in resultado),
        ("Texto completo preservado", "especialmente quando elas ajudam" in resultado),
    ]

    for desc, passed in checks:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {desc}")

    print()

    # Teste 2: Resposta com código
    print("=" * 60)
    print("TESTE 2: Resposta com código")
    print("=" * 60)

    texto_codigo = """Para resolver o problema, você pode usar o seguinte código:

```python
def hello():
    print("Olá mundo!")
```

Esta função simples imprime uma mensagem."""

    resultado2 = _clean_text_for_speech(texto_codigo)

    print(f"Original: {len(texto_codigo)} chars")
    print(f"Limpo: {len(resultado2)} chars")
    print(f"\nTexto limpo:\n{resultado2}")
    print()

    checks2 = [
        ("Código removido", "```" not in resultado2 and "def hello" not in resultado2),
        ("Texto preservado", "Para resolver o problema" in resultado2),
        ("Explicação preservada", "imprime uma mensagem" in resultado2),
    ]

    for desc, passed in checks2:
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {desc}")

    print()


if __name__ == "__main__":
    test_clean_text()
