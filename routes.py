# routes.py
from agents.news_agent import handle_news_request

if intent == "news":
    reply = handle_news_request(user_input)
