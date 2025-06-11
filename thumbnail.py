import subprocess
import os
from datetime import datetime

def get_video_info(input_file):
    """Get video/image dimensions using FFprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        input_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            stream = data.get('streams', [{}])[0]
            return {
                'width': stream.get('width', 0),
                'height': stream.get('height', 0)
            }
    except Exception as e:
        print(f"Error getting dimensions: {e}")
    return None

def create_text_overlay(input_image, output_image, team1, team2, game_date, score1, score2):
    """Create a dynamic thumbnail with slanted text spanning the image width"""
    try:
        # Format the text
        teams_text = f"{team1} vs {team2}"
        date_text = game_date.strftime("%B %d %Y")
        score_text = f"{score1} - {score2}"
        
        # Use relative font path for FFmpeg
        font_path = "fonts\\Tagesschrift-Regular.ttf"
        
        # Build filter complex string without angle parameter
        filter_complex = (
            # Teams text
            "[0]drawtext="
            f"fontfile='{font_path}'"
            f":text='{teams_text}'"
            ":fontcolor=white"
            ":fontsize=120"
            ":x=(w-text_w)/2"
            ":y=h/3"
            ":shadowcolor=black@0.8"
            ":shadowx=6"
            ":shadowy=6"
            ":borderw=6"
            ":bordercolor=black@1"
            ":box=1"
            ":boxcolor=black@0.5[v1];"
            
            # Score text
            "[v1]drawtext="
            f"fontfile='{font_path}'"
            f":text='{score_text}'"
            ":fontcolor=yellow"
            ":fontsize=140"
            ":x=(w-text_w)/2"
            ":y=h/2"
            ":shadowcolor=black@0.8"
            ":shadowx=8"
            ":shadowy=8"
            ":borderw=8"
            ":bordercolor=black@1[v2];"
            
            # Date text
            "[v2]drawtext="
            f"fontfile='{font_path}'"
            f":text='{date_text}'"
            ":fontcolor=white"
            ":fontsize=80"
            ":x=(w-text_w)/2"
            ":y=2*h/3"
            ":shadowcolor=black@0.8"
            ":shadowx=4"
            ":shadowy=4"
            ":borderw=4"
            ":bordercolor=black@1[v3]"
        )

        # FFmpeg command with filter complex
        cmd = [
            'ffmpeg',
            '-i', input_image,
            '-filter_complex', filter_complex,
            '-map', '[v3]',
            '-y',
            output_image
        ]

        print("\nExecuting FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"\nFFmpeg Error:\n{result.stderr}")
            return False
            
        print(f"Successfully created thumbnail: {output_image}")
        return True
        
    except Exception as e:
        print(f"Error processing thumbnail: {str(e)}")
        return False

def main():
    input_image = "thumbnail.png"
    output_image = "thumbnail_edited.png"
    team1 = "INDIANA PACERS"
    team2 = "OKLAHOMA CITY THUNDER"
    game_date = datetime.strptime("2025-06-09", "%Y-%m-%d")
    score1 = "107"
    score2 = "123"
    
    if not os.path.exists(input_image):
        print(f"Error: Input image {input_image} not found!")
        return
    
    print("Creating thumbnail with text overlay...")
    success = create_text_overlay(input_image, output_image, team1, team2, game_date, score1, score2)
    
    if success:
        print("✅ Thumbnail created successfully!")
    else:
        print("❌ Failed to create thumbnail")

if __name__ == "__main__":
    main()