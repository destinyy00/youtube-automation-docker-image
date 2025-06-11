FROM python:3.9-slim

# System dependencies including FFmpeg and build tools
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    python3-pip \
    build-essential \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories
RUN mkdir -p /app/videos /app/fonts

# Environment variables
ENV SPORTSDB_API_KEY=123

# Command to run
CMD ["python", "final.py"]