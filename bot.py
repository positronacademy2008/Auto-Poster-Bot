import os
import requests
import time

# --- CONFIG ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")

CAPTION = "Positron Academy Bhilwara 🚀\nAdmission Open: BSTC, B.Ed, D.Pharma\nContact: 8104894648"

def get_posted_files():
    if not os.path.exists("posted.txt"):
        return set()
    with open("posted.txt", "r") as f:
        return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f:
        f.write(filename + "\n")

def post_file(folder, filename):
    file_path = os.path.join(folder, filename)
    is_video = folder == 'videos' or filename.lower().endswith(('.mp4', '.mov', '.avi'))
    
    print(f"🚀 Processing {folder}: {filename}")
    
    try:
        # --- FACEBOOK ---
        if is_video:
            # Video ke liye Page ID aur Raw URL
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            media_url = f"https://raw.githubusercontent.com/{REPO}/main/videos/{filename}"
            res_fb = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            # Photo ke liye /me/ logic
            fb_url = "https://graph.facebook.com/v19.0/me/photos"
            with open(file_path, 'rb') as f:
                res_fb = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()

        # --- INSTAGRAM ---
        if IG_ACCOUNT_ID:
            ig_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
            ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
            if is_video:
                c_res = requests.post(f"{ig_base}/media", data={'media_type': 'REELS', 'video_url': ig_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()
            else:
                c_res = requests.post(f"{ig_base}/media", data={'image_url': ig_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()

            if 'id' in c_res:
                time.sleep(60 if is_video else 20) # Video processing takes more time
                requests.post(f"{ig_base}/media_publish", data={'creation_id': c_res['id'], 'access_token': ACCESS_TOKEN})

        if 'id' in res_fb:
            print(f"✅ Success! Posted: {filename}")
            mark_as_posted(filename)
            return True
        else:
            print(f"❌ FB Fail: {res_fb.get('error', {}).get('message')}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    posted = get_posted_files()
    
    # 1. PEHLE VIDEO CHECK KAREIN (Priority)
    if os.path.exists("videos"):
        video_files = [f for f in sorted(os.listdir("videos")) if f not in posted and not f.startswith('.')]
        if video_files:
            print(f"🎬 Nayi video mili: {video_files[0]}")
            post_file("videos", video_files[0])
            print("⏳ Video post ho gayi, 40 sec wait next image ke liye...")
            time.sleep(40)
    
    # 2. PHIR IMAGE CHECK KAREIN
    if os.path.exists("images"):
        image_files = [f for f in sorted(os.listdir("images")) if f not in posted and not f.startswith('.')]
        if image_files:
            print(f"📸 Nayi image mili: {image_files[0]}")
            post_file("images", image_files[0])

if __name__ == "__main__":
    main()
