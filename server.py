import re
import requests


def download_tiktok_hd(video_url, output_filename="tiktok_hd.mp4"):
    # 1. Base API URL for parsing
    api_url = "https://tik-tok.download"

    # 2. Send POST request to extract clean video links
    payload = {"url": video_url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.post(api_url, data=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # 3. Extract the HD (No Watermark) download URL
        # The API usually provides multiple streams; look for the clean video URL
        video_download_url = data.get("video", {}).get("url")

        if not video_download_url:
            print("Could not find HD video URL.")
            return False

        # 4. Download and save the actual video file
        print("Downloading HD video...")
        video_bytes = requests.get(video_download_url, headers=headers)
        video_bytes.raise_for_status()

        with open(output_filename, "wb") as file:
            file.write(video_bytes.content)

        print(f"Success! Saved as {output_filename}")
        return True

    except Exception as e:
        print(f"Error occurred: {e}")
        return False
