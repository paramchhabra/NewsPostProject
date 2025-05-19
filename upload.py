import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.auth.transport.requests
from googleapiclient.http import MediaFileUpload
import pickle
import json

def upload(data, video_file):
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    def upload_video(file_path, title, description, tags=None, category_id="22", privacy_status="private"):
        creds = None

        # Check if token.pickle exists (saved credentials)
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(google.auth.transport.requests.Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

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
