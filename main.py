import os
import asyncio
import aiohttp
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


FLIC_TOKEN = "flic_d96f9d4110a92cfd83c170211cea387d066e13e48fa43bf9a0499ef23f4db592"


UPLOAD_URL_ENDPOINT = "https://api.socialverseapp.com/posts/generate-upload-url"


HEADERS = {"Flic-Token": FLIC_TOKEN, "Content-Type": "application/json"}

def get_upload_url():
    try:
        response = requests.get(UPLOAD_URL_ENDPOINT, headers=HEADERS)
        response.raise_for_status()
        data = response.json()  
        print(f"Generated upload URL: {data}")
        return data 
    except requests.RequestException as e:
        print(f"Error fetching upload URL: {e}")
        return None

async def upload_video(pre_signed_url, video_path):
    async with aiohttp.ClientSession() as session:
        try:
            with open(video_path, 'rb') as video_file:
                async with session.put(pre_signed_url, data=video_file) as response:
                    if response.status == 200:
                        print(f"Video {video_path} uploaded successfully!")
                        return True
                    else:
                        print(f"Error uploading video: {response.status}")
                        return False
        except Exception as e:
            print(f"Exception during upload: {e}")
            return False

def create_post(title, hash_value, category_id=1):
    payload = {
        "title": title,
        "hash": hash_value,
        "is_available_in_public_feed": False,
        "category_id": category_id,
    }
    try:
        response = requests.post("https://api.socialverseapp.com/posts", json=payload, headers=HEADERS)
        response.raise_for_status()
        print(f"Post created successfully: {response.json()}")
        return True
    except requests.RequestException as e:
        print(f"Error creating post: {e}")
        return False

class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith(".mp4"):
            print(f"New video detected: {event.src_path}")
            asyncio.create_task(process_video(event.src_path))

async def process_video(video_path):
    print(f"Processing video: {os.path.basename(video_path)}")
    upload_data = get_upload_url()
    if upload_data:
        pre_signed_url = upload_data.get("url")
        hash_value = upload_data.get("hash")
        if await upload_video(pre_signed_url, video_path):
            if create_post(title=os.path.basename(video_path), hash_value=hash_value):
                os.remove(video_path)
                print(f"Deleted local file: {video_path}")
            else:
                print("Failed to create post.")
        else:
            print("Failed to upload video.")
    else:
        print("Failed to get upload URL.")

async def main():
    
    if not os.path.exists("./videos"):
        os.makedirs("./videos")
    print("Monitoring directory: ./videos")

    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, path="./videos", recursive=False)
    observer.start()

    print("Bot is running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)  
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Stopping bot...")
        observer.stop()
        observer.join()


if __name__ == "__main__":
    asyncio.run(main())  
