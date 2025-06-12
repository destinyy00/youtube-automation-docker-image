import os
import logging
from yt_dlp import YoutubeDL
import ffmpeg
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.videos_dir = 'videos'
        self.assets_dir = 'assets'
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)
        self.update_ytdlp()

    def update_ytdlp(self):
        """Ensure yt-dlp is up to date"""
        try:
            logger.info("Updating yt-dlp...")
            subprocess.run(["yt-dlp", "--update"], check=True)
            logger.info("yt-dlp update completed")
        except subprocess.CalledProcessError as e:
            logger.warning(f"yt-dlp update failed: {e}")
        except Exception as e:
            logger.warning(f"yt-dlp update error: {e}")

    def download_video(self, url: str) -> str:
        """Download video from URL"""
        try:
            # Update yt-dlp before each download
            self.update_ytdlp()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_template = f"{self.videos_dir}/{timestamp}.%(ext)s"
            
            ydl_opts = {
                'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'updatetime': False
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # Find downloaded file
            for file in os.listdir(self.videos_dir):
                if file.startswith(timestamp):
                    return os.path.join(self.videos_dir, file)
                    
            raise Exception("Download completed but file not found")
            
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            raise

    def brand_video(self, video_path: str) -> str:
        """Add branding to video"""
        try:
            output_path = video_path.replace('.mp4', '_branded.mp4')
            
            # Add watermark and subscribe button
            stream = (
                ffmpeg
                .input(video_path)
                .overlay(
                    ffmpeg.input(f"{self.assets_dir}/logo.png"),
                    x=10,
                    y=10
                )
                .overlay(
                    ffmpeg.input(f"{self.assets_dir}/subscribe.png"),
                    x='main_w-overlay_w-10',
                    y='main_h-overlay_h-10'
                )
            )
            
            stream = ffmpeg.output(
                stream,
                output_path,
                acodec='copy',
                vcodec='libx264'
            )
            
            ffmpeg.run(stream, overwrite_output=True)
            return output_path
            
        except Exception as e:
            logger.error(f"Branding error: {str(e)}")
            raise

    def process_video(self, url: str) -> dict:
        """Download and brand video"""
        try:
            # Download video
            logger.info("Downloading video...")
            video_path = self.download_video(url)
            
            # Brand video
            logger.info("Adding branding...")
            branded_path = self.brand_video(video_path)
            
            return {
                'success': True,
                'original_path': video_path,
                'branded_path': branded_path,
                'processed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processed_at': datetime.now().isoformat()
            }