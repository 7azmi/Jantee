import os

import requests
from cryptography.fernet import Fernet

_fastapi_endpoint = os.environ.get('AI_API', 'http://0.0.0.0:5000/count_pushups')
# 'http://dockerapi-production.up.railway.app/count_pushups')

def count_pushups_from_videonote(update, context):
    try:
        key = _load_fernet_key()

        if update.message.video_note:
            video_file = update.message.video_note.get_file()
            file_url = video_file.file_path  # This gets the public URL for the video file
            pushup_count = _count_pushups_in_video(file_url, _fastapi_endpoint, key)
            return pushup_count
        else:
            raise Exception("No video or video note found in the message.")

    except Exception as e:
        raise Exception(f"Error in processing videonote: {e}")


def _load_fernet_key():
    key = os.environ.get('FERNET_KEY', 'OR9Hdu3NKcaT4PPHJni3NAepp61DL_SGeOmB2Eg7PT0=')  # change this later
    if not key:
        raise ValueError("Fernet key not found in environment variables")

    # Convert the key from string to bytes without altering it
    return key.encode()


def _encrypt_message(message, key):
    f = Fernet(key)
    return f.encrypt(message.encode())


def _send_encrypted_video_to_fastapi(data, fastapi_endpoint):
    try:
        response = requests.post(fastapi_endpoint, data=data)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None


def _count_pushups_in_video(video_url, fastapi_endpoint, key):
    try:
        encrypted_url = _encrypt_message(video_url, key)
        data = {'encrypted_video_url': encrypted_url.decode()}

        response = requests.post(fastapi_endpoint, data=data)

        if response is not None:
            if response.status_code == 200:
                pushup_count = response.json().get('pushup_count')
                return pushup_count
            else:
                raise Exception("Error processing video at server.")
        else:
            raise Exception("Error sending video to the server.")
    except Exception as e:
        raise Exception(f"Error in counting pushups: {e}")
