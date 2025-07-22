import subprocess
import re
from tqdm import tqdm
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video_generator")


def create_music_visualizer(audio, logo_image, background_image):
    # File paths
    output_video = "output.mp4"
    # Video settings
    width = 768
    height = 1344
    
    # Text settings
    text_content = "This is an AI Generated Image and is NOT real"  # Change this to your desired text
    font_size = 24
    
    # Check if required files exist
    required_files = [audio, background_image, logo_image]
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: {file} not found in current directory")
            return False
    
    # FFmpeg command with showwaves filter for full-width waveform
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file if it exists
        "-i", audio,  # Input audio
        "-i", background_image,  # Input background image
        "-i", logo_image,  # Input logo image
        "-filter_complex",
        f"""
        [0:a]aformat=channel_layouts=mono,showwaves=s={width}x{height//8}:mode=line:colors=white:draw=full[waves];
        [waves]format=rgba,colorchannelmixer=aa=0.6[waves_transparent];
        [1:v]scale={width}:{height}[bg];
        [bg][waves_transparent]overlay=0:{height*9//10}[bg_with_waves];
        [bg_with_waves]drawtext=text='{text_content}':fontcolor=white:fontsize={font_size}:x=20:y=20[bg_with_text];
        [2:v]scale=60:60[logo_scaled];
        [bg_with_text][logo_scaled]overlay={width-80}:{height-80}[final]
        """,
        "-map", "[final]",  # Use the final video stream
        "-map", "0:a",      # Use the original audio stream
        "-c:v", "libx264",  # Video codec
        "-c:a", "aac",      # Audio codec
        "-pix_fmt", "yuv420p",  # Pixel format for compatibility
        "-r", "80",         # Frame rate for smoother animation
        "-shortest",        # End when shortest input ends
        output_video
    ]
    
    
    try:
        # Run FFmpeg command
        result = subprocess.run(ffmpeg_cmd, 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        print(f"Output file: {output_video}")
        
    except subprocess.CalledProcessError as e:
        return False , None
    
    except FileNotFoundError:
        return False , None
    
    return True , output_video


def get_audio_duration(filename):
    """Get duration of an audio file in seconds."""
    try:
        from mutagen.mp3 import MP3
        audio = MP3(filename)
        return audio.info.length
    except ImportError:
        raise ImportError("Install 'mutagen' via pip: pip install mutagen")
    except Exception as e:
        logger.error(f"❌ Failed to read audio duration: {e}")
        raise


def generate_fullwidth_waveform_video(audio_file, logo_file, output_file="output.mp4", language="English"):
    try:
        width = 768
        height = 1344
        waveform_height = 300
        color = "FF6462" if language == "Hindi" else "00FF00"

        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', audio_file,
            '-loop', '1',
            '-i', logo_file,
            '-filter_complex',
            (
                f"color=c=black:s={width}x{height}[bg];"
                f"[0:a]aformat=channel_layouts=mono,showwaves=s={width}x{waveform_height}:mode=cline:colors=#{color}FF:draw=full[wave];"
                f"[bg][wave]overlay=x=0:y=({height}-{waveform_height})/2[vid1];"
                f"[1:v]scale=70:-1[logo];"
                f"[vid1][logo]overlay=W-w-30:H-h-30[vid]"
            ),
            '-map', '[vid]',
            '-map', '0:a',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-r', '70',
            '-c:a', 'aac',
            '-shortest',
            '-progress', 'pipe:1',
            '-nostats',
            output_file
        ]

        duration = get_audio_duration(audio_file)

        logger.info("🎞️ Generating video, please wait...")
        with subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1) as process:
            pbar = tqdm(total=duration, unit="s", desc="Progress", position=0)
            time_pattern = re.compile(r"out_time_ms=(\d+)")

            for line in process.stdout:
                match = time_pattern.search(line)
                if match:
                    out_time = int(match.group(1)) / 1_000_000  # microseconds to seconds
                    pbar.n = min(out_time, duration)
                    pbar.refresh()

            process.wait()
            pbar.n = duration
            pbar.refresh()
            pbar.close()

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, ffmpeg_cmd)

        logger.info("✅ Video generation complete.")
        return output_file

    except subprocess.CalledProcessError as e:
        logger.error("❌ ffmpeg failed with return code %s", e.returncode)
        logger.error("🔍 Command: %s", ' '.join(ffmpeg_cmd))
        raise
    except Exception as e:
        logger.exception(f"❌ Unexpected error during video generation: {e}")
        raise


def create_video(audio_file, logo_file, language, background):
    resp, file = create_music_visualizer(audio_file,logo_file,background)
    if resp:
        return file
    else:
        return generate_fullwidth_waveform_video(audio_file,logo_file,language=language)