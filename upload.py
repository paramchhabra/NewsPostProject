import os
import base64
import pickle
import json
import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uploader")

load_dotenv(override=True)

def authenticate(scopes):
    creds = None
    token_b64 = os.getenv("GOOGLE_OAUTH_TOKEN")

    if token_b64:
        try:
            creds = pickle.loads(base64.b64decode(token_b64))
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        except Exception as e:
            logger.warning("Failed to decode or refresh GOOGLE_OAUTH_TOKEN: %s", e)
            creds = None

    if not creds or not creds.valid or not token_b64:
        logger.info("Launching browser for Google OAuth...")
        flow = InstalledAppFlow.from_client_secrets_file("creds.json", scopes)
        creds = flow.run_local_server(port=0)

        # Save token as env var
        token_b64 = base64.b64encode(pickle.dumps(creds)).decode("utf-8")

        # Avoid duplicate env var
        with open(".env", "a") as f:
            if "GOOGLE_OAUTH_TOKEN=" not in open(".env").read():
                f.write(f"\nGOOGLE_OAUTH_TOKEN={token_b64}\n")

        logger.info("Saved token to .env")

    return creds


def upload(data, video_file, language):
    scopes = ["https://www.googleapis.com/auth/youtube"]
    creds = authenticate(scopes)
    youtube = build("youtube", "v3", credentials=creds)

    English_Playlist = os.getenv("ENGLISH")
    Hindi_Playlist = os.getenv("HINDI")
    playlist_id = English_Playlist if language.lower() == "english" else Hindi_Playlist

    def upload_video(file_path, title, description, tags=None, category_id="22", privacy_status="private"):
        try:
            request_body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }

            media_file = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")

            request = youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media_file
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"📤 Upload progress: {int(status.progress() * 100)}%")

            video_id = response.get("id")
            logger.info("✅ Upload complete! Video ID: %s", video_id)
            return video_id

        except HttpError as e:
            logger.error("YouTube API error during upload: %s", e)
            return None
        except Exception as e:
            logger.error("Upload failed: %s", e)
            return None

    def add_to_playlist(video_id):
        if not video_id:
            logger.warning("Skipping playlist addition — no video ID.")
            return
        try:
            request = youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            response = request.execute()
            logger.info(f"🎬 Added video to {language} playlist.")
            return response
        except HttpError as e:
            logger.error("Failed to add video to playlist: %s", e)
        except Exception as e:
            logger.error("Playlist addition error: %s", e)

    video_id = upload_video(
        video_file,
        data.get("video_title", "Untitled"),
        data.get("description", ""),
        data.get("tags", []),
        privacy_status="private",
        category_id=25
    )
    add_to_playlist(video_id)
