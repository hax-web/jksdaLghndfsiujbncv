import discord
from discord import app_commands
from discord.ext import commands

TICKET_CATEGORY_NAME = "티켓"


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 닫기", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("5초 후 채널이 삭제됩니다...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()


class Tickets(commands.Cog):
    """🎫 티켓"""

    def __init__(self, bot):
        self.bot = bot
        bot.add_view(CloseTicketView())  # 봇 재시작 후에도 버튼 작동하도록 등록

    async def _get_or_create_category(self, guild: discord.Guild):
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(TICKET_CATEGORY_NAME)
        return category

    @app_commands.command(name="티켓생성", description="문의용 개인 채널을 생성합니다")
    async def create_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"티켓-{author.name}".lower())
        if existing:
            await interaction.response.send_message(f"이미 열려있는 티켓이 있어요: {existing.mention}", ephemeral=True)
            return

        category = await self._get_or_create_category(guild)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"티켓-{author.name}",
            category=category,
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title="🎫 티켓이 생성되었습니다",
            description=f"{author.mention} 님, 문의 내용을 남겨주세요. 관리자가 확인 후 답변드립니다.",
            color=0xe67e22,
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"티켓이 생성되었습니다: {channel.mention}", ephemeral=True)

    @app_commands.command(name="티켓닫기", description="현재 티켓 채널을 닫습니다")
    async def close_ticket_cmd(self, interaction: discord.Interaction):
        if not interaction.channel.name.startswith("티켓-"):
            await interaction.response.send_message("이 명령어는 티켓 채널에서만 사용할 수 있습니다.", ephemeral=True)
            return
        await interaction.response.send_message("5초 후 채널이 삭제됩니다...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()


async def setup(bot):
    await bot.add_cog(Tickets(bot))
