import os
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import feedparser

CHECK_INTERVAL_MINUTES = 60
SEEN_FILE = "data/seen_news.json"
CONFIG_FILE = "data/news_config.json"
RSS_URL = "https://news.google.com/rss/search?q=비행기+OR+항공기&hl=ko&gl=KR&ceid=KR:ko"


def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def load_seen():
    _ensure_data_dir()
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    _ensure_data_dir()
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)


def load_channel_id():
    _ensure_data_dir()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("channel_id")
    return None


def save_channel_id(channel_id):
    _ensure_data_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"channel_id": channel_id}, f)


def fetch_latest_news(limit=5):
    feed = feedparser.parse(RSS_URL)
    return feed.entries[:limit]


def _entry_key(entry):
    # 구글 뉴스 링크는 매번 다른 추적 코드가 붙어 바뀔 수 있어서,
    # 링크 대신 기사 고유 id(guid)로 비교해 중복 전송을 막는다.
    return entry.get("id") or entry.link


def search_news(keyword, limit=5):
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    return feed.entries[:limit]


class News(commands.Cog):
    """✈️ 항공 뉴스"""

    def __init__(self, bot):
        self.bot = bot
        self.check_news.start()

    def cog_unload(self):
        self.check_news.cancel()

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_news(self):
        channel_id = load_channel_id()
        if channel_id is None:
            return
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return

        seen = load_seen()
        entries = fetch_latest_news(limit=50)  # 넉넉하게 가져와서 누락 방지
        new_entries = [e for e in entries if _entry_key(e) not in seen]

        for entry in reversed(new_entries):
            embed = discord.Embed(
                title=entry.title,
                url=entry.link,
                description=getattr(entry, "published", ""),
                color=0x3498db,
            )
            embed.set_footer(text="✈️ 항공 뉴스 알림")
            await channel.send(embed=embed)
            seen.add(_entry_key(entry))

        if new_entries:
            save_seen(seen)

    @check_news.before_loop
    async def before_check_news(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="비행기뉴스", description="최신 항공 뉴스를 바로 확인합니다")
    async def airplane_news(self, interaction: discord.Interaction):
        await interaction.response.defer()
        entries = fetch_latest_news(limit=5)
        if not entries:
            await interaction.followup.send("뉴스를 가져오지 못했습니다.")
            return
        embeds = [
            discord.Embed(title=e.title, url=e.link, description=getattr(e, "published", ""), color=0x3498db)
            for e in entries
        ]
        await interaction.followup.send(embeds=embeds)

    @app_commands.command(name="항공검색", description="키워드로 항공 관련 뉴스를 검색합니다")
    @app_commands.describe(키워드="검색할 단어 (예: 대한항공, 보잉, 공항 등)")
    async def airplane_search(self, interaction: discord.Interaction, 키워드: str):
        await interaction.response.defer()
        entries = search_news(키워드, limit=5)
        if not entries:
            await interaction.followup.send(f"'{키워드}' 관련 뉴스를 찾지 못했습니다.")
            return
        embeds = [
            discord.Embed(title=e.title, url=e.link, description=getattr(e, "published", ""), color=0x2ecc71)
            for e in entries
        ]
        await interaction.followup.send(embeds=embeds)

    @app_commands.command(name="자동", description="이 채널에 항공 뉴스 자동 알림을 설정합니다")
    async def set_auto_channel(self, interaction: discord.Interaction):
        save_channel_id(interaction.channel.id)
        await interaction.response.send_message(
            f"✅ 이 채널에 앞으로 {CHECK_INTERVAL_MINUTES}분마다 새 항공 뉴스를 자동으로 보내드릴게요!"
        )

    @app_commands.command(name="자동해제", description="항공 뉴스 자동 알림을 끕니다")
    async def unset_auto_channel(self, interaction: discord.Interaction):
        save_channel_id(None)
        await interaction.response.send_message("🔕 자동 알림을 껐습니다.")


async def setup(bot):
    await bot.add_cog(News(bot))
