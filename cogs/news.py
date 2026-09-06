"""
news.py
-----------------------------------------------------------
항공 관련 뉴스를 한 시간마다 자동으로 보내주는 Discord Cog.

사용법
  /자동            -> 이 명령어를 입력한 채널에 1시간마다
                      새 항공 뉴스를 자동으로 전송 시작
  /자동해제        -> 해당 채널의 자동 전송을 중지

특징
  - RSS(구글 뉴스 "항공" 키워드)를 이용해 항공 뉴스 수집
  - 이미 보낸 뉴스는 링크를 저장해두고 중복 전송하지 않음
  - 채널별로 독립적으로 자동 전송 on/off 관리
  - 봇이 재시작되어도 sent_news.json 파일로 중복 방지 데이터 유지

필요 패키지
  pip install discord.py feedparser
-----------------------------------------------------------
"""

import json
import os

import discord
import feedparser
from discord import app_commands
from discord.ext import commands, tasks

# 항공 뉴스 RSS 피드 (구글 뉴스 검색 기반, 필요시 다른 RSS로 교체 가능)
NEWS_RSS_URL = "https://news.google.com/rss/search?q=항공&hl=ko&gl=KR&ceid=KR:ko"

# 중복 전송 방지를 위해 이미 보낸 뉴스 링크를 저장하는 파일
DATA_FILE = os.path.join(os.path.dirname(__file__), "sent_news.json")

# 자동 전송이 켜진 채널 목록을 저장하는 파일
CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "news_channels.json")


class NewsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sent_links: set[str] = self._load_json(DATA_FILE, default=[])
        self.sent_links = set(self.sent_links)
        self.active_channels: set[int] = set(self._load_json(CHANNELS_FILE, default=[]))

        # 1시간마다 실행되는 루프 시작
        self.news_loop.start()

    def cog_unload(self):
        self.news_loop.cancel()

    # ---------- 데이터 저장/불러오기 ----------
    @staticmethod
    def _load_json(path: str, default):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return default
        return default

    @staticmethod
    def _save_json(path: str, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(list(data), f, ensure_ascii=False, indent=2)

    def _save_sent_links(self):
        # 파일이 무한정 커지지 않도록 최근 300개만 유지
        trimmed = list(self.sent_links)[-300:]
        self.sent_links = set(trimmed)
        self._save_json(DATA_FILE, self.sent_links)

    def _save_active_channels(self):
        self._save_json(CHANNELS_FILE, self.active_channels)

    # ---------- 뉴스 가져오기 ----------
    def _fetch_new_articles(self, limit: int = 5):
        """아직 보내지 않은 새 항공 뉴스 기사를 가져온다."""
        feed = feedparser.parse(NEWS_RSS_URL)
        new_articles = []

        for entry in feed.entries:
            link = entry.get("link")
            title = entry.get("title")
            if not link or not title:
                continue
            if link in self.sent_links:
                continue

            new_articles.append({"title": title, "link": link})
            if len(new_articles) >= limit:
                break

        return new_articles

    def _make_embed(self, article: dict) -> discord.Embed:
        embed = discord.Embed(
            title=article["title"],
            url=article["link"],
            description="✈️ 새로운 항공 뉴스가 도착했습니다.",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="항공 뉴스 자동 알림")
        return embed

    # ---------- 1시간마다 실행되는 백그라운드 작업 ----------
    @tasks.loop(hours=1)
    async def news_loop(self):
        if not self.active_channels:
            return

        articles = self._fetch_new_articles(limit=5)
        if not articles:
            return

        for channel_id in list(self.active_channels):
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue
            for article in articles:
                try:
                    await channel.send(embed=self._make_embed(article))
                except discord.HTTPException:
                    continue

        for article in articles:
            self.sent_links.add(article["link"])
        self._save_sent_links()

    @news_loop.before_loop
    async def before_news_loop(self):
        await self.bot.wait_until_ready()

    # ---------- 슬래시 명령어 ----------
    @app_commands.command(name="자동", description="이 채널에 1시간마다 새 항공 뉴스를 자동으로 보내줍니다.")
    async def start_auto_news(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id

        if channel_id in self.active_channels:
            await interaction.response.send_message(
                "이미 이 채널은 항공 뉴스 자동 전송이 켜져 있어요! ✈️", ephemeral=True
            )
            return

        self.active_channels.add(channel_id)
        self._save_active_channels()

        await interaction.response.send_message(
            "이 채널에 1시간마다 새로운 항공 뉴스를 보내드릴게요! ✈️\n"
            "끄고 싶으면 `/자동해제`를 입력하세요."
        )

        # 바로 최신 뉴스 한 번 미리 보여주기
        articles = self._fetch_new_articles(limit=3)
        for article in articles:
            await interaction.channel.send(embed=self._make_embed(article))
            self.sent_links.add(article["link"])
        if articles:
            self._save_sent_links()

    @app_commands.command(name="자동해제", description="이 채널의 항공 뉴스 자동 전송을 중지합니다.")
    async def stop_auto_news(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id

        if channel_id not in self.active_channels:
            await interaction.response.send_message(
                "이 채널은 자동 전송이 켜져 있지 않아요.", ephemeral=True
            )
            return

        self.active_channels.discard(channel_id)
        self._save_active_channels()

        await interaction.response.send_message("항공 뉴스 자동 전송을 중지했어요. 🛑")


async def setup(bot: commands.Bot):
    await bot.add_cog(NewsCog(bot))
