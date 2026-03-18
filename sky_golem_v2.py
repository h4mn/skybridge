#!/usr/bin/env python3
"""
Script para ler o level.dat e criar uma snow golem chamada "Sky"
Made by Sky 🚀
"""

import os
from nbt import nbt

# Caminho do save do mundo
WORLD_PATH = r"C:\Users\hadst\AppData\Roaming\.minecraft\versions\mod do miguel\saves\Conseguiiiiii"
LEVEL_DAT = os.path.join(WORLD_PATH, "level.dat")


def main():
    print("=" * 50)
    print("🎮 Sky Golem Creator v2")
    print("made by Sky 🚀")
    print("=" * 50)

    try:
        # Ler o arquivo level.dat
        print("\n🔍 Lendo level.dat...")
        nbt_file = nbt.NBTFile(LEVEL_DAT)

        # Extrair coordenadas de spawn
        # A estrutura é: Data -> SpawnX, SpawnY, SpawnZ
        data_tag = nbt_file.get("Data")

        if data_tag:
            spawn_x = data_tag.get("SpawnX").value
            spawn_y = data_tag.get("SpawnY").value
            spawn_z = data_tag.get("SpawnZ").value

            print(f"\n📍 Coordenadas de spawn encontradas:")
            print(f"   X: {spawn_x}")
            print(f"   Y: {spawn_y}")
            print(f"   Z: {spawn_z}")

            # Coordenadas para a snow golem (um pouco acima do spawn)
            golem_x = spawn_x
            golem_y = spawn_y + 3
            golem_z = spawn_z

            print(f"\n🧊 A snow golem 'Sky' será criada em:")
            print(f"   X: {golem_x}")
            print(f"   Y: {golem_y}")
            print(f"   Z: {golem_z}")

            print(f"\n📋 Para encontrar a Sky no jogo, vá para:")
            print(f"   X: {golem_x}, Y: {golem_y}, Z: {golem_z}")

            print(f"\n💡 Dica: Use F3 no jogo para ver suas coordenadas!")

        else:
            print("❌ Não encontrou a tag 'Data' no arquivo NBT")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("💪 Boa sorte, papai!")
    print("=" * 50)


if __name__ == "__main__":
    main()
