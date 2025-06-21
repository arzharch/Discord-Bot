# app.py

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from memory import append_user_message, get_user_context
from agents.qa_agent import handle_qa
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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_input = message.content.strip()
    user_id = str(message.author.id)

    # Save the user's message
    append_user_message(user_id, "user", user_input)

    # Retrieve recent memory
    context = get_user_context(user_id)

    # Detect intent
    intent = detect_intent(user_input, context)

    # Route to agent
    if intent == "music":
        response = handle_music(user_input, user_id)
    elif intent == "news":
        response = handle_news(user_input)
    else:
        response = handle_qa(user_input, context)

    # Save bot's response
    append_user_message(user_id, "assistant", response)

    await message.channel.send(response)

bot.run(os.getenv("DISCORD_BOT_TOKEN"))