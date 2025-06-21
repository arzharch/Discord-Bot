# app.py

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from memory import append_user_message, get_user_context
from agents.news_agent import handle_news
from utils.intent_router import detect_intent

load_dotenv()

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

# Discord bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_input = message.content.strip()
    user_id = str(message.author.id)

    # Save user input
    append_user_message(user_id, "user", user_input)

    # Retrieve recent context
    context = get_user_context(user_id)

    # Detect intent
    intent = detect_intent(user_input, context)

    # Handle based on intent
    try:
        if intent == "news":
            response = handle_news(user_input)
        elif intent == "music":
            response = "🎵 Music assistant is coming soon!"
        elif intent == "qa":
            response = "💬 General Q&A is coming soon!"
        else:
            response = "🤖 I didn't understand that. Try asking for news."
    except Exception as e:
        print(f"[on_message] Error: {e}")
        response = "⚠️ Something went wrong while processing your request."

    # Save and send bot's reply
    append_user_message(user_id, "assistant", response)
    await message.channel.send(response)

# Start the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
