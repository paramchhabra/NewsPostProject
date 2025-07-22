from pathlib import Path
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from google.cloud import texttospeech
from google.api_core.exceptions import GoogleAPIError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_audio(script, language, model):
    load_dotenv()

    def generate_speech(text: str, filename: str = "audio.mp3", voice: str = "coral", tone: str = "Speak in a cheerful and positive tone."):
        speech_file_path = Path.cwd() / filename
        try:
            client = OpenAI()
            with client.audio.speech.with_streaming_response.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                instructions=tone
            ) as response:
                response.stream_to_file(speech_file_path)

            logger.info(f"✅ OpenAI speech saved to: {speech_file_path}")
        except OpenAIError as e:
            logger.error(f"⚠️ OpenAI TTS API error: {e}")
        except Exception as e:
            logger.error(f"⚠️ Unexpected error in generate_speech: {e}")

    def synthesize_speech(text):
        try:
            client = texttospeech.TextToSpeechClient()

            if language == 'Hindi':
                voice = texttospeech.VoiceSelectionParams(
                    language_code="hi-IN",
                    name="hi-IN-Chirp3-HD-Autonoe"
                )
            elif language == 'English':
                voice = texttospeech.VoiceSelectionParams(
                    language_code="en-US",
                    name="en-US-Chirp3-HD-Achird"
                )
            else:
                logger.warning("Unsupported language. Must be 'English' or 'Hindi'.")
                return

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0,
                effects_profile_id=["telephony-class-application"]
            )

            synthesis_input = texttospeech.SynthesisInput(text=text)

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            output_filename = "audio.mp3"
            with open(output_filename, "wb") as out:
                out.write(response.audio_content)
                logger.info(f"✅ Google speech saved to: {output_filename}")
        except GoogleAPIError as e:
            logger.error(f"⚠️ Google TTS API error: {e}")
        except Exception as e:
            logger.error(f"⚠️ Unexpected error in synthesize_speech: {e}")

    try:
        if model == "OpenAI":
            generate_speech(
                text=script['script'],
                voice="onyx" if language == "English" else "coral",
                tone=script.get('mood', 'Neutral tone.')
            )
        else:
            synthesize_speech(text=script['script'])

        return "audio.mp3"
    except Exception as e:
        logger.error(f"⚠️ make_audio encountered an error but continuing: {e}")
        return None
