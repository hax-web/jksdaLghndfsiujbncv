import os
import random
import sqlite3
import asyncio
from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
DB_PATH = "bot.db"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

db = sqlite3.connect(DB_PATH)
db.execute("""CREATE TABLE IF NOT EXISTS levels (
    guild_id INTEGER,
    user_id INTEGER,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    PRIMARY KEY (guild_id, user_id)
)""")
db.execute("""CREATE TABLE IF NOT EXISTS settings (
    guild_id INTEGER PRIMARY KEY,
    level_channel INTEGER,
    ticket_category INTEGER,
    ticket_log_channel INTEGER,
    timed_channel INTEGER,
    timed_hour INTEGER,
    timed_minute INTEGER,
    timed_message TEXT
)""")
db.execute("""CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER,
    channel_id INTEGER,
    hour INTEGER,
    minute INTEGER,
    message TEXT,
    last_sent_date TEXT
)""")
db.commit()

xp_cooldown = {}

def get_settings(guild_id):
    row = db.execute("SELECT * FROM settings WHERE guild_id=?", (guild_id,)).fetchone()
    if not row:
        db.execute("INSERT INTO settings(guild_id) VALUES(?)", (guild_id,))
        db.commit()
        return get_settings(guild_id)
    return row

def set_setting(guild_id, column, value):
    get_settings(guild_id)
    db.execute(f"UPDATE settings SET {column}=? WHERE guild_id=?", (value, guild_id))
    db.commit()

def is_admin(interaction):
    return interaction.user.guild_permissions.manage_guild

async def admin_only(interaction):
    if not is_admin(interaction):
        await interaction.response.send_message("관리자 권한이 필요합니다.", ephemeral=True)
        return False
    return True

@bot.event
async def on_ready():
    await bot.tree.sync()
    timed_message_loop.start()
    print(f"로그인 완료: {bot.user} ({bot.user.id})")

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    now = datetime.now().timestamp()
    key = (message.guild.id, message.author.id)
    if now - xp_cooldown.get(key, 0) >= 60:
        xp_cooldown[key] = now
        row = db.execute(
            "SELECT xp, level FROM levels WHERE guild_id=? AND user_id=?",
            (message.guild.id, message.author.id)
        ).fetchone()

        if row:
            xp, level = row
        else:
            xp, level = 0, 1

        xp += random.randint(10, 20)
        needed = level * 100
        if xp >= needed:
            xp -= needed
            level += 1
            settings = get_settings(message.guild.id)
            channel_id = settings[1]
            channel = message.guild.get_channel(channel_id) if channel_id else None
            if channel:
                await channel.send(f"🎉 {message.author.mention} 레벨 **{level}** 달성!")

        db.execute(
            "INSERT OR REPLACE INTO levels(guild_id,user_id,xp,level) VALUES(?,?,?,?)",
            (message.guild.id, message.author.id, xp, level)
        )
        db.commit()

    await bot.process_commands(message)

# ---------------- 미니게임 ----------------

@bot.tree.command(name="홀짝", description="1~10의 숫자가 홀수인지 짝수인지 맞힙니다.")
@app_commands.describe(선택="홀 또는 짝")
async def odd_even(interaction: discord.Interaction, 선택: str):
    if 선택 not in ("홀", "짝"):
        await interaction.response.send_message("`홀` 또는 `짝`만 입력하세요.", ephemeral=True)
        return
    number = random.randint(1, 10)
    answer = "홀" if number % 2 else "짝"
    result = "정답!" if 선택 == answer else "틀렸습니다!"
    await interaction.response.send_message(f"🎲 숫자: **{number}** → **{answer}**\n{result}")

@bot.tree.command(name="가위바위보", description="봇과 가위바위보를 합니다.")
@app_commands.describe(선택="가위, 바위, 보")
async def rps(interaction: discord.Interaction, 선택: str):
    choices = ["가위", "바위", "보"]
    if 선택 not in choices:
        await interaction.response.send_message("가위/바위/보 중 하나를 입력하세요.", ephemeral=True)
        return
    bot_choice = random.choice(choices)
    if 선택 == bot_choice:
        result = "무승부!"
    elif (선택, bot_choice) in [("가위","보"), ("바위","가위"), ("보","바위")]:
        result = "승리!"
    else:
        result = "패배!"
    await interaction.response.send_message(f"✊ 선택: {선택}\n🤖 봇: {bot_choice}\n**{result}**")

@bot.tree.command(name="주사위", description="주사위를 굴립니다.")
async def dice(interaction: discord.Interaction):
    await interaction.response.send_message(f"🎲 **{random.randint(1, 6)}**")

@bot.tree.command(name="숫자맞히기", description="1~10 중 봇이 고른 숫자를 맞힙니다.")
@app_commands.describe(숫자="1~10 사이 숫자")
async def number_guess(interaction: discord.Interaction, 숫자: int):
    if not 1 <= 숫자 <= 10:
        await interaction.response.send_message("1~10 사이로 입력하세요.", ephemeral=True)
        return
    answer = random.randint(1, 10)
    await interaction.response.send_message(
        f"🎯 정답은 **{answer}**\n" + ("정답입니다!" if 숫자 == answer else "아쉽네요!")
    )

# ---------------- 관리 ----------------

@bot.tree.command(name="청소", description="현재 채널의 메시지를 삭제합니다.")
@app_commands.describe(개수="삭제할 메시지 수")
async def clear(interaction: discord.Interaction, 개수: app_commands.Range[int, 1, 100]):
    if not await admin_only(interaction):
        return
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=개수)
    await interaction.followup.send(f"🧹 {len(deleted)}개의 메시지를 삭제했습니다.", ephemeral=True)

@bot.tree.command(name="추방", description="멤버를 서버에서 추방합니다.")
@app_commands.describe(멤버="추방할 멤버", 사유="사유")
async def kick(interaction: discord.Interaction, 멤버: discord.Member, 사유: str = "사유 없음"):
    if not await admin_only(interaction):
        return
    await 멤버.kick(reason=사유)
    await interaction.response.send_message(f"👢 {멤버.mention} 추방 완료.")

@bot.tree.command(name="차단", description="멤버를 서버에서 차단합니다.")
@app_commands.describe(멤버="차단할 멤버", 사유="사유")
async def ban(interaction: discord.Interaction, 멤버: discord.Member, 사유: str = "사유 없음"):
    if not await admin_only(interaction):
        return
    await 멤버.ban(reason=사유)
    await interaction.response.send_message(f"🔨 {멤버} 차단 완료.")

@bot.tree.command(name="공지", description="현재 채널에 공지를 보냅니다.")
@app_commands.describe(내용="공지 내용")
async def announce(interaction: discord.Interaction, 내용: str):
    if not await admin_only(interaction):
        return
    embed = discord.Embed(title="📢 공지", description=내용, color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)

# ---------------- 레벨 ----------------

@bot.tree.command(name="레벨", description="내 레벨을 확인합니다.")
@app_commands.describe(멤버="확인할 멤버")
async def level(interaction: discord.Interaction, 멤버: discord.Member = None):
    member = 멤버 or interaction.user
    row = db.execute(
        "SELECT xp, level FROM levels WHERE guild_id=? AND user_id=?",
        (interaction.guild.id, member.id)
    ).fetchone()
    xp, lvl = row if row else (0, 1)
    await interaction.response.send_message(f"⭐ {member.mention} | 레벨 **{lvl}** | XP **{xp}/{lvl*100}**")

@bot.tree.command(name="랭킹", description="서버 레벨 랭킹을 확인합니다.")
async def ranking(interaction: discord.Interaction):
    rows = db.execute(
        "SELECT user_id, level, xp FROM levels WHERE guild_id=? ORDER BY level DESC, xp DESC LIMIT 10",
        (interaction.guild.id,)
    ).fetchall()
    if not rows:
        await interaction.response.send_message("아직 레벨 데이터가 없습니다.")
        return
    lines = []
    for i, (uid, lvl, xp) in enumerate(rows, 1):
        member = interaction.guild.get_member(uid)
        name = member.display_name if member else f"사용자 {uid}"
        lines.append(f"**{i}.** {name} — Lv.{lvl} ({xp} XP)")
    await interaction.response.send_message("🏆 **레벨 랭킹**\n" + "\n".join(lines))

@bot.tree.command(name="레벨채널", description="레벨업 알림 채널을 설정합니다.")
@app_commands.describe(채널="알림 채널")
async def level_channel(interaction: discord.Interaction, 채널: discord.TextChannel):
    if not await admin_only(interaction):
        return
    set_setting(interaction.guild.id, "level_channel", 채널.id)
    await interaction.response.send_message(f"⭐ 레벨업 채널을 {채널.mention}으로 설정했습니다.")

# ---------------- 티켓 ----------------

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 티켓 생성", style=discord.ButtonStyle.primary, custom_id="ticket_create")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        settings = get_settings(guild.id)
        category = guild.get_channel(settings[2]) if settings[2] else None

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.id}")
        if existing:
            await interaction.response.send_message(f"이미 티켓이 있습니다: {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        for role in guild.roles:
            if role.permissions.manage_guild:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites,
            reason="티켓 생성"
        )
        await channel.send(
            f"{interaction.user.mention} 티켓이 생성되었습니다.",
            view=CloseTicketView()
        )
        await interaction.response.send_message(f"🎫 티켓 생성: {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 티켓 닫기", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not (interaction.user.guild_permissions.manage_guild or
                interaction.channel.name == f"ticket-{interaction.user.id}"):
            await interaction.response.send_message("티켓을 닫을 권한이 없습니다.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 티켓을 닫습니다.")
        await asyncio.sleep(2)
        await interaction.channel.delete(reason="티켓 종료")

@bot.tree.command(name="티켓설정", description="티켓 생성 패널을 현재 채널에 설치합니다.")
async def ticket_setup(interaction: discord.Interaction):
    if not await admin_only(interaction):
        return
    embed = discord.Embed(
        title="🎫 고객지원 티켓",
        description="문의가 필요하면 아래 버튼을 눌러 티켓을 생성하세요.",
        color=discord.Color.blurple()
    )
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("티켓 패널을 설치했습니다.", ephemeral=True)

@bot.tree.command(name="티켓카테고리", description="티켓이 생성될 카테고리를 설정합니다.")
@app_commands.describe(카테고리="티켓 카테고리")
async def ticket_category(interaction: discord.Interaction, 카테고리: discord.CategoryChannel):
    if not await admin_only(interaction):
        return
    set_setting(interaction.guild.id, "ticket_category", 카테고리.id)
    await interaction.response.send_message(f"🎫 티켓 카테고리: **{카테고리.name}**")

# ---------------- 시간 채팅 ----------------

@bot.tree.command(name="반복채팅추가", description="정해진 시간마다 특정 채널에 자동 메시지를 보내도록 추가합니다.")
@app_commands.describe(채널="메시지를 보낼 채널", 시="0~23", 분="0~59", 내용="자동으로 보낼 메시지")
async def schedule_add(interaction: discord.Interaction, 채널: discord.TextChannel, 시: int, 분: int, 내용: str):
    if not await admin_only(interaction):
        return
    if not 0 <= 시 <= 23 or not 0 <= 분 <= 59:
        await interaction.response.send_message("시간은 시 0~23, 분 0~59입니다.", ephemeral=True)
        return
    db.execute(
        "INSERT INTO schedules(guild_id, channel_id, hour, minute, message) VALUES(?,?,?,?,?)",
        (interaction.guild.id, 채널.id, 시, 분, 내용)
    )
    db.commit()
    await interaction.response.send_message(f"⏰ 매일 {시:02d}:{분:02d}에 {채널.mention}으로 메시지를 보냅니다.\n> {내용}")

@bot.tree.command(name="반복채팅목록", description="등록된 자동 메시지 목록을 확인합니다.")
async def schedule_list(interaction: discord.Interaction):
    rows = db.execute(
        "SELECT id, channel_id, hour, minute, message FROM schedules WHERE guild_id=? ORDER BY hour, minute",
        (interaction.guild.id,)
    ).fetchall()
    if not rows:
        await interaction.response.send_message("등록된 자동 메시지가 없습니다.")
        return
    lines = []
    for id_, channel_id, hour, minute, message in rows:
        channel = interaction.guild.get_channel(channel_id)
        channel_text = channel.mention if channel else f"(알 수 없는 채널: {channel_id})"
        lines.append(f"`#{id_}` {hour:02d}:{minute:02d} → {channel_text}\n> {message}")
    await interaction.response.send_message("⏰ **등록된 자동 메시지**\n" + "\n".join(lines))

@bot.tree.command(name="반복채팅삭제", description="등록된 자동 메시지를 삭제합니다. (/반복채팅목록에서 번호 확인)")
@app_commands.describe(번호="삭제할 항목 번호 (/반복채팅목록에서 #뒤의 숫자)")
async def schedule_delete(interaction: discord.Interaction, 번호: int):
    if not await admin_only(interaction):
        return
    row = db.execute(
        "SELECT id FROM schedules WHERE guild_id=? AND id=?", (interaction.guild.id, 번호)
    ).fetchone()
    if not row:
        await interaction.response.send_message("해당 번호의 항목을 찾을 수 없습니다.", ephemeral=True)
        return
    db.execute("DELETE FROM schedules WHERE id=?", (번호,))
    db.commit()
    await interaction.response.send_message(f"🗑️ `#{번호}` 항목을 삭제했습니다.")

@tasks.loop(minutes=1)
async def timed_message_loop():
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    rows = db.execute(
        "SELECT id, guild_id, channel_id, hour, minute, message, last_sent_date FROM schedules"
    ).fetchall()
    for id_, guild_id, channel_id, hour, minute, message, last_sent_date in rows:
        if now.hour != hour or now.minute != minute:
            continue
        if last_sent_date == today:
            continue  # 같은 날 중복 전송 방지
        guild = bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id) if guild else None
        if channel and message:
            try:
                await channel.send(message)
                db.execute("UPDATE schedules SET last_sent_date=? WHERE id=?", (today, id_))
                db.commit()
            except discord.HTTPException:
                pass

# ---------------- 음악 ----------------
# 음악 기능은 yt-dlp + FFmpeg를 사용합니다.
# Railway에서는 FFmpeg가 제공되는 환경인지 확인하고, 필요하면 Nixpacks 설정을 추가하세요.

music_queues = {}
music_starters = {}  # guild_id -> 재생을 시작한 사람의 user_id

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
        }
    },
    "geo_bypass": True,
}

FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
)

def get_queue(guild_id):
    return music_queues.setdefault(guild_id, [])

async def ensure_voice(interaction):
    """interaction.response.defer()가 이미 호출된 뒤에 불러야 함 (followup 사용)"""
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send("먼저 음성 채널에 들어가세요.", ephemeral=True)
        return None
    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client
    if vc and vc.channel != channel:
        if vc.is_playing() or vc.is_paused():
            await interaction.followup.send(
                f"🔊 이미 **{vc.channel.mention}**에서 음악을 재생 중이에요. "
                f"거기로 이동하거나, 그 방 음악이 끝난 뒤 다시 시도해주세요.",
                ephemeral=True
            )
            return None
        await vc.move_to(channel)
    elif not vc:
        vc = await channel.connect()
    return vc

def search_track(query: str) -> dict:
    """검색어면 유튜브 상위 1위, URL이면 해당 URL 정보를 가져온다."""
    import yt_dlp
    is_url = query.startswith(("http://", "https://"))
    target = query if is_url else f"ytsearch1:{query}"
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(target, download=False)
    if "entries" in info:
        entries = [e for e in info["entries"] if e]
        if not entries:
            return None
        info = entries[0]
    return info

def build_audio_source(info: dict) -> discord.FFmpegOpusAudio:
    """yt-dlp 결과에서 스트림 URL과 헤더를 뽑아 FFmpeg 소스를 만든다."""
    stream_url = info["url"]
    headers = info.get("http_headers") or {}
    header_str = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
    before_options = FFMPEG_BEFORE_OPTIONS
    if header_str:
        before_options += f' -headers "{header_str}"'
    return discord.FFmpegOpusAudio(
        stream_url,
        before_options=before_options,
        options="-vn",
    )

@bot.tree.command(name="음악재생", description="노래 제목/가수명 또는 URL로 음악을 재생합니다.")
@app_commands.describe(검색어="노래 제목, 가수명 또는 URL")
async def play(interaction: discord.Interaction, 검색어: str):
    await interaction.response.defer()
    vc = await ensure_voice(interaction)
    if not vc:
        return
    try:
        info = await asyncio.to_thread(search_track, 검색어)
        if not info:
            await interaction.followup.send(f"🔍 검색 결과가 없습니다: **{검색어}**")
            return

        title = info.get("title", "알 수 없는 곡")

        if vc.is_playing() or vc.is_paused():
            get_queue(interaction.guild.id).append(info)
            await interaction.followup.send(f"🎵 대기열 추가: **{title}**")
        else:
            source = build_audio_source(info)
            vc.play(source, after=lambda e: bot.loop.create_task(play_next(interaction.guild.id)))
            music_starters[interaction.guild.id] = interaction.user.id
            await interaction.followup.send(f"▶️ 재생: **{title}**")
    except Exception as e:
        await interaction.followup.send(f"음악 재생 실패: `{e}`")

async def play_next(guild_id):
    queue = get_queue(guild_id)
    guild = bot.get_guild(guild_id)
    vc = guild.voice_client if guild else None
    if not vc or not queue:
        return
    info = queue.pop(0)
    try:
        source = build_audio_source(info)
        vc.play(source, after=lambda e: bot.loop.create_task(play_next(guild_id)))
    except Exception:
        await play_next(guild_id)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    guild_id = member.guild.id
    starter_id = music_starters.get(guild_id)
    if starter_id is None or member.id != starter_id:
        return
    # 재생을 시작한 사람이 봇이 있는 채널에서 완전히 나갔을 때(다른 채널로 이동 포함)
    vc = member.guild.voice_client
    if not vc or before.channel != vc.channel:
        return
    if after.channel == vc.channel:
        return  # 같은 채널에 그대로 있음
    get_queue(guild_id).clear()
    music_starters.pop(guild_id, None)
    await vc.disconnect()

@bot.tree.command(name="음악일시정지", description="음악을 일시정지합니다.")
async def pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ 일시정지")
    else:
        await interaction.response.send_message("재생 중인 음악이 없습니다.", ephemeral=True)

@bot.tree.command(name="음악재개", description="일시정지한 음악을 재개합니다.")
async def resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ 재개")
    else:
        await interaction.response.send_message("일시정지된 음악이 없습니다.", ephemeral=True)

@bot.tree.command(name="음악스킵", description="현재 음악을 건너뜁니다.")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()
        await interaction.response.send_message("⏭️ 스킵")
    else:
        await interaction.response.send_message("재생 중인 음악이 없습니다.", ephemeral=True)

@bot.tree.command(name="음악정지", description="음악을 멈추고 음성 채널에서 나갑니다.")
async def stop_music(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        music_queues[interaction.guild.id] = []
        music_starters.pop(interaction.guild.id, None)
        await vc.disconnect()
        await interaction.response.send_message("⏹️ 음악을 정지하고 나갔습니다.")
    else:
        await interaction.response.send_message("음성 채널에 연결되어 있지 않습니다.", ephemeral=True)

@bot.tree.command(name="대기열", description="음악 대기열을 확인합니다.")
async def queue_cmd(interaction: discord.Interaction):
    queue = get_queue(interaction.guild.id)
    if not queue:
        await interaction.response.send_message("🎵 대기열이 비어 있습니다.")
        return
    text = "\n".join(
        f"{i}. {info.get('title', '알 수 없는 곡')}" for i, info in enumerate(queue[:10], 1)
    )
    await interaction.response.send_message("🎵 **대기열**\n" + text)

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN 환경변수가 없습니다.")
    bot.run(TOKEN)
