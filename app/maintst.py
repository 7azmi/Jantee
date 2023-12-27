import requests

def fetch_pushup_count(video_url):
    # Sending data as form data instead of JSON
    response = requests.post(
        'http://dockerapi-production.up.railway.app/count_pushups',
        data={'video_url': video_url}
    )

    if response.status_code == 200:
        data = response.json()
        pushup_count = data.get('pushup_count')
        return pushup_count
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

# Usage example:
if __name__ == "__main__":
    video_url = "https://api.telegram.org/file/bot6088899662:AAGP8lQ9GixY3UVjmMwK4idtZBnCY030lSE/videos/file_3.MP4"  # Replace with the actual video URL
    try:
        pushup_count = fetch_pushup_count(video_url)
        print(f"Pushup count: {pushup_count}")
    except Exception as e:
        print(f"Error: {str(e)}")

