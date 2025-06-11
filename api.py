from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import thumbnail
import os

app = FastAPI()

class ThumbnailRequest(BaseModel):
    team1: str
    team2: str
    score1: str
    score2: str
    game_date: str
    input_image: str = "thumbnail.png"
    output_image: str = "thumbnail_edited.png"

@app.post("/create-thumbnail")
async def create_thumbnail(request: ThumbnailRequest):
    try:
        # Parse date
        game_date = datetime.strptime(request.game_date, "%Y-%m-%d")
        
        # Create thumbnail
        success = thumbnail.create_text_overlay(
            request.input_image,
            request.output_image,
            request.team1,
            request.team2,
            game_date,
            request.score1,
            request.score2
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create thumbnail")
            
        # Return the path to the created thumbnail
        return {"status": "success", "output_file": request.output_image}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))