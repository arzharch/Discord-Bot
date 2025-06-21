import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

# Load from .env
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
NEWS_API_ENDPOINT = "https://newsapi.org/v2/everything"


def extract_search_query(prompt: str) -> str:
    """Query local Mistral via Ollama to get a short news search phrase."""
    payload = {
        "model": "mistral",
        "prompt": (
            "You are a smart assistant.\n"
            "Task: Given a request, return only a 3-5 word search phrase related to news. "
            "Don't explain. No label, just the phrase.\n"
            f"Request: {prompt}\n"
            "Search Phrase:"
        ),
        "stream": False
    }

    try:
        res = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=10)
        res.raise_for_status()
        result = res.json()
        return result.get("response", "").strip()

    except Exception as e:
        logging.error(f"[news_agent] Mistral error: {e}")
        return "latest news"


def fetch_news_results(query: str) -> list:
    """Search for news articles using NewsAPI."""
    params = {
        "q": query,
        "apiKey": NEWS_API_KEY,
        "pageSize": 3,
        "sortBy": "publishedAt",
        "language": "en"
    }

    try:
        res = requests.get(NEWS_API_ENDPOINT, params=params, timeout=10)
        data = res.json()
        return [
            {
                "title": a["title"],
                "url": a["url"],
                "source": a["source"]["name"],
                "published": a["publishedAt"][:10]
            }
            for a in data.get("articles", [])
        ]

    except Exception as e:
        logging.error(f"[news_agent] NewsAPI error: {e}")
        return []


def format_news_reply(articles: list, topic: str) -> str:
    """Build reply message from articles."""
    if not articles:
        return f"Sorry, I couldn't find recent news on **{topic}**."

    reply = f"🗞️ Top news for **{topic}**:\n\n"
    for art in articles:
        reply += f"• [{art['title']}]({art['url']}) — {art['source']} ({art['published']})\n"
    return reply


def handle_news_request(user_input: str) -> str:
    """Main entry for news intent."""
    topic = extract_search_query(user_input)
    articles = fetch_news_results(topic)
    return format_news_reply(articles, topic)
