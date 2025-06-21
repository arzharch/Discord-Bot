import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from memory import append_user_message, get_user_context
from agents.news_agent import handle_news
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

    # Save message
    append_user_message(user_id, "user", query)

    try:
        response = handle_news(query)
    except Exception as e:
        print(f"[news_command] Error: {e}")
        response = "⚠️ Could not fetch news right now."

    append_user_message(user_id, "assistant", response)
    await ctx.send(response)

# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
