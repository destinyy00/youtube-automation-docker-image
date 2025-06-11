import os
import subprocess
import requests
from yt_dlp import YoutubeDL
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

# TheSportsDB API configuration
SPORTSDB_API_KEY = '123'
SPORTSDB_BASE_URL = 'https://www.thesportsdb.com/api/v1/json'

# Updated sports leagues mapping for TheSportsDB
SPORTS_LEAGUES = {
    'Soccer': [
        ('4328', 1),  # Premier League
        ('4335', 1),  # La Liga
        ('4331', 1),  # Bundesliga
        ('4332', 1),  # Serie A
        ('4480', 1),  # Champions League
        ('4346', 2),  # MLS
    ],
    'Basketball': [
        ('4387', 1),  # NBA
        ('4436', 2),  # EuroLeague
        ('4572', 3),  # NBL
    ],
    'American Football': [
        ('4391', 1),  # NFL
        ('4479', 2),  # NCAA Football
    ],
    'Ice Hockey': [
        ('4380', 1),  # NHL
        ('4446', 2),  # KHL
    ]
}

# Maximum events to process per run
MAX_EVENTS = 1

# Directory for storing videos
VIDEOS_DIR = Path('videos')
VIDEOS_DIR.mkdir(exist_ok=True)

def is_event_processed(event_id):
    """Check if event has already been processed"""
    try:
        with open('processed_events.txt', 'r') as f:
            processed_events = f.read().splitlines()
        return event_id in processed_events
    except FileNotFoundError:
        return False

def is_game_concluded(event):
    """Check if game is concluded based on date and status"""
    try:
        # Get event date and current time in UTC
        event_date = datetime.fromisoformat(event.get('date').replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        
        # Check game status
        status = event.get('status', {}).get('type', {}).get('name', '').upper()
        completed_statuses = ['FINAL', 'COMPLETED', 'POST']
        
        # Game should be in the past and have a completed status
        return event_date < now and status in completed_statuses
    except Exception:
        return False

def is_game_in_timeframe(event, extended=False):
    """
    Check if game is within timeframe (past 5 days)
    extended=False: checks 0-72 hour window (3 days)
    extended=True: checks 72-120 hour window (3-5 days)
    """
    try:
        # Parse event date, handling multiple possible formats
        event_date_str = event.get('date', '')
        if not event_date_str:
            print("-> Skipped: No date found")
            return False
            
        # Handle different date formats
        try:
            if 'T' in event_date_str:
                # ISO format with timezone
                event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
            else:
                # Try parsing other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        event_date = datetime.strptime(event_date_str, fmt).replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue
        except Exception as e:
            print(f"-> Skipped: Invalid date format: {event_date_str}")
            return False

        now = datetime.now(timezone.utc)
        hours_ago = (now - event_date).total_seconds() / 3600
        
        # Simple past event check
        if event_date >= now:
            print(f"-> Skipped: Future event ({hours_ago:.1f} hours)")
            return False
            
        print(f"Event: {event.get('name')} - Date: {event_date}, Hours ago: {hours_ago:.1f}")
        
        # Time windows (0-72h for primary, 72-120h for extended)
        if not extended:
            in_window = 0 <= hours_ago <= 72
            if not in_window:
                print("-> Skipped: Not in primary window (0-72h)")
            return in_window
        else:
            in_window = 72 < hours_ago <= 120
            if not in_window:
                print("-> Skipped: Not in extended window (72-120h)")
            return in_window
            
    except Exception as e:
        print(f"Error checking timeframe: {e}")
        return False

def get_recent_events():
    """
    Retrieves and sorts sports events from TheSportsDB with better date filtering
    """
    all_events = []
    now = datetime.now(timezone.utc)
    
    # Get events from last 5 days to today
    date_from = (now - timedelta(days=5)).strftime('%Y-%m-%d')
    date_to = now.strftime('%Y-%m-%d')
    
    print(f"\nFetching events from {date_from} to {date_to}")
    
    for sport, leagues in SPORTS_LEAGUES.items():
        print(f"\nChecking {sport}...")
        for league_id, priority in leagues:
            try:
                # Use events by league API
                url = f"{SPORTSDB_BASE_URL}/{SPORTSDB_API_KEY}/eventspastleague.php"
                params = {
                    'id': league_id
                }
                
                response = requests.get(url, params=params)
                data = response.json()
                all_league_events = data.get('events', [])
                
                if not all_league_events:
                    print(f"No events found for {sport}/{league_id}")
                    continue
                
                # Filter events within our date range
                valid_events = []
                for event in all_league_events:
                    try:
                        event_date_str = event.get('dateEvent')
                        if not event_date_str:
                            continue
                            
                        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                        event_date = event_date.replace(tzinfo=timezone.utc)
                        
                        # Calculate hours difference
                        hours_ago = (now - event_date).total_seconds() / 3600
                        
                        # Debug output
                        print(f"Event: {event.get('strEvent')} - Date: {event_date_str} - Hours ago: {hours_ago:.1f}")
                        
                        # Include events from last 5 days that are in the past
                        if 0 <= hours_ago <= 120:  # 5 days = 120 hours
                            event['sport'] = sport
                            event['league_id'] = league_id
                            event['priority'] = priority
                            event['hours_ago'] = hours_ago
                            event['id'] = f"{league_id}-{event['idEvent']}"
                            valid_events.append(event)
                    
                    except Exception as e:
                        print(f"Error processing event date: {e}")
                        continue
                
                print(f"Found {len(valid_events)} valid events out of {len(all_league_events)} total for {sport}/{league_id}")
                all_events.extend(valid_events)
                
            except Exception as e:
                print(f"Error fetching {sport}/{league_id}: {e}")
                continue
    
    if not all_events:
        print("\nNo suitable games found in the last 5 days.")
        return []
    
    # Sort by:
    # 1. Hours ago (most recent first)
    # 2. Priority (higher priority first)
    all_events.sort(key=lambda x: (x.get('hours_ago', 999), x.get('priority', 999)))
    
    # Debug output
    print("\nFiltered and sorted events:")
    for event in all_events[:5]:
        print(f"- {event.get('strEvent')}: {event.get('hours_ago'):.1f}h ago (Priority: {event.get('priority')})")
    
    return all_events[:MAX_EVENTS]

def search_youtube(query, event_date):
    """Enhanced YouTube search with working download options"""
    try:
        search_date = event_date.strftime('%Y-%m-%d')
        parts = query.split(' highlights')[0].split(' vs ')
        if len(parts) >= 2:
            team1, team2 = parts[0].strip(), parts[1].split(' ')[0].strip()
            sport = query.split(' ')[-2]
            
            # Simplified search queries like test.py
            search_queries = [
                f"{team1} vs {team2} highlights {search_date}",
                f"{team1} vs {team2} full game highlights",
                f"{team1} vs {team2} {sport} highlights",
                f"{team1} {team2} highlights"
            ]
        else:
            search_queries = [query]

        print(f"\n🔍 Trying search queries: {search_queries}")

        ydl_opts = {
            'format': 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch5',
            'ignoreerrors': True
        }

        for search_query in search_queries:
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    print(f"Searching: {search_query}")
                    result = ydl.extract_info(f"ytsearch5:{search_query}", download=False)
                    
                    if not result or 'entries' not in result:
                        continue
                        
                    for video in result['entries']:
                        if not video:
                            continue
                            
                        title = video.get('title', '').lower()
                        
                        # Simple validation like test.py
                        if 'highlight' in title or 'recap' in title:
                            video_id = video.get('id')
                            print(f"✅ Found match: {video.get('title')}")
                            return f"https://www.youtube.com/watch?v={video_id}"
                
            except Exception as e:
                print(f"❌ Error with search '{search_query}': {e}")
                continue
                
        return None
            
    except Exception as e:
        print(f"❌ YouTube search error: {e}")
        return None

def download_video(url, event_id):
    """Download video with enhanced error handling and retry logic"""
    try:
        output_template = f"videos/{event_id}.%(ext)s"
        ydl_opts = {
            "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "outtmpl": output_template,
            "quiet": False,
            "no_warnings": False,
            "cookiefile": "cookies.txt",
            "extract_flat": False,
            "nocheckcertificate": True,
            "retries": 10,
            "fragment_retries": 10,
            "ignoreerrors": True,
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4"
            }]
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        return f"videos/{event_id}.mp4"
        
    except Exception as e:
        print(f"❌ Failed to download video: {str(e)}")
        return None

def add_branding(video_path, event_id):
    """
    Adds branding overlays and cleans up intermediate files.
    """
    try:
        base_name = Path(video_path).stem
        branded_temp = VIDEOS_DIR / f"{base_name}_branded.mp4"
        final_output = VIDEOS_DIR / f"{base_name}_final.mp4"

        logo_path = Path('logo.png')
        subscribe_img = Path('subscribe.png')
        subscribe_vid = Path('subscribe.mp4')

        # Verify branding assets exist
        if not logo_path.exists() or not subscribe_img.exists() or not subscribe_vid.exists():
            print("Branding assets missing (logo.png, subscribe.png, subscribe.mp4).")
            return None

        # Fixed filter_complex string - properly connecting drawbox output
        filter_complex = (
            "[0:v]drawbox=x=0:y=40:w=iw:h=1:color=white@0.5:t=fill[base];"  # Add line first
            "[base][1:v]overlay=10:10[tmp1];"  # Logo at top-left
            "[tmp1][2:v]overlay=main_w-overlay_w-10:10[tmp2];"  # Logo at top-right
            "[tmp2][3:v]overlay=main_w-overlay_w-10:main_h-overlay_h-10"  # Subscribe image (last output)
        )

        overlay_cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(logo_path),
            '-i', str(logo_path),
            '-i', str(subscribe_img),
            '-filter_complex', filter_complex,
            '-c:v', 'libx264',
            '-c:a', 'copy',
            '-pix_fmt', 'yuv420p',
            str(branded_temp)
        ]
        try:
            subprocess.run(overlay_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during overlay branding: {e}")
            return None

        # Get video resolution using ffprobe
        probe_cmd = [
            'ffprobe', 
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            str(branded_temp)
        ]
        
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        video_info = json.loads(probe_result.stdout)
        width = video_info['streams'][0]['width']
        height = video_info['streams'][0]['height']

        # Modified concat filter to include audio
        concat_filter = (
            f"[1:v]scale={width}:{height}[scaled];"  # Scale subscribe video
            "[0:v][0:a][scaled][1:a]concat=n=2:v=1:a=1[v][a]"  # Concatenate video and audio
        )

        concat_cmd = [
            'ffmpeg', '-y',
            '-i', str(branded_temp),
            '-i', str(subscribe_vid),
            '-filter_complex', concat_filter,
            '-map', '[v]',  # Map video
            '-map', '[a]',  # Map concatenated audio
            '-c:v', 'libx264',
            '-c:a', 'aac',  # Use AAC codec for audio
            str(final_output)
        ]
        try:
            subprocess.run(concat_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error during concatenation: {e}")
            return None

        # After successful processing, clean up intermediate files
        if final_output.exists():
            # Remove original downloaded video
            Path(video_path).unlink(missing_ok=True)
            # Remove temporary branded video
            branded_temp.unlink(missing_ok=True)
            return str(final_output)
        return None

    except Exception as e:
        print(f"Error in add_branding: {e}")
        # Clean up any partial files on error
        Path(video_path).unlink(missing_ok=True)
        branded_temp.unlink(missing_ok=True)
        final_output.unlink(missing_ok=True)
        return None

def get_accurate_score(competitor):
    """Helper function to get accurate score from competitor data"""
    # Try multiple score locations in ESPN API response
    score = competitor.get('score')
    if not score or score == '0':
        # Try statistics
        stats = competitor.get('statistics', [])
        if isinstance(stats, list):
            for stat in stats:
                if stat.get('name') == 'points':
                    score = stat.get('value')
                    break
        else:
            score = stats.get('points', stats.get('score', '0'))
            
    # Try score from linescores if available
    if not score or score == '0':
        linescores = competitor.get('linescores', [])
        if linescores:
            score = sum(int(ls.get('value', 0)) for ls in linescores)
    
    return str(score)

def mark_as_downloaded(event_id, event_data, final_video_path):
    """
    Stores completed event information and appends event ID
    """
    try:
        json_file = 'processed_videos.json'
        
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        video_info = {
            'event_id': event_id,
            'sport': event_data.get('sport'),
            'league_id': event_data.get('league_id'),
            'date': event_data.get('dateEvent'),
            'home_team': event_data.get('strHomeTeam'),
            'away_team': event_data.get('strAwayTeam'),
            'home_score': event_data.get('intHomeScore'),
            'away_score': event_data.get('intAwayScore'),
            'final_score': f"{event_data.get('intHomeScore')}-{event_data.get('intAwayScore')}",
            'processed_date': datetime.now().isoformat(),
            'output_file': str(final_video_path)
        }
        
        data.append(video_info)
        
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        with open('processed_events.txt', 'a', newline='') as f:
            f.write(f"{event_id}\n")
            
    except Exception as e:
        print(f"Error marking event as downloaded: {e}")

def main():
    events = get_recent_events()
    if not events:
        print("No events found.")
        return

    for event in events:
        event_id = event.get('id', '')
        sport = event.get('sport', '')
        league_id = event.get('league_id', '')
        
        # Get date from TheSportsDB format
        event_date_str = event.get('dateEvent', '')
        if not event_date_str:
            print(f"No date found for event {event_id}. Skipping.")
            continue
            
        try:
            # Parse TheSportsDB date format
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            event_date = event_date.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(f"Error parsing date for event {event_id}: {e}")
            continue
        
        # Build search query using TheSportsDB fields
        home_team = event.get('strHomeTeam', '')
        away_team = event.get('strAwayTeam', '')
        team_names = f"{away_team} vs {home_team}"
        
        # Include sport in search query
        query = f"{team_names} {sport} highlights"
        print(f"Searching for highlights for {sport}/League {league_id} event {event_id}: {query}")
        
        video_url = search_youtube(query, event_date)
        if not video_url:
            print(f"No YouTube video found for event {event_id}. Trying next event.")
            continue

        print(f"Found video URL: {video_url}")
        downloaded = download_video(video_url, event_id)
        if not downloaded:
            print(f"Failed to download video for event {event_id}.")
            continue

        print(f"Downloaded video to {downloaded}. Adding branding...")
        final_video = add_branding(downloaded, event_id)
        if not final_video:
            print(f"Branding failed for event {event_id}.")
            continue

        print(f"Successfully processed video for event {event_id}: {final_video}")
        mark_as_downloaded(event_id, event, final_video)
        # Stop after one successful processing
        break

if __name__ == "__main__":
    main()
