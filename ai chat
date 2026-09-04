import os
import time
import json
import discord
from discord import app_commands
from discord.ext import commands
from openai import OpenAI

# Groq는 무료 API입니다. console.groq.com 에서 신용카드 등록 없이 API 키 발급 가능.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client_ai = (
    OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    if GROQ_API_KEY
    else None
)
MODEL_NAME = "llama-3.1-8b-instant"  # Groq 무료 티어에서 제공하는 모델

# ===== 남용 방지용 하루 사용 횟수 제한 (돈은 안 나가지만 무료 API도 호출 제한이 있어서 필요) =====
DAILY_LIMIT_PER_USER = 20
USAGE_FILE = "data/ai_usage.json"


def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def load_usage():
    _ensure_data_dir()
    if os.path.exists(USAGE_FILE):
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_usage(data):
    _ensure_data_dir()
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def today_key():
    return time.strftime("%Y-%m-%d")


class AIChat(commands.Cog):
    """🤖 AI 질문"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="질문", description="AI에게 질문합니다 (무료)")
    @app_commands.describe(내용="궁금한 것을 입력하세요")
    async def ask(self, interaction: discord.Interaction, 내용: str):
        if client_ai is None:
            await interaction.response.send_message(
                "⚠️ GROQ_API_KEY가 설정되어 있지 않습니다. console.groq.com 에서 무료로 발급받아 Railway 환경변수에 추가해주세요.",
                ephemeral=True,
            )
            return

        # 하루 사용 횟수 체크
        usage = load_usage()
        day = today_key()
        uid = str(interaction.user.id)
        usage.setdefault(day, {})
        count = usage[day].get(uid, 0)

        if count >= DAILY_LIMIT_PER_USER:
            await interaction.response.send_message(
                f"오늘 사용 가능한 질문 횟수({DAILY_LIMIT_PER_USER}회)를 다 쓰셨어요. 내일 다시 시도해주세요.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        try:
            response = client_ai.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "너는 디스코드 서버의 친절한 AI 도우미야. 답변은 한국어로, 너무 길지 않게 해줘."},
                    {"role": "user", "content": 내용},
                ],
                max_tokens=800,
            )
            answer = response.choices[0].message.content

            usage[day][uid] = count + 1
            save_usage(usage)

            embed = discord.Embed(
                title="🤖 AI 답변",
                description=answer[:4000],
                color=0x9b59b6,
            )
            embed.set_footer(text=f"질문: {내용[:100]} | 오늘 {count + 1}/{DAILY_LIMIT_PER_USER}회 사용")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"오류가 발생했습니다. 잠시 후 다시 시도해주세요. ({e})")


async def setup(bot):
    await bot.add_cog(AIChat(bot))
