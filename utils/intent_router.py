import os
import requests

# URL for hosted BART zero-shot classifier
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Must be set in your .env or environment
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}
INTENTS = ["music", "news", "qa"]

def detect_intent(message: str, context=None) -> str:
    payload = {
        "inputs": message,
        "parameters": {"candidate_labels": INTENTS}
    }

    try:
        response = requests.post(HF_API_URL, headers=HEADERS, json=payload)
        response.raise_for_status()

        result = response.json()
        return result["labels"][0]  # top intent
    except Exception as e:
        print(f"Intent detection failed: {e}")
        return "qa"  # fallback
