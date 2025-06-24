# 🎶 Discord Music & Assistant Bot 🤖

---

## 👋 Welcome!

Meet your all-in-one Discord (and WhatsApp-adaptable) assistant!  
This bot is your **music DJ**, **news anchor**, **reminder buddy**, and **AI chat companion**—all powered by Spotify, Google Calendar, Google News, and a local LLM (Ollama/Mistral).  
Perfect for servers that want a smart, interactive, and fun assistant!

---

## 🚀 Features at a Glance

### 🎵 Spotify Music Control
- **Play anything:** `!play <song/artist/album/playlist>`
  - Smart intent detection—just type what you want!
  - Queues tracks, top artist hits, or full albums to your Spotify queue.
- **Playback controls:**
  - `!pause` — Pause Spotify playback.
  - `!resume` — Resume Spotify playback.
  - `!next` — Skip to the next song.
- **Error handling:** Only fails on Spotify API errors 401, 403, 404, or 429. Otherwise, it just works!
- **Current track info:** (function available, can be added as a command)

---

### 📰 News Summaries
- `!news <topic>` — Get the latest news on any topic, summarized and formatted for Discord.
- Uses Google Custom Search API for reliable, up-to-date results.

---

### ⏰ Reminders & Google Calendar Integration
- `!remind <reminder>` — Natural language reminders (e.g., "remind me to call mom at 10am tomorrow").
- LLM extracts event details and adds them to your Google Calendar.
- Handles vague times ("tomorrow", "morning", "evening") with sensible defaults.

---

### 💬 AI Chat & Q&A
- `!ask <question>` — Chat with your own local AI assistant (Ollama/Mistral).
- Maintains short-term memory for context-aware, human-like conversations.

---

### 🧠 Memory System
- Stores conversation history per user in a local SQLite database (`memory.db`).
- Used for context in chat and can be extended for music context ("play more" style commands).

---

### 🛠️ Extensible & Modular
- **Modular architecture:** Each feature (music, news, reminders, Q&A) is a separate agent/module.
- **Easy to extend:** Add new commands or integrations (weather, jokes, translation, etc.) by creating a new agent and registering a command in `app.py`.
- **Environment-based config:** All sensitive credentials and API keys are managed via a `.env` file (excluded from git).
- **Separation of concerns:** Business logic is kept out of the main bot file and placed in dedicated modules for clean, scalable code.
- **Memory system:** The bot uses a local SQLite database to store user interactions and context, which can be leveraged by any agent for context-aware responses or features.

---

## 🛠️ Setup Guide

1. **Clone the repository**
   ```sh
   https://github.com/arzharch/Discord-Bot.git
   cd discord-bot
   ```

2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up your `.env` file** with:  (ALL ARE FREE !!)
   - `DISCORD_BOT_TOKEN`
   - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REFRESH_TOKEN`
   - `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`

4. **Google Calendar:** Place your `credentials.json` in the root directory.

5. **Run a local LLM (Ollama/Mistral) on port 11434.**
   - Example: `ollama run mistral`

6. **Start the bot**
   ```sh
   python app.py
   ```

---

## 🤖 Commands Cheat Sheet

| Command            | What it Does                                              |
|--------------------|----------------------------------------------------------|
| `!play <query>`    | Play or queue music (track, artist, album, playlist)     |
| `!pause`           | Pause Spotify playback                                   |
| `!resume`          | Resume Spotify playback                                  |
| `!next`            | Skip to next song on Spotify                             |
| `!news <topic>`    | Get news summaries for a topic                           |
| `!remind <text>`   | Set a reminder (adds to Google Calendar)                 |
| `!ask <question>`  | Ask a question or chat with the AI assistant             |
| `!help`            | Show this help message                                   |

---


## 📝 Notes & Tips

- **Spotify:** Requires a premium account and Spotify app open for queueing.
- **Google Calendar:** First use will prompt for OAuth in your browser.
- **LLM:** Requires Ollama or compatible local LLM running on your machine.
- **Fun tip:** You can easily add more skills—just drop a new agent in the `agents/` folder and wire up a command!

---

## 🙏 Credits

- Built with [discord.py](https://discordpy.readthedocs.io/), [requests](https://docs.python-requests.org/), [Ollama](https://ollama.com/), [Google APIs](https://developers.google.com/), and [Spotify Web API](https://developer.spotify.com/documentation/web-api/).

---

## 💡 Get Involved!

Have ideas? Want to contribute?  
Open an issue or pull request—let’s make this bot even smarter, together! 🚀
