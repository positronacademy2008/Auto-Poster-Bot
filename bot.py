import os
import requests
import time
from PIL import Image

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def process_and_save_story(input_path):
    """Patti lagao aur temporary file save karo Meta URL ke liye"""
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    
    # Patti lagane ka logic
    new_h = int(w / target_ratio)
    if new_h < h:
        new_w = int(h * target_ratio)
        new_h = h
    else:
        new_w = w
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    new_img.save("temp_story.jpg", "JPEG", quality=95)
    print(f"✅ Temporary story file saved: temp_story.jpg")

def post_story(filename):
    file_path = os.path.join('images', filename)
    process_and_save_story(file_path)

    # Ab hum Meta ko ye URL denge (Isliye GitHub commit zaroori hai)
    media_url = f"https://raw.githubusercontent.com/{REPO}/main/temp_story.jpg"
    
    try:
        # --- IG STORY ---
        print(f"🤳 IG Story: Sending URL...")
        ig_res = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media", 
            data={'media_type': 'STORY', 'image_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in ig_res:
            time.sleep(35)
            requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN})
            print("✅ IG Story Live!")
        else:
            print(f"❌ IG Fail: {ig_res.get('error', {}).get('message')}")

        # --- FB STORY ---
        print(f"🎬 FB Story: Sending URL...")
        fb_res = requests.post(f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories", 
            data={'url': media_url, 'access_token': ACCESS_TOKEN}).json()
        if 'id' in fb_res: print("✅ FB Story Live!")
        else: print(f"❌ FB Fail: {fb_res.get('error', {}).get('message')}")

    except Exception as e: print(f"❌ Error: {e}")

def main():
    if os.path.exists('images'):
        posted = get_posted_files()
        all_files = [f for f in sorted(os.listdir('images')) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        pending = [f for f in all_files if f not in posted]
        
        if all_files and not pending:
            os.remove("posted.txt")
            pending = all_files

        if pending:
            print(f"🚀 Processing Story: {pending[0]}")
            post_story(pending[0])
            mark_as_posted(pending[0])

if __name__ == "__main__":
    main()
