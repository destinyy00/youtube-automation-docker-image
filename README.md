# YouTube Sports Highlights Automation

Automated system for downloading sports highlights and generating custom thumbnails.

## Features
- Fetch recent sports events from TheSportsDB
- Download highlight videos from YouTube
- Generate custom thumbnails with game info
- Process videos with FFmpeg
- Dockerized deployment

## Prerequisites
- Docker installed
- Font file: `fonts/Tagesschrift-Regular.ttf`
- TheSportsDB API key (free tier: '123')

## Quick Start
```bash
# Build Docker image
docker build -t sports-highlights .

# Run container
docker run -v ${PWD}/videos:/app/videos sports-highlights
```

## Project Structure
```
├── final.py           # Main automation script
├── thumbnail.py       # Thumbnail generation
├── test.py           # Testing utilities
├── api.py            # FastAPI endpoints
├── Dockerfile        # Container configuration
├── requirements.txt  # Python dependencies
├── fonts/           # Font files
├── videos/          # Downloaded videos
└── .env             # Environment variables (create this)
```

## Environment Variables
Create a `.env` file:
```
SPORTSDB_API_KEY=123
```

## Local Development
```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run script
python final.py
```

## Docker Usage
```bash
# Build with logs
docker build -t sports-highlights . --progress=plain

# Run with volume mount
docker run -v ${PWD}/videos:/app/videos sports-highlights
```

## Notes
- No YouTube API key needed (using yt-dlp)
- Videos are stored in ./videos directory
- Thumbnails are generated with FFmpeg
- Default sports: Basketball, Soccer, Hockey