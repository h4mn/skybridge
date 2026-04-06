"""
Módulo de soma aritmética simples.
Implementa a operação: resultado = resultado + 1

Autor: Sky (via Ralph Loop)
Versão: 1.0.0
"""

from typing import Union


def soma(resultado: Union[int, float]) -> Union[int, float]:
    """
    Soma 1 ao resultado fornecido.

    Implementação direta: resultado = resultado + 1

    Args:
        resultado: Valor numérico inicial (int ou float)

    Returns:
        Valor incrementado em 1

    Examples:
        >>> soma(0)
        1
        >>> soma(5)
        6
        >>> soma(5.5)
        6.5
        >>> soma(-10)
        -9
    """
    novo_resultado = resultado + 1
    return novo_resultado


def main():
    """Função principal para demonstrar a soma."""
    print("=== SOMA: resultado = resultado + 1 ===\n")

    # Teste com inteiros
    print("Teste com inteiros:")
    resultado = 0
    print(f"  Inicial: {resultado}")

    for i in range(5):
        resultado = soma(resultado)
        print(f"  Iteração {i+1}: {resultado}")

    # Teste com float
    print("\nTeste com float:")
    print(f"  soma(5.5) = {soma(5.5)}")

    # Teste com negativo
    print("\nTeste com negativo:")
    print(f"  soma(-10) = {soma(-10)}")

    print(f"\nResultado final: {resultado}")


if __name__ == "__main__":
    main()
