import os
import discord
from discord.ext import commands

TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # 레벨링(메시지 감지)에 필요
intents.members = True  # 티켓 등에서 멤버 정보 사용

bot = commands.Bot(command_prefix="!", intents=intents)

INITIAL_COGS = [
    "cogs.news",
    "cogs.ai_chat",
    "cogs.leveling",
    "cogs.tickets",
    "cogs.help",
]


@bot.event
async def on_ready():
    print(f"{bot.user} 로 로그인 완료")
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"동기화 실패: {e}")


async def main():
    async with bot:
        for cog in INITIAL_COGS:
            await bot.load_extension(cog)
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
