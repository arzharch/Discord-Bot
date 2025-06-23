import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from memory import append_user_message, get_user_context
from agents.news_agent import handle_news
from agents.spotify_agent import handle_music
from utils.intent_router import detect_intent

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

# Start bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
