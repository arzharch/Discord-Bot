import os
import requests
import logging
import json
import time
from dotenv import load_dotenv

load_dotenv()

# Environment variables
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
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
            "{ \"type\": \"mood|artist|genre|track|album\", \"value\": \"extracted info\" }\n"
            "For album requests, identify as 'album' type.\n"
            "For artist requests, identify as 'artist' type.\n"
            "For specific songs, identify as 'track' type.\n"
            "For moods/genres, identify as 'mood' type.\n"
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
        return {"type": "track", "value": prompt}
    except Exception as e:
        logging.warning(f"[llm] Failed to classify: {e}")
        return {"type": "track", "value": prompt}

def search_lastfm_tracks(intent: dict, limit=50) -> list:
    base = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": limit
    }
    try:
        if intent["type"] == "artist":
            params.update({"method": "artist.gettoptracks", "artist": intent["value"]})
        elif intent["type"] in ["tag", "mood", "genre"]:
            params.update({"method": "tag.gettoptracks", "tag": intent["value"]})
        elif intent["type"] == "album":
            params.update({"method": "album.search", "album": intent["value"]})
        else:
            params.update({"method": "track.search", "track": intent["value"], "limit": 1})

        res = requests.get(base, params=params, timeout=10)
        data = res.json()
        results = []

        if "trackmatches" in data.get("results", {}):
            results = data["results"]["trackmatches"]["track"]
        elif "toptracks" in data:
            results = data["toptracks"]["track"]
        elif "results" in data and "albummatches" in data["results"]:
            for album in data["results"]["albummatches"]["album"]:
                results.append({"name": album["name"], "artist": album["artist"]})

        return [{"name": t["name"], "artist": t["artist"]} for t in results][:limit]
    except Exception as e:
        logging.error(f"[lastfm] Track search failed: {e}")
        return []

def find_spotify_uri(search_query: str, search_type: str = "track", market: str = "IN") -> tuple:
    headers = {"Authorization": f"Bearer {get_spotify_access_token()}"}
    params = {
        "q": search_query,
        "type": search_type,
        "market": market,
        "limit": 1
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
        
        if res.status_code == 204:
            return True
        elif res.status_code in (401, 403, 429):
            logging.warning(f"[spotify] Queue error: {res.status_code} - {res.text}")
            return False
        elif res.status_code == 404:
            return False
        return True
    except Exception as e:
        logging.warning(f"[spotify] Queue error: {e}")
        return False

def handle_music(user_input: str, user_id: str = None) -> str:
    print(f"[handle_music] User input: {user_input}")
    intent = classify_music_request(user_input)
    print(f"[handle_music] Classified intent: {intent}")
    
    if not get_spotify_access_token():
        print("[handle_music] Spotify authentication failed.")
        return "⚠️ Spotify authentication failed."

    # Handle album requests
    if intent["type"] == "album":
        print(f"[handle_music] Handling album request for: {intent['value']}")
        _, album_uri = find_spotify_uri(intent["value"], "album")
        
        if not album_uri:
            return f"❌ Could not find album: {intent['value']}"
            
        album_id = album_uri.split(":")[-1]
        tracks = get_album_tracks(album_id)
        
        if not tracks:
            return f"❌ No tracks found in album: {intent['value']}"
            
        queued_count = 0
        for track in tracks:
            if queue_spotify_track(track["uri"]):
                queued_count += 1
                
        if queued_count > 0:
            return f"🎧 Added album: {intent['value']}"
        else:
            return "❌ Could not queue album. Please make sure Spotify is open and active."

    # Handle artist requests
    elif intent["type"] == "artist":
        print(f"[handle_music] Handling artist request for: {intent['value']}")
        _, artist_uri = find_spotify_uri(intent["value"], "artist")
        
        if not artist_uri:
            return f"❌ Could not find artist: {intent['value']}"
            
        artist_id = artist_uri.split(":")[-1]
        tracks = get_artist_top_tracks(artist_id)
        
        if not tracks:
            return f"❌ No tracks found for artist: {intent['value']}"
            
        queued_count = 0
        for track in tracks:
            if queue_spotify_track(track["uri"]):
                queued_count += 1
                
        if queued_count > 0:
            return f"🎧 Added top tracks by: {intent['value']}"
        else:
            return "❌ Could not queue artist tracks. Please make sure Spotify is open and active."

    # Handle single track requests
    elif intent["type"] == "track":
        print(f"[handle_music] Handling track request for: {intent['value']}")
        link, uri = find_spotify_uri(intent["value"])
        
        if not uri:
            return f"❌ Could not find track: {intent['value']}"
            
        if queue_spotify_track(uri):
            return f"🎧 Now playing: {intent['value']}"
        else:
            return "❌ Could not queue track. Please make sure Spotify is open and active."

    # Handle mood/genre requests
    else:
        print(f"[handle_music] Handling mood/genre request for: {intent['value']}")
        tracks = search_lastfm_tracks(intent)
        
        if not tracks:
            return "❌ I couldn't find any tracks for your query."
            
        queued_count = 0
        for track in tracks:
            _, uri = find_spotify_uri(f"{track['name']} {track['artist']}")
            if uri and queue_spotify_track(uri):
                queued_count += 1
                
        if queued_count > 0:
            return f"🎧 Added {queued_count} tracks for: {intent['value']}"
        else:
            return "❌ Could not queue tracks. Please make sure Spotify is open and active."