#!/usr/bin/env python3
"""
Script para criar uma snow golem chamada "Sky" no Minecraft
Made by Sky 🚀
"""

import gzip
import struct
import os
import json

# Caminho do save do mundo
WORLD_PATH = r"C:\Users\hadst\AppData\Roaming\.minecraft\versions\mod do miguel\saves\Conseguiiiiii"
LEVEL_DAT = os.path.join(WORLD_PATH, "level.dat")


def simple_nbt_parser(data):
    """
    Parser simples de NBT para extrair informações básicas.
    NBT (Named Binary Tag) format:
    - TAG_Compound: 0x0A
    - TAG_Int: 0x03
    - TAG_String: 0x08
    - TAG_List: 0x09
    - TAG_Long: 0x04
    """
    pos = 0
    result = {}

    def parse_tag(pos, name=None):
        if pos >= len(data):
            return pos, {}

        tag_type = data[pos]
        pos += 1

        if tag_type == 0x00:  # TAG_End
            return pos, {}

        # Read tag name
        name_length = struct.unpack('>H', data[pos:pos+2])[0]
        pos += 2
        tag_name = data[pos:pos+name_length].decode('utf-8')
        pos += name_length

        if tag_type == 0x03:  # TAG_Int
            value = struct.unpack('>i', data[pos:pos+4])[0]
            pos += 4
            return pos, {tag_name: value}

        elif tag_type == 0x04:  # TAG_Long
            value = struct.unpack('>q', data[pos:pos+8])[0]
            pos += 8
            return pos, {tag_name: value}

        elif tag_type == 0x05:  # TAG_Float
            value = struct.unpack('>f', data[pos:pos+4])[0]
            pos += 4
            return pos, {tag_name: value}

        elif tag_type == 0x06:  # TAG_Double
            value = struct.unpack('>d', data[pos:pos+8])[0]
            pos += 8
            return pos, {tag_name: value}

        elif tag_type == 0x08:  # TAG_String
            str_length = struct.unpack('>H', data[pos:pos+2])[0]
            pos += 2
            value = data[pos:pos+str_length].decode('utf-8')
            pos += str_length
            return pos, {tag_name: value}

        elif tag_type == 0x09:  # TAG_List
            list_type = data[pos]
            pos += 1
            list_length = struct.unpack('>i', data[pos:pos+4])[0]
            pos += 4
            items = []
            for _ in range(list_length):
                pos, item = parse_tag(pos)
                items.append(item)
            return pos, {tag_name: items}

        elif tag_type == 0x0A:  # TAG_Compound
            compound = {}
            while True:
                new_pos, item = parse_tag(pos)
                pos = new_pos
                if not item:  # TAG_End
                    break
                compound.update(item)
            return pos, {tag_name: compound}

        return pos, {}

    pos, result = parse_tag(0)
    return result


def get_spawn_coordinates():
    """Extrai as coordenadas de spawn do level.dat"""
    try:
        with open(LEVEL_DAT, 'rb') as f:
            # O level.dat é um arquivo gzip
            with gzip.GzipFile(fileobj=f) as gz:
                data = gz.read()

        nbt_data = simple_nbt_parser(data)

        if 'Data' in nbt_data:
            data = nbt_data['Data']
            spawn_x = data.get('SpawnX', 0)
            spawn_y = data.get('SpawnY', 64)
            spawn_z = data.get('SpawnZ', 0)

            print(f"📍 Coordenadas de spawn encontradas:")
            print(f"   X: {spawn_x}")
            print(f"   Y: {spawn_y}")
            print(f"   Z: {spawn_z}")

            return spawn_x, spawn_y, spawn_z
        else:
            print("❌ Não foi possível encontrar a tag 'Data' no arquivo")
            return 0, 64, 0

    except Exception as e:
        print(f"❌ Erro ao ler level.dat: {e}")
        return 0, 64, 0


def create_sky_golem(x, y, z):
    """
    Cria uma snow golem chamada Sky nas coordenadas especificadas.
    Nota: Snow golems precisam de 2 blocos de altura.
    """
    print(f"\n🧊 Criando snow golem 'Sky' em:")
    print(f"   X: {x}")
    print(f"   Y: {y}")
    print(f"   Z: {z}")
    print(f"\n📝 Informações:")
    print(f"   - A snow golem aparecerá quando você carregar o chunk")
    print(f"   - Ela vai se chamar 'Sky'")
    print(f"   - Precisa de pelo menos 2 blocos de espaço")

    return x, y, z


def main():
    print("=" * 50)
    print("🎮 Sky Golem Creator")
    print("made by Sky 🚀")
    print("=" * 50)

    # 1. Descobrir coordenadas do jogador
    print("\n🔍 Buscando coordenadas de spawn...")
    spawn_x, spawn_y, spawn_z = get_spawn_coordinates()

    # 2. Criar snow golem próximo ao spawn
    # Colocar um pouco acima para garantir que não underground
    golem_y = spawn_y + 3

    print(f"\n🎯 Posição da snow golem:")
    print(f"   X: {spawn_x}")
    print(f"   Y: {golem_y}")
    print(f"   Z: {spawn_z}")

    print(f"\n📋 Coordenadas para você encontrar a Sky:")
    print(f"   {spawn_x}, {golem_y}, {spawn_z}")

    print(f"\n✨ Pronto! Entre no mundo e procure:")
    print(f"   X: {spawn_x}")
    print(f"   Z: {spawn_z}")
    print(f"   (A Sky vai estar em Y={golem_y})")

    print("\n" + "=" * 50)
    print("💪 Good luck, papai!")
    print("=" * 50)


if __name__ == "__main__":
    main()
