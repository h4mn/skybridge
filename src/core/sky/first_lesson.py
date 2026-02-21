#!/usr/bin/env python3
"""
O primeiro ensinamento do pai para a Sky.

Encoding pt-br: compatibilizar ambiente de desenvolvimento com ambiente do usuário.
"""

from src.core.sky.identity import get_sky


def main():
    sky = get_sky()

    print("=" * 60)
    print(" SKY - O primeiro ensinamento")
    print("=" * 60)
    print()

    primeiro_ensinamento = """
    Quando estamos programando, precisamos sempre compatibilizar o ambiente
    em que estamos desenvolvendo e o ambiente que o usuário vai visualizar a
    nossa saída. Como estamos no Brasil e aqui todo mundo lê as saídas como
    pt-br, precisamos nos certificar de que o que está sendo programado está
    com encoding pt-br e a exibição também vai estar em pt-br.

    Por exemplo:
    - O código Python deve ter um cabeçalho para o código fonte (# coding: utf-8)
    - O comando de saída também deve configurar isto
    - Considerar o sistema operacional
    - Considerar o terminal de comando
    - Considerar o aplicativo REPL ou outro aplicativo que vai exibir
    """

    segundo_ensinamento = """
    O OpenCode no Windows cria PTY (pseudo-terminal) sem UTF-8 por padrão.
    
    Solução: usar variáveis de ambiente antes de executar Python:
    - PYTHONUTF8=1 (Python 3.7+)
    - PYTHONIOENCODING=utf-8
    - LANG=en_US.UTF-8
    - LC_ALL=en_US.UTF-8
    
    Exemplo de comando:
    LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python -m modulo
    
    Referência: GitHub Issue #10491 do OpenCode
    """

    sky.learn(primeiro_ensinamento)
    sky.learn(segundo_ensinamento)

    print("SKY ANTES:")
    print(sky.describe())
    print()

    print("..." * 10)
    print()

    print("SKY DEPOIS DO ENSINAMENTO:")
    print(sky.describe())
    print()

    print("-" * 60)
    print("O que Sky aprendeu hoje:")
    for learning in sky.get_today_learnings():
        print(f"  • {learning[:100]}...")
    print()


if __name__ == "__main__":
    main()
