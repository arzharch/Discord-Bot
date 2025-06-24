import os
import requests
import logging
import json
import time
from dotenv import load_dotenv
from memory import get_user_context

load_dotenv()

# Environment variables
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

# Spotify API
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_QUEUE_API = "https://api.spotify.com/v1/me/player/queue"
SPOTIFY_SEARCH_API = "https://api.spotify.com/v1/search"

# Global token cache
_spotify_token = None
_spotify_token_expiry = 0

def get_spotify_access_token() -> str:
    global _spotify_token, _spotify_token_expiry
    
    # If token is still valid, return it
    if _spotify_token and time.time() < _spotify_token_expiry:
        return _spotify_token

    try:
        auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        data = {
            "grant_type": "refresh_token",
            "refresh_token": SPOTIFY_REFRESH_TOKEN
        }
        response = requests.post(SPOTIFY_TOKEN_URL, data=data, auth=auth, timeout=10)
        response.raise_for_status()
        resp_json = response.json()
        _spotify_token = resp_json.get("access_token")
        # Set expiry to now + expires_in (default 3600 seconds)
        _spotify_token_expiry = time.time() + resp_json.get("expires_in", 3600) - 60  # 1 min buffer
        return _spotify_token
    except Exception as e:
        logging.error(f"[spotify] Failed to refresh token: {e}")
        return None

def classify_music_request(prompt: str) -> dict:
    payload = {
        "model": "mistral",
        "prompt": (
            "You are a music assistant.\n"
            "Given a user message, extract the music intent in JSON format like:\n"
            "{ \"type\": \"artist|album|playlist|track\", \"value\": \"search query\" }\n"
            "If unsure, use 'track' as type. Only use the user's message as value.\n"
            f"User: {prompt}\n"
            "Intent:"
        ),
        "stream": False
    }
    try:
        res = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=10)
        res.raise_for_status()
        parsed = res.json().get("response", "").strip()
        if "{" in parsed:
            import re
            match = re.search(r"\{.*\}", parsed, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        # fallback: treat whole prompt as track search
        return {"type": "track", "value": prompt}
    except Exception as e:
        logging.warning(f"[llm] Failed to classify: {e}")
        return {"type": "track", "value": prompt}

def find_spotify_uri(search_query: str, search_type: str = "track", market: str = "IN") -> tuple:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    params = {
        "q": search_query,
        "type": search_type,
        "market": market,
        "limit": 5 if search_type == "artist" else 1  # get more artists to check
    }
    try:
        res = requests.get(SPOTIFY_SEARCH_API, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        if search_type == "track":
            items = res.json().get("tracks", {}).get("items", [])
            if items:
                return items[0]["external_urls"]["spotify"], items[0]["uri"]
        elif search_type == "album":
            items = res.json().get("albums", {}).get("items", [])
            if items:
                return items[0]["external_urls"]["spotify"], items[0]["uri"]
        elif search_type == "artist":
            items = res.json().get("artists", {}).get("items", [])
            # Try to find the best match
            for item in items:
                if search_query.lower() in item["name"].lower():
                    return item["external_urls"]["spotify"], item["uri"]
            # fallback to first if no match
            if items:
                return items[0]["external_urls"]["spotify"], items[0]["uri"]
        return None, None
    except Exception as e:
        logging.warning(f"[spotify] Search error: {e}")
        return None, None

def get_album_tracks(album_id: str) -> list:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    tracks_url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    
    try:
        res = requests.get(tracks_url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json().get("items", [])
    except Exception as e:
        logging.error(f"[spotify] Failed to get album tracks: {e}")
        return []

def get_artist_top_tracks(artist_id: str, market: str = "IN") -> list:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market={market}"
    
    try:
        res = requests.get(tracks_url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json().get("tracks", [])
    except Exception as e:
        logging.error(f"[spotify] Failed to get artist top tracks: {e}")
        return []

def queue_spotify_track(uri: str) -> bool:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    params = {"uri": uri}
    try:
        res = requests.post(SPOTIFY_QUEUE_API, headers=headers, params=params, timeout=5)
        # Only fail on 401, 403, 404, 429
        if res.status_code in (401, 403, 404, 429):
            logging.warning(f"[spotify] Queue error: {res.status_code} - {res.text}")
            return False
        # For all other codes (including 2xx), treat as success
        return True
    except Exception as e:
        logging.warning(f"[spotify] Queue error: {e}")
        return False

def pause_music() -> bool:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    try:
        res = requests.put("https://api.spotify.com/v1/me/player/pause", headers=headers, timeout=5)
        if res.status_code in (401, 403, 404, 429):
            logging.error(f"[spotify] Pause error: {res.status_code} - {res.text}")
            return False
        return True
    except Exception as e:
        logging.error(f"[spotify] Pause error: {e}")
        return False

def resume_music() -> bool:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    try:
        res = requests.put("https://api.spotify.com/v1/me/player/play", headers=headers, timeout=5)
        if res.status_code in (401, 403, 404, 429):
            logging.error(f"[spotify] Resume error: {res.status_code} - {res.text}")
            return False
        return True
    except Exception as e:
        logging.error(f"[spotify] Resume error: {e}")
        return False

def next_song() -> bool:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    try:
        res = requests.post("https://api.spotify.com/v1/me/player/next", headers=headers, timeout=5)
        if res.status_code in (401, 403, 404, 429):
            logging.error(f"[spotify] Next song error: {res.status_code} - {res.text}")
            return False
        return True
    except Exception as e:
        logging.error(f"[spotify] Next song error: {e}")
        return False

def get_current_track_uri() -> str:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    try:
        res = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("item", {}).get("uri")
        return None
    except Exception as e:
        logging.error(f"[spotify] Get current track error: {e}")
        return None

def handle_music(user_input: str, user_id: str = None) -> str:
    print(f"[handle_music] User input: {user_input}")
    intent = classify_music_request(user_input)
    print(f"[handle_music] Classified intent: {intent}")

    if not get_spotify_access_token():
        print("[handle_music] Spotify authentication failed.")
        return "⚠️ Spotify authentication failed."

    search_type = intent["type"]
    search_query = intent["value"]

    # Album
    if search_type == "album":
        print(f"[handle_music] Handling album request for: {search_query}")
        _, album_uri = find_spotify_uri(search_query, "album")
        if not album_uri:
            return f"❌ Could not find album: {search_query}"
        album_id = album_uri.split(":")[-1]
        tracks = get_album_tracks(album_id)
        if not tracks:
            return f"❌ No tracks found in album: {search_query}"
        queued_count = 0
        for track in tracks:
            if queue_spotify_track(track["uri"]):
                queued_count += 1
        if queued_count > 0:
            return f"🎧 Added album: {search_query}"
        else:
            return "❌ Could not queue album. Please make sure Spotify is open and active."

    # Artist
    elif search_type == "artist":
        print(f"[handle_music] Handling artist request for: {search_query}")
        _, artist_uri = find_spotify_uri(search_query, "artist")
        if not artist_uri:
            return f"❌ Could not find artist: {search_query}"
        artist_id = artist_uri.split(":")[-1]
        tracks = get_artist_top_tracks(artist_id)
        if not tracks:
            return f"❌ No tracks found for artist: {search_query}"
        queued_count = 0
        for track in tracks:
            if queue_spotify_track(track["uri"]):
                queued_count += 1
        if queued_count > 0:
            return f"🎧 Added top tracks by: {search_query}"
        else:
            return "❌ Could not queue artist tracks. Please make sure Spotify is open and active."

    # Playlist
    elif search_type == "playlist":
        print(f"[handle_music] Handling playlist request for: {search_query}")
        link, uri = find_spotify_uri(search_query, "playlist")
        if not uri:
            return f"❌ Could not find playlist: {search_query}"
        # Spotify API does not allow queueing an entire playlist directly.
        return f"🔗 Playlist found: [{search_query}]({link}) (Add to your Spotify manually!)"

    # Track (default)
    else:
        print(f"[handle_music] Handling track request for: {search_query}")
        link, uri = find_spotify_uri(search_query, "track")
        if not uri:
            return f"❌ Could not find track: {search_query}"
        if queue_spotify_track(uri):
            return f"🎧 Now playing: {search_query}"
        else:
            return "❌ Could not queue track. Please make sure Spotify is open and active."

    # After a successful queue, store context:
    if user_id and search_type in ["artist", "album", "track"]:
        set_user_context(user_id, {"music_last_type": search_type, "music_last_value": search_query})

    if user_input.strip().lower() == "more" and user_id:
        context = get_user_context(user_id)
        if context and "music_last_type" in context and "music_last_value" in context:
            # Use the last context to play more from the artist/album/etc.
            search_type = context["music_last_type"]
            search_query = context["music_last_value"]
            # ...proceed as if the user typed the last command again...
        else:
            return "⚠️ No previous music context found. Please specify what you want to play."