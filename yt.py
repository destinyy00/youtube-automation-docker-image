import requests
from datetime import datetime, timedelta
import yt_dlp

# Placeholder API keys (replace with your actual keys)
SPORTSDB_API_KEY = "123"
YOUTUBE_API_KEY = ""

def get_recent_matches(date_str, sport=None, league_id=None):
    """
    Fetches events from TheSportsDB for the given date (YYYY-MM-DD).
    Optionally filter by sport name or league ID.
    """
    base_url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/eventsday.php?d={date_str}"
    if sport:
        base_url += f"&s={sport}"
    if league_id:
        # If league_id is numeric (EPL or NBA), use eventspastleague instead of eventsday
        url = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_API_KEY}/eventspastleague.php?id={league_id}"
    else:
        url = base_url
    try:
        response = requests.get(url)
        data = response.json()
        # The API returns an 'events' list or None
        return data.get('events') or []
    except Exception as e:
        print(f"Error fetching sports data: {e}")
        return []

def search_youtube_video(query, api_key):
    """
    Uses YouTube Data API v3 to search for the top video matching the query.
    Returns the video ID or None if not found.
    """
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",       # we only want videos
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

def download_youtube_video(video_id, output_name):
    """
    Downloads the YouTube video with yt-dlp in 1080p (if available).
    Merges best audio and video streams with ffmpeg.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestvideo[height<=1080]+bestaudio/best",
        "outtmpl": output_name + ".%(ext)s",  # save as output_name.mp4 (or .mkv)
        "merge_output_format": "mp4"  # ensure mp4 output
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Downloaded highlight as {output_name}.mp4")
    except Exception as e:
        print(f"Failed to download video {video_id}: {e}")

def main():
    # Compute dates: today and yesterday
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    yesterday = now - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    # Define sports/leagues to process
    # For Premier League and NBA, we know league IDs (EPL=4328, NBA=4387):contentReference[oaicite:8]{index=8}.
    categories = [
        {"name": "Football (soccer, general)", "sport": "Soccer", "league_id": None},
        {"name": "Premier League", "sport": "Soccer", "league_id": 4328},
        {"name": "NBA", "sport": "Basketball", "league_id": 4387},
        {"name": "Hockey", "sport": "Ice Hockey", "league_id": None},
        {"name": "Rugby", "sport": "Rugby", "league_id": None}
    ]

    # Collect and process events for each category
    for cat in categories:
        # Try both dates to cover matches in the past 24h
        matches = []
        for date_str in [today_str, yesterday_str]:
            if cat["league_id"]:
                events = get_recent_matches(date_str, league_id=cat["league_id"])
            else:
                events = get_recent_matches(date_str, sport=cat["sport"])
            if events:
                for e in events:
                    # Convert event date/time to datetime for filtering if needed
                    date_event = e.get("dateEvent")
                    time_event = e.get("strTime") or ""
                    title = e.get("strEvent") or f"{e.get('strHomeTeam','')} vs {e.get('strAwayTeam','')}"
                    if not title:
                        continue
                    # We could filter by timestamp here if we had precise times
                    matches.append(title)
        # Remove duplicates
        matches = list(set(matches))
        if not matches:
            print(f"No recent matches found for {cat['name']}.")
            continue

        for match_title in matches:
            # Construct a search query for YouTube
            query = f"{match_title} highlights"
            print(f"Searching YouTube for highlights of: {match_title}")
            video_id = search_youtube_video(query, YOUTUBE_API_KEY)
            if not video_id:
                print(f"No YouTube highlights found for {match_title}.")
                continue
            # Create a safe filename (e.g., replace spaces with underscores)
            filename = match_title.replace(" ", "_")
            # Download the video in 1080p (best available up to 1080p)
            download_youtube_video(video_id, filename)

if __name__ == "__main__":
    main()
 