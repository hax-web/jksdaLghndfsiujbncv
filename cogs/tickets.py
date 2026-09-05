import discord
from discord import app_commands
from discord.ext import commands

TICKET_CATEGORY_NAME = "티켓"


class CreateTicketView(discord.ui.View):
    """안내 메시지에 붙는, 유저가 누르면 티켓을 생성하는 버튼"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 티켓 생성", style=discord.ButtonStyle.primary, custom_id="create_ticket_button")
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await Tickets.make_ticket(interaction)


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
        bot.add_view(CreateTicketView())  # 봇 재시작 후에도 버튼 작동하도록 등록
        bot.add_view(CloseTicketView())

    @staticmethod
    async def _get_or_create_category(guild: discord.Guild):
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(TICKET_CATEGORY_NAME)
        return category

    @staticmethod
    async def make_ticket(interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"티켓-{author.name}".lower())
        if existing:
            await interaction.response.send_message(f"이미 열려있는 티켓이 있어요: {existing.mention}", ephemeral=True)
            return

        category = await Tickets._get_or_create_category(guild)

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

    @app_commands.command(name="티켓패널", description="이 채널에 '티켓 생성' 버튼이 있는 안내 메시지를 올립니다")
    @app_commands.describe(설명="버튼 위에 보여줄 안내 문구 (비워두면 기본 문구 사용)")
    async def ticket_panel(self, interaction: discord.Interaction, 설명: str = None):
        description = 설명 or "문의사항이 있으시면 아래 버튼을 눌러 티켓을 생성해주세요."

        embed = discord.Embed(
            title="🎫 문의 티켓",
            description=description,
            color=0xe67e22,
        )
        await interaction.channel.send(embed=embed, view=CreateTicketView())
        await interaction.response.send_message("✅ 티켓 안내 메시지를 올렸습니다.", ephemeral=True)

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
