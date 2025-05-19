from pathlib import Path
from openai import OpenAI
import json
from dotenv import load_dotenv

def make_audio(script):
    def generate_speech(text: str, filename: str = "speech.mp3", voice: str = "coral", tone: str = "Speak in a cheerful and positive tone."):
        """
        Generate speech from text using OpenAI TTS and save it to a file.

        Args:
            text (str): The input text to convert to speech.
            filename (str): The output file name (default is 'speech.mp3').
            voice (str): Voice to use (e.g., 'nova', 'echo', 'fable', 'shimmer', 'onyx', 'alloy', 'coral').
            tone (str): Instruction for tone and style of speech.
        """
        load_dotenv()
        client = OpenAI()
        speech_file_path = Path.cwd() / filename

        with client.audio.speech.with_streaming_response.create(
            model="tts-1-hd",  # or "tts-1" for faster/cheaper
            voice=voice,
            input=text,
            instructions=tone
        ) as response:
            response.stream_to_file(speech_file_path)

        print(f"✅ Speech saved to: {speech_file_path}")

    generate_speech(
        text=script['script'],
        filename="audio.mp3",
        voice="onyx",
        tone=script['mood']
    )
    return "audio.mp3"

