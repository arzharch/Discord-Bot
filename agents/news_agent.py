import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("GOOGLE_CSE_ID")

def extract_search_query(prompt: str) -> str:
    """Return the raw user query for Google search."""
    return prompt.strip()

def search_news_google(query: str, max_results: int = 3) -> list:
    """Use Google Custom Search API to get top news results."""
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX_ID,
        "q": query,
        "num": max_results
    }

    try:
        res = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=10)
        res.raise_for_status()
        items = res.json().get("items", [])
        return [
            {
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "url": item.get("link")
            }
            for item in items
        ]
    except Exception as e:
        logging.error(f"[google_news] Search error: {e}")
        return []

def format_news_reply(articles: list, topic: str) -> str:
    """Format articles into a neat, clickable Discord message."""
    if not articles:
        return f"❌ Sorry, I couldn't find relevant news on **{topic}**."

    reply = f"🗞️ Top news for **{topic}**:\n\n"
    for i, art in enumerate(articles, start=1):
        reply += (
            f"**Article {i}**: [{art['title']}]({art['url']})\n"
            f"🔹 {art['snippet']}\n\n"
        )
    return reply


def handle_news(user_input: str) -> str:
    """Main entrypoint for news intent."""
    topic = extract_search_query(user_input)
    articles = search_news_google(topic)
    return format_news_reply(articles, topic)
