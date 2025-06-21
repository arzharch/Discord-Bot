import os
import requests

# Switch to local Mistral/Ollama endpoint for intent detection
MISTRAL_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
INTENTS = ["music", "news", "qa"]

def detect_intent(message: str, context=None) -> str:
    prompt = (
        "You are an intent classifier. "
        f"Given the message: '{message}', classify it as one of: {', '.join(INTENTS)}. "
        "Respond with only the intent label."
    )
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(MISTRAL_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        intent = result.get("response", "").strip().lower()
        if intent in INTENTS:
            return intent
        else:
            return "qa"  # fallback intent
    except Exception as e:
        print(f"Intent detection failed: {e}")
        return "qa"  # fallback intent
