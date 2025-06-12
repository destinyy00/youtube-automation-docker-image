from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from brand import brand_and_append_subscribe
from yt_dlp import YoutubeDL
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, 'videos')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process_video(url: str, return_binary: bool = False):
    try:
        # Ensure directories exist
        os.makedirs(VIDEOS_DIR, exist_ok=True)
        
        # Download video
        logger.info(f"Downloading video from: {url}")
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': os.path.join(VIDEOS_DIR, '%(id)s.%(ext)s'),
            'quiet': False,  # Changed to show download progress
            'no_warnings': False
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting download...")
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            logger.info(f"Download complete: {video_path}")
        
        if not os.path.exists(video_path):
            raise HTTPException(status_code=500, detail="Download failed - file not found")
        
        # Brand video
        logger.info("Applying branding...")
        try:
            final_path = brand_and_append_subscribe(
                video_path,
                logo_filename=os.path.join(ASSETS_DIR, "logo.png"),
                subscribe_image=os.path.join(ASSETS_DIR, "subscribe.png"),
                subscribe_clip=os.path.join(ASSETS_DIR, "subscribe.mp4")
            )
            logger.info(f"Branding complete: {final_path}")
        except Exception as e:
            logger.error(f"Branding failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Branding failed: {str(e)}")
        
        if return_binary:
            if not os.path.exists(final_path):
                raise HTTPException(status_code=500, detail="Branded video not found")
            return FileResponse(
                path=final_path,
                media_type="video/mp4",
                filename=os.path.basename(final_path)
            )
        
        return {
            "success": True,
            "input_video": video_path,
            "output_video": final_path
        }
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server with:")
    logger.info(f"Videos directory: {VIDEOS_DIR}")
    logger.info(f"Assets directory: {ASSETS_DIR}")
    uvicorn.run(app, host="0.0.0.0", port=8000)