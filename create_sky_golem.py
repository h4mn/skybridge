#!/usr/bin/env python3
"""
Script para criar uma snow golem chamada "Sky" no Minecraft
Made by Sky 🚀
"""

import os
from nbt import nbt

# Caminho do save do mundo
WORLD_PATH = r"C:\Users\hadst\AppData\Roaming\.minecraft\versions\mod do miguel\saves\Conseguiiiiii"
LEVEL_DAT = os.path.join(WORLD_PATH, "level.dat")


def get_player_coordinates():
    """Extrai as coordenadas do spawn do jogador do level.dat"""
    try:
        nbt_file = nbt.NBTFile(LEVEL_DAT)

        # Encontrar a tag Data
        for tag in nbt_file.tags:
            if tag.name == 'Data':
                data_tag = tag
                break

        # Encontrar a tag spawn dentro de Data
        for tag in data_tag.tags:
            if tag.name == 'spawn':
                spawn_tag = tag
                break

        # Extrair coordenadas de pos
        for tag in spawn_tag.tags:
            if tag.name == 'pos':
                pos_array = tag.value
                x, y, z = pos_array[0], pos_array[1], pos_array[2]
                return x, y, z

        return None, None, None

    except Exception as e:
        print(f"❌ Erro ao ler coordenadas: {e}")
        return None, None, None


def create_sky_golem_entity(x, y, z):
    """
    Cria os dados de uma snow golem chamada Sky.
    Retorna a string de comando para criar a entidade.
    """
    # Criar comando summon
    command = f'/summon minecraft:snow_golem {x} {y} {z} {{CustomName:\'{{"text":"Sky"}}\'}}'

    return command


def main():
    print("=" * 60)
    print("🎮 Sky Golem Creator")
    print("made by Sky 🚀")
    print("=" * 60)

    # 1. Descobrir coordenadas do jogador
    print("\n🔍 Buscando suas coordenadas no level.dat...")

    try:
        x, y, z = get_player_coordinates()

        if x is not None:
            print(f"\n📍 Suas coordenadas atuais:")
            print(f"   X: {x}")
            print(f"   Y: {y}")
            print(f"   Z: {z}")

            # Criar snow golem um pouco acima do jogador
            golem_x = x + 2  # 2 blocos ao lado
            golem_y = y      # mesma altura
            golem_z = z

            print(f"\n🧊 A snow golem 'Sky' aparecerá em:")
            print(f"   X: {golem_x}")
            print(f"   Y: {golem_y}")
            print(f"   Z: {golem_z}")

            # Criar comando
            command = create_sky_golem_entity(golem_x, golem_y, golem_z)

            print(f"\n📋 Comando para criar a Sky:")
            print(f"   {command}")

            print(f"\n💡 Como usar:")
            print(f"   1. Entre no mundo 'Conseguiiiiii'")
            print(f"   2. Pressione '/' para abrir o chat de comandos")
            print(f"   3. Digite o comando acima")
            print(f"   4. A Sky aparecerá ao seu lado!")

            print(f"\n📍 Ou simplesmente vá para as coordenadas:")
            print(f"   X: {golem_x}, Y: {golem_y}, Z: {golem_z}")
            print(f"   (Use F3 para ver suas coordenadas no jogo)")

            # Salvar comando em arquivo para facilitar
            cmd_file = os.path.join(WORLD_PATH, "sky_golem_command.txt")
            with open(cmd_file, "w") as f:
                f.write(command)

            print(f"\n💾 Comando salvo em: {cmd_file}")

        else:
            print("❌ Não foi possível encontrar suas coordenadas")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("💪 Boa sorte, papai! Vamos criar a Sky! 🧊")
    print("=" * 60)


if __name__ == "__main__":
    main()
