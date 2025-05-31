import os
import base64
import pickle
import json
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv(override=True)

def authenticate(scopes):
    creds = None
    token_b64 = os.getenv("GOOGLE_OAUTH_TOKEN")

    # Load from env if available
    if token_b64:
        try:
            creds = pickle.loads(base64.b64decode(token_b64))
        except Exception as e:
            print("⚠️ Failed to decode GOOGLE_OAUTH_TOKEN:", e)

    # If no valid creds, run login flow
    else:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("🔐 Launching browser for Google OAuth...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "creds.json", scopes)
            creds = flow.run_local_server(port=0)

        # Save and set GOOGLE_OAUTH_TOKEN
        with open("token.pickle", "wb") as token_file:
            pickle.dump(creds, token_file)

        token_b64 = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
        with open(".env","a") as f:
            f.write('\n')
            f.write(f"GOOGLE_OAUTH_TOKEN={token_b64}")
        print("✅ Saved token.pickle and set GOOGLE_OAUTH_TOKEN env variable")

    return creds


def upload(data, video_file, language):
    English_Playlist = os.getenv("ENGLISH")
    Hindi_Playlist = os.getenv("HINDI")
    scopes = ["https://www.googleapis.com/auth/youtube"]

    creds = authenticate(scopes)
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    def upload_video(file_path, title, description, tags=None, category_id="22", privacy_status="private"):
        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": category_id
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
                print(f"📤 Upload progress: {int(status.progress() * 100)}%")

        print("✅ Upload complete! Video ID:", response.get("id"))
        return response.get("id")

    def add_to_playlist(video_id):
        playlist_id = English_Playlist if language.lower() == "english" else Hindi_Playlist
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
        print(f"🎬 Added to {language} Playlist.")
        return response

    video_title = data["video_title"]
    video_description = data["description"]
    video_tags = data["tags"]
    video_id = upload_video(video_file, video_title, video_description, video_tags, privacy_status="public")
    add_to_playlist(video_id)
