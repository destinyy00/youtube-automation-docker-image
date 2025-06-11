import subprocess
import os

def brand_and_append_subscribe(video_filename,
                                logo_filename="logo.png",
                                subscribe_image="subscribe.png",
                                subscribe_clip="subscribe.mp4"):

    input_path = os.path.join("videos", video_filename)
    output_intermediate = video_filename.replace(".mp4", "_branded.mp4")
    output_intermediate_path = os.path.join("videos", output_intermediate)
    final_output = video_filename.replace(".mp4", "_final.mp4")
    final_output_path = os.path.join("videos", final_output)

    # Validate input files
    for file in [input_path, logo_filename, subscribe_image, subscribe_clip]:
        if not os.path.exists(file) and not os.path.exists(os.path.join("videos", file)):
            print(f"❌ File not found: {file}")
            return

    # Step 1: Apply branding and timed subscribe overlay
    filter_complex = (
        "[0:v][1:v]overlay=10:10[tmp1];"                                # Top-left logo
        "[tmp1][1:v]overlay=W-w-10:10[tmp2];"                           # Top-right logo
        "[tmp2]drawbox=y=ih/2:x=0:h=1:w=iw:color=white@0.8:t=fill[tmp3];"  # Horizontal line
        "[tmp3][2:v]overlay=W-w-10:H-h-10:enable='gte(t,5)'[v]"         # Subscribe image at 5s
    )

    step1_cmd = [
        "ffmpeg",
        "-i", input_path,               # [0] Main video
        "-i", logo_filename,            # [1] Logo image
        "-i", subscribe_image,          # [2] Subscribe image
        "-filter_complex", filter_complex,
        "-map", "[v]",                  # Final video stream
        "-map", "0:a?",                 # Audio stream (optional)
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        output_intermediate_path
    ]

    try:
        subprocess.run(step1_cmd, check=True)
        print(f"✅ Branding applied: {output_intermediate_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg branding failed: {e}")
        return

    # Step 2: Append subscribe clip
    concat_list = "concat_list.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{output_intermediate_path}'\n")
        f.write(f"file '{subscribe_clip}'\n")

    step2_cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        final_output_path
    ]

    try:
        subprocess.run(step2_cmd, check=True)
        print(f"✅ Final video with subscribe clip: {final_output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg concatenation failed: {e}")

    # Optional cleanup
    os.remove(concat_list)

# ✅ Example usage
brand_and_append_subscribe("test.mp4")
