FROM python:3.9-slim


# Install FFmpeg and dependencies
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    python3-pip \
    build-essential \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install yt-dlp directly from GitHub for latest version
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && \
    chmod a+rx /usr/local/bin/yt-dlp

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories and cookie file with proper format
RUN mkdir -p /app/videos /app/fonts && \
    echo "# Netscape HTTP Cookie File\n# https://curl.haxx.se/rfc/cookie_spec.html\n# This is a generated file!  Do not edit.\n\n" > /app/cookies.txt && \
    chmod 644 /app/cookies.txt

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV SPORTSDB_API_KEY=123

# Debug: List contents
RUN ls -la

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Keep container running
CMD ["tail", "-f", "/dev/null"]