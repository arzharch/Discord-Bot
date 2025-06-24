# qa_agent.py
import os
import json
import requests
import logging
from dotenv import load_dotenv
from memory import get_user_context

load_dotenv()

# Local LLM config (Ollama)
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"  # or llama3, deepseek-coder, etc.

def local_llm_response(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        res = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=15)
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except Exception as e:
        logging.error(f"[LLM Chat] Error: {e}")
        return "⚠️ I'm having trouble processing that. Try again later."

def classify_intent(user_input: str) -> str:
    prompt = (
        "Classify the following user message as one of: reminder, chat.\n"
        f"Message: \"{user_input}\"\n"
        "Respond with only the label."
    )
    response = local_llm_response(prompt)
    return response.strip().lower()

def handle_qa_agent(user_input: str, user_id: str) -> str:
    intent = classify_intent(user_input)
    if "reminder" in intent:
        from agents.reminder_agent import create_reminder
        return create_reminder(user_input)
    context = get_user_context(user_id)
    prompt = (
        f"You are a helpful assistant. Here is the conversation so far:\n"
        f"{context}\n"
        f"User: {user_input}\nAssistant:"
    )
    return local_llm_response(prompt)
