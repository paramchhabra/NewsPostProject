import subprocess
import os
import re
from tqdm import tqdm
import wave
import contextlib

def get_audio_duration(filename):
    """Get duration of an audio file in seconds."""
    try:
        import mutagen
        from mutagen.mp3 import MP3
        audio = MP3(filename)
        return audio.info.length
    except ImportError:
        raise ImportError("Install 'mutagen' via pip: pip install mutagen")

def generate_fullwidth_waveform_video(audio_file, logo_file, output_file="output.mp4"):
    width = 1400
    height = 790
    waveform_height = 300

    # Add '-y' to auto-overwrite output files
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Don't prompt for overwrite
        '-i', audio_file,
        '-loop', '1',
        '-i', logo_file,
        '-filter_complex',
        (
            f"color=c=black:s={width}x{height}[bg];"
            f"[0:a]aformat=channel_layouts=mono,showwaves=s={width}x{waveform_height}:mode=cline:colors=#00FF00FF:draw=full[wave];"
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
        '-progress', 'pipe:1',  # Output progress to stdout
        '-nostats',  # Disable other ffmpeg output
        output_file
    ]

    duration = get_audio_duration(audio_file)

    print("Generating video, please wait...")

    with subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1) as process:
        pbar = tqdm(total=duration, unit="s", desc="Progress", position=0)
        time_pattern = re.compile(r"out_time_ms=(\d+)")

        for line in process.stdout:
            match = time_pattern.search(line)
            if match:
                out_time = int(match.group(1)) / 1_000_000  # Convert microseconds to seconds
                pbar.n = min(out_time, duration)
                pbar.refresh()

        pbar.n = duration
        pbar.refresh()
        pbar.close()

    print("✅ Video generation complete.")
    return output_file

# if __name__ == "__main__":
#     generate_fullwidth_waveform_video("audio.mp3", "LogoS.png", "output.mp4")
