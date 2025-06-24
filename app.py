import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from memory import append_user_message, get_user_context
from agents.news_agent import handle_news
from agents.spotify_agent import handle_music, pause_music, resume_music, next_song
from agents.reminder_agent import create_reminder  
from agents.qa_agent import handle_qa_agent

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")



@bot.command(name="news")
async def news_command(ctx, *, query: str):
    user_id = str(ctx.author.id)
    print(f"📨 News command from {ctx.author}: {query}")

    append_user_message(user_id, "user", query)

    try:
        response = handle_news(query)
    except Exception as e:
        print(f"[news_command] Error: {e}")
        response = "⚠️ Could not fetch news right now."

    append_user_message(user_id, "assistant", response)
    await ctx.send(response)

@bot.command(name="play")
async def play_command(ctx, *, query: str):
    user_id = str(ctx.author.id)
    print(f"🎵 Music command from {ctx.author}: {query}")

    append_user_message(user_id, "user", query)

    try:
        response = handle_music(query, user_id)
    except Exception as e:
        print(f"[play_command] Error: {e}")
        response = "⚠️ Could not process music request."

    append_user_message(user_id, "assistant", response)
    await ctx.send(response)

@bot.command(name="remind")
async def remind_command(ctx, *, query: str):
    user_id = str(ctx.author.id)
    print(f"⏰ Remind command from {ctx.author}: {query}")

    append_user_message(user_id, "user", query)

    try:
        response = create_reminder(query)
    except Exception as e:
        print(f"[remind_command] Error: {e}")
        response = "⚠️ Could not set reminder right now."

    append_user_message(user_id, "assistant", response)
    await ctx.send(response)

@bot.command(name="ask")
async def ask_command(ctx, *, query: str):
    user_id = str(ctx.author.id)
    print(f"💬 Ask command from {ctx.author}: {query}")

    append_user_message(user_id, "user", query)

    try:
        response = handle_qa_agent(query, user_id)
    except Exception as e:
        print(f"[ask_command] Error: {e}")
        response = "⚠️ Sorry, I couldn’t answer that right now."

    append_user_message(user_id, "assistant", response)
    await ctx.send(response)

@bot.command(name="next")
async def next_command(ctx):
    user_id = str(ctx.author.id)
    print(f"⏭️ Next command from {ctx.author}")
    success = next_song()
    response = "⏭️ Skipped to next song." if success else "⚠️ Could not skip to next song."
    await ctx.send(response)

@bot.command(name="pause")
async def pause_command(ctx):
    user_id = str(ctx.author.id)
    print(f"⏸️ Pause command from {ctx.author}")
    success = pause_music()
    response = "⏸️ Paused playback." if success else "⚠️ Could not pause playback."
    await ctx.send(response)

@bot.command(name="resume")
async def resume_command(ctx):
    user_id = str(ctx.author.id)
    print(f"▶️ Resume command from {ctx.author}")
    success = resume_music()
    response = "▶️ Resumed playback." if success else "⚠️ Could not resume playback."
    await ctx.send(response)


# Start bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
