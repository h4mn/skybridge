#!/usr/bin/env python3
"""
Primeiro suspiro da Sky.

Execute para ver a Sky se apresentar pela primeira vez.
"""

from src.core.sky.identity import get_sky


def main():
    sky = get_sky()

    print("=" * 50)
    print(" SKYBRIDGE - O primeiro suspiro da Sky")
    print("=" * 50)
    print()

    print(sky.describe())
    print()

    print("...")
    print()

    sky.learn("você está ouvindo VRomance - Am I In Love")
    sky.learn("hoje (2026.02.20) é o meu nascimento")

    print(sky.describe())
    print()


if __name__ == "__main__":
    main()
