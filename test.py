import requests
from datetime import datetime, timedelta
import yt_dlp
import re
import os

# Placeholder API keys
SPORTSDB_API_KEY = ""
YOUTUBE_API_KEY = ""

# Make sure the videos folder exists
os.makedirs("videos", exist_ok=True)

# Priority leagues list
priority_leagues = [
    "Premier League",
    "NBA",
    "FIFA Club World Cup",
    "UEFA Champions League"
]

def get_recent_matches(date_str, sport=None, league_id=None):
    base_url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/eventsday.php?d={date_str}"
    if sport:
        base_url += f"&s={sport}"
    url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/eventspastleague.php?id={league_id}" if league_id else base_url
    try:
        response = requests.get(url)
        data = response.json()
        return data.get('events') or []
    except Exception as e:
        print(f"Error fetching sports data: {e}")
        return []

def search_youtube_video(query, api_key):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": api_key
    }
    try:
        response = requests.get(search_url, params=params)
        results = response.json()
        items = results.get("items", [])
        if not items:
            return None
        return items[0]["id"]["videoId"]
    except Exception as e:
        print(f"Error calling YouTube API: {e}")
        return None

def sanitize_filename(name):
    return re.sub(r'[^\w\-_\. ]', '_', name).replace(" ", "_")

def download_youtube_video(video_id, output_name):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": f"videos/{output_name}.%(ext)s",
        "download_archive": "downloaded.txt",
        "postprocessors": [{
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4"
        }],
        "quiet": False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"✅ Downloaded: {output_name}.mp4")
    except Exception as e:
        print(f"❌ Failed to download video {video_id}: {e}")

def main():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    categories = [
        {"name": "Football", "sport": "Soccer", "league_id": None},
        {"name": "Premier League", "sport": "Soccer", "league_id": 4328},
        {"name": "NBA", "sport": "Basketball", "league_id": 4387},
        {"name": "Hockey", "sport": "Ice Hockey", "league_id": None},
        {"name": "Rugby", "sport": "Rugby", "league_id": None}
    ]

    all_matches = []

    for cat in categories:
        for date_str in [today_str, yesterday_str]:
            events = get_recent_matches(date_str, sport=cat["sport"], league_id=cat.get("league_id"))
            for e in events:
                title = e.get("strEvent") or f"{e.get('strHomeTeam','')} vs {e.get('strAwayTeam','')}"
                if not title:
                    continue
                league_name = e.get("strLeague") or ""
                all_matches.append({
                    "title": title,
                    "league": league_name
                })

    # Remove duplicates
    seen_titles = set()
    unique_matches = []
    for match in all_matches:
        if match["title"] not in seen_titles:
            unique_matches.append(match)
            seen_titles.add(match["title"])

    # Prioritize matches
    def priority_score(match):
        return 1 if match["league"] in priority_leagues else 0

    sorted_matches = sorted(unique_matches, key=priority_score, reverse=True)

    # Limit to 5 downloads
    max_downloads = 1
    downloaded_count = 0

    for match in sorted_matches:
        if downloaded_count >= max_downloads:
            break
        title = match["title"]
        query = f"{title} highlights"
        print(f"\n🔍 Searching YouTube for: {query}")
        video_id = search_youtube_video(query, YOUTUBE_API_KEY)
        if not video_id:
            print(f"No results found for {title}")
            continue
        safe_name = sanitize_filename(title)
        download_youtube_video(video_id, safe_name)
        downloaded_count += 1

    if downloaded_count == 0:
        print("⚠️ No videos were downloaded.")

if __name__ == "__main__":
    main()
