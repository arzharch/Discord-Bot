# reminder_agent.py

import os
import json
import requests
import datetime
import logging
import re
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

# Google Calendar config
SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CRED_FILE = 'credentials.json'
GOOGLE_TOKEN_FILE = 'token.json'

# Local LLM config (Ollama)
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

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

def authenticate_google_calendar():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CRED_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def extract_json(text: str) -> str:
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        return match.group(0)
    raise ValueError("No JSON object found in LLM response")

def create_reminder(event_text: str) -> str:
    try:
        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        extraction_prompt = (
            "Extract reminder details from this text and return JSON like:\n"
            "{ \"summary\": \"title\", \"start\": \"YYYY-MM-DD HH:MM\" }\n\n"
            f"Today's date is {today_str} and the current time is {time_str}.\n"
            f"Reminder: \"{event_text}\"\nResponse:"
        )
        response = local_llm_response(extraction_prompt)
        parsed = json.loads(extract_json(response))
        summary = parsed["summary"]
        start_str = parsed["start"]
        try:
            start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
        except ValueError:
            # If only date is provided, default to 09:00
            try:
                start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d")
                start_dt = start_dt.replace(hour=9, minute=0)
            except Exception as e:
                logging.error(f"[Reminder] Invalid date/time format: {e}")
                return "⚠️ Could not understand the reminder time. Please specify a time."
        end_dt = start_dt + datetime.timedelta(minutes=30)
        service = authenticate_google_calendar()
        event = {
            'summary': summary,
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Kolkata'}
        }
        service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Reminder '{summary}' set for {start_dt.strftime('%Y-%m-%d %H:%M')}."
    except Exception as e:
        logging.error(f"[Reminder] Failed to set: {e}")
        return "⚠️ Could not create the reminder. Try a simpler description."
