# # sk-Nym7aZxNI1NONfULtM4iwJSux8eNrxThb4RPgkxUqIvvLDJF

import base64
import os
import requests
engine_id = "stable-diffusion-xl-1024-v1-0"
api_host = os.getenv('API_HOST', 'https://api.stability.ai')
api_key = os.getenv("STABILITY_AI_API")

def create_bg_img(prompt):
    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": prompt
                }
            ],
            "cfg_scale": 7,
            "height": 1344,
            "width": 768,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    with open(f"background.png", "wb") as f:
        f.write(base64.b64decode(data["artifacts"][0]["base64"]))
    
    return "background.png"
