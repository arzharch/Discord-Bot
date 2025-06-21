import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

# Load from .env
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
NEWS_API_EVERYTHING = "https://newsapi.org/v2/everything"
NEWS_API_HEADLINES = "https://newsapi.org/v2/top-headlines"


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
        return result.get("response", "").strip().strip("\"'")  # trim quotes and whitespace
    except Exception as e:
        logging.error(f"[news_agent] Mistral/Ollama error: {e}")
        return "latest news"


def fetch_news_results(query: str) -> list:
    """Search for news articles using NewsAPI with improved accuracy."""
    params = {
        "q": query,  # <-- removed exact match quotes
        "apiKey": NEWS_API_KEY,
        "pageSize": 3,
        "sortBy": "relevancy",  # use relevance instead of date
        "language": "en"
    }

    try:
        res = requests.get(NEWS_API_EVERYTHING, params=params, timeout=10)  # <-- FIXED HERE
        res.raise_for_status()
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



def fetch_headlines(country: str = "us") -> list:
    """Fallback to top headlines if everything API returns nothing."""
    params = {
        "apiKey": NEWS_API_KEY,
        "country": country,
        "pageSize": 3
    }

    try:
        res = requests.get(NEWS_API_HEADLINES, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return format_articles(data.get("articles", []))
    except Exception as e:
        logging.error(f"[news_agent] Top headlines error: {e}")
        return []


def format_articles(articles: list) -> list:
    """Format raw NewsAPI articles."""
    return [
        {
            "title": a["title"],
            "url": a["url"],
            "source": a["source"]["name"],
            "published": a["publishedAt"][:10]
        }
        for a in articles
    ]


def format_news_reply(articles: list, topic: str) -> str:
    """Build reply message from articles."""
    if not articles:
        return f"❌ Sorry, I couldn't find recent news on **{topic}**."

    reply = f"🗞️ Top news for **{topic}**:\n\n"
    for art in articles:
        reply += f"• [{art['title']}]({art['url']}) — {art['source']} ({art['published']})\n"
    return reply


def handle_news(user_input: str) -> str:
    """Main entrypoint for news intent."""
    topic = extract_search_query(user_input)
    articles = fetch_news_results(topic)
    return format_news_reply(articles, topic)
