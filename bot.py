import os
import requests
import time
from PIL import Image
import io
import uuid

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") # Actions provides this automatically

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def process_and_save_story(input_path):
    """Square/Horizontal image par black patti lagakar 9:16 banata hai"""
    print(f"🎨 Processing Image for Story: {input_path}")
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    
    new_h = int(w / target_ratio)
    if new_h < h:
        new_w = int(h * target_ratio)
        new_h = h
    else:
        new_w = w
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    # Save with a unique name to totally avoid cache
    unique_name = f"story_{uuid.uuid4().hex[:8]}.jpg"
    new_img.save(unique_name, "JPEG", quality=95)
    print(f"✅ Story file saved locally: {unique_name}")
    return unique_name

def post_story(filename):
    file_path = os.path.join('images', filename)
    unique_filename = process_and_save_story(file_path)

    # Nocache trick with unique filename
    media_url = f"https://raw.githubusercontent.com/{REPO}/main/{unique_filename}"
    
    print(f"⏳ Waiting 30 seconds for GitHub to update the URL: {media_url}")
    # 30 second wait zaroori hai GitHub Raw URL ke update hone ke liye
    time.sleep(30) 

    try:
        # --- INSTAGRAM STORY ---
        print(f"🤳 Instagram Story: Sending URL...")
        ig_res = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media", 
            data={'media_type': 'STORY', 'image_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in ig_res:
            print("⏳ IG processing...")
            time.sleep(20) # Processing time for IG
            pub = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN}).json()
            
            if 'id' in pub:
                print("✅ Instagram Story Live!")
            else:
                print(f"❌ IG Publish Fail: {pub}")
        else:
            print(f"❌ IG Fail: {ig_res}")

        # --- FACEBOOK STORY ---
        print(f"🎬 Facebook Story: Sending URL...")
        fb_res = requests.post(f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories", 
            data={'url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in fb_res: 
            print("✅ Facebook Story Live!")
        else: 
            print(f"❌ FB Fail: {fb_res}")

    except Exception as e: 
        print(f"❌ Error: {e}")

def main():
    if os.path.exists('images'):
        posted = get_posted_files()
        all_files = [f for f in sorted(os.listdir('images')) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        pending = [f for f in all_files if f not in posted]
        
        if all_files and not pending:
            print("♻️ All images posted. Resetting loop...")
            if os.path.exists("posted.txt"): os.remove("posted.txt")
            pending = all_files

        if pending:
            print(f"🚀 Current File: {pending[0]}")
            post_story(pending[0])
            mark_as_posted(pending[0])

if __name__ == "__main__":
    main()
