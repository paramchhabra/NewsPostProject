import os
import base64
import pickle
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload

def upload(data, video_file):
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    def upload_video(file_path, title, description, tags=None, category_id="22", privacy_status="private"):
        # Load credentials from HF Secrets (base64-encoded pickle)
        creds = None
        token_b64 = os.getenv("GOOGLE_OAUTH_TOKEN")
        if token_b64:
            creds = pickle.loads(base64.b64decode(token_b64))

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise Exception("Invalid or missing OAuth credentials. Generate token.pickle locally.")

        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags if tags else [],
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
                print(f"Uploaded {int(status.progress() * 100)}%")

        print("Upload Complete! Video ID:", response.get("id"))
        return response.get("id")

    video_title = data['video_title']
    video_description = data['description']
    video_tags = data['tags']

    upload_video(video_file, video_title, video_description, video_tags, privacy_status="public")
