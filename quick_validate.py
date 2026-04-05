import asyncio, os, discord
from dotenv import load_dotenv

load_dotenv()

async def check():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        forum = client.get_channel(1490026271445483762)
        print(f"\n✅ FÓRUM: {forum.name}")
        print(f"🏷️  TAGS: {len(forum.tags)}")
        for t in forum.tags: print(f"   {t.emoji} {t.name}")

        count = 0
        async for thread in forum.active_threads(limit=None):
            count += 1
            print(f"\n📝 POST {count}: {thread.name}")

        print(f"\n📊 TOTAL: {count} posts criados")
        print(f"🔗 URL: https://discord.com/channels/208357890317221888/1490026271445483762\n")
        await client.close()

    await client.start(os.getenv("DISCORD_BOT_TOKEN"))

asyncio.run(check())
