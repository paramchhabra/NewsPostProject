from pathlib import Path
from openai import OpenAI
import json
from dotenv import load_dotenv
from google.cloud import texttospeech

def make_audio(script, language, model):
    def generate_speech(text: str, filename: str = "audio.mp3", voice: str = "coral", tone: str = "Speak in a cheerful and positive tone."):
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
    
    def synthesize_speech(text):
        client = texttospeech.TextToSpeechClient()

        # Language-specific voice selection
        if language == 'Hindi':
            voice = texttospeech.VoiceSelectionParams(
                language_code="hi-IN",
                name="hi-IN-Chirp3-HD-Autonoe"  # News-style, clear Hindi voice
            )
        elif language == 'English':
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",  # Indian English
                name="en-US-Chirp3-HD-Achird"  # Good for male news narration
            )
        else:
            raise ValueError("Unsupported language. Choose 'en' or 'hi'.")

        # Set audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,  # MP3 format
            speaking_rate=1.0,
            pitch=0,
            effects_profile_id=["telephony-class-application"]
        )

        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Save the output
        output_filename = f"audio.mp3"
        with open(output_filename, "wb") as out:
            out.write(response.audio_content)
            print(f"Audio content saved to {output_filename}")

    if model=="OpenAI":
        generate_speech(
            text=script['script'],
            voice="onyx" if language == "English" else "coral",
            tone=script['mood']
        )
    else:
        synthesize_speech(text=script['script'])
    return "audio.mp3"
