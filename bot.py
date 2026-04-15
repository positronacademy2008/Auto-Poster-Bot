import os
import requests
import time

# --- CONFIG ---
# Zaroori: FB_PAGE_ID ko Secrets mein daal dena ya yahan likh dena
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")

CAPTION = "Positron Academy Bhilwara 🚀\nAdmission Open: BSTC, B.Ed, D.Pharma\nContact: 8104894648"

def get_next_file():
    # Folder check logic
    for folder in ['images', 'videos']:
        if os.path.exists(folder):
            files = sorted([f for f in os.listdir(folder) if not f.startswith('.')])
            posted = []
            if os.path.exists("posted.txt"):
                with open("posted.txt", "r") as f:
                    posted = f.read().splitlines()
            
            for f in files:
                if f not in posted:
                    return folder, f
    return None, None

def post_content():
    folder, filename = get_next_file()
    if not filename:
        print("✅ Sab kuch post ho chuka hai!")
        return

    file_path = os.path.join(folder, filename)
    is_video = folder == 'videos' or filename.lower().endswith(('.mp4', '.mov'))
    
    print(f"🚀 Processing {folder}: {filename}")

    # --- 1. FACEBOOK POSTING ---
    if is_video:
        # Videos ke liye Page ID zaroori hai
        fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
        # Video heavy hoti hai isliye URL method best hai
        video_url = f"https://raw.githubusercontent.com/{REPO}/main/videos/{filename}"
        payload = {'description': CAPTION, 'file_url': video_url, 'access_token': ACCESS_TOKEN}
        res_fb = requests.post(fb_url, data=payload).json()
    else:
        # Photos ke liye aapka purana /me/ logic
        fb_url = "https://graph.facebook.com/v19.0/me/photos"
        with open(file_path, 'rb') as f:
            res_fb = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()

    # --- 2. INSTAGRAM POSTING ---
    if IG_ACCOUNT_ID:
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        
        if is_video:
            # IG Reel
            c_res = requests.post(f"{ig_base}/media", data={'media_type': 'REELS', 'video_url': media_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()
        else:
            # IG Photo
            c_res = requests.post(f"{ig_base}/media", data={'image_url': media_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()

        if 'id' in c_res:
            time.sleep(40 if is_video else 15) # Processing time
            requests.post(f"{ig_base}/media_publish", data={'creation_id': c_res['id'], 'access_token': ACCESS_TOKEN})

    if 'id' in res_fb:
        print(f"✅ Success! Posted: {filename}")
        with open("posted.txt", "a") as f:
            f.write(filename + "\n")
    else:
        print(f"❌ FB Fail: {res_fb.get('error', {}).get('message')}")

if __name__ == "__main__":
    post_content()
