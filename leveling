import os
import json
import random
import discord
from discord import app_commands
from discord.ext import commands

DATA_FILE = "data/levels.json"
XP_PER_MESSAGE_MIN = 10
XP_PER_MESSAGE_MAX = 20
COOLDOWN_SECONDS = 30  # 도배 방지: 이 시간 안에는 XP 중복 지급 안 함


def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def load_data():
    _ensure_data_dir()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data):
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def xp_for_level(level):
    # 레벨이 오를수록 필요한 XP가 늘어나는 곡선
    return 5 * (level ** 2) + 50 * level + 100


class Leveling(commands.Cog):
    """📈 레벨링"""

    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return

        import time
        now = time.time()
        key = f"{message.guild.id}-{message.author.id}"
        last = self.cooldowns.get(key, 0)
        if now - last < COOLDOWN_SECONDS:
            return
        self.cooldowns[key] = now

        data = load_data()
        gid = str(message.guild.id)
        uid = str(message.author.id)
        data.setdefault(gid, {})
        data[gid].setdefault(uid, {"xp": 0, "level": 0})

        data[gid][uid]["xp"] += random.randint(XP_PER_MESSAGE_MIN, XP_PER_MESSAGE_MAX)

        level = data[gid][uid]["level"]
        needed = xp_for_level(level)
        if data[gid][uid]["xp"] >= needed:
            data[gid][uid]["xp"] -= needed
            data[gid][uid]["level"] += 1
            try:
                await message.channel.send(
                    f"🎉 {message.author.mention} 님이 레벨 {data[gid][uid]['level']}(으)로 올랐습니다!"
                )
            except discord.Forbidden:
                pass

        save_data(data)

    @app_commands.command(name="레벨", description="자신 또는 다른 사람의 레벨을 확인합니다")
    @app_commands.describe(유저="확인할 사용자 (비워두면 본인)")
    async def level(self, interaction: discord.Interaction, 유저: discord.Member = None):
        target = 유저 or interaction.user
        data = load_data()
        gid = str(interaction.guild.id)
        uid = str(target.id)
        info = data.get(gid, {}).get(uid, {"xp": 0, "level": 0})
        needed = xp_for_level(info["level"])

        embed = discord.Embed(title=f"{target.display_name} 님의 레벨", color=0xf1c40f)
        embed.add_field(name="레벨", value=str(info["level"]))
        embed.add_field(name="경험치", value=f"{info['xp']} / {needed}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="랭킹", description="서버 레벨 랭킹을 확인합니다")
    async def ranking(self, interaction: discord.Interaction):
        data = load_data()
        gid = str(interaction.guild.id)
        guild_data = data.get(gid, {})

        if not guild_data:
            await interaction.response.send_message("아직 랭킹 데이터가 없습니다.")
            return

        ranked = sorted(guild_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]

        lines = []
        for i, (uid, info) in enumerate(ranked, start=1):
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"알 수 없음({uid})"
            lines.append(f"**{i}.** {name} — 레벨 {info['level']} ({info['xp']} XP)")

        embed = discord.Embed(title="🏆 서버 레벨 랭킹", description="\n".join(lines), color=0xf1c40f)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Leveling(bot))
