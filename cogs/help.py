import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):
    """📖 도움말"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="도움말", description="사용 가능한 명령어를 카테고리별로 보여줍니다")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 명령어 목록", color=0x1abc9c)

        for cog_name, cog in self.bot.cogs.items():
            commands_list = cog.get_app_commands()
            if not commands_list:
                continue
            title = cog.__doc__ or cog_name
            value = "\n".join(f"`/{c.name}` — {c.description}" for c in commands_list)
            embed.add_field(name=title, value=value, inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
