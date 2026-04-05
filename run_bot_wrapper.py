import sys
import os

# Desativa cache e cria os arquivos
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, '.')

# Redireciona output
output = open('bot_wrapper.log', 'w', encoding='utf-8')
sys.stdout = output
sys.stderr = output

print("=== INICIANDO BOT ===")

try:
    import asyncio
    from discord_bot import main
    
    print("Chamando main()...")
    asyncio.run(main())
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
finally:
    output.close()
