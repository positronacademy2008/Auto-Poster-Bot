import os
import requests
import time

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")

CAPTION = (
    "Positron Academy Bhilwara 🚀\n"
    "Admission Open for BSTC, B.Ed, D.Pharma!\n"
    "📞 Contact: 8104894648\n\n"
    "#PositronAcademy #Bhilwara #Education"
)

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def post_to_instagram(folder, filename, is_video):
    if not IG_ACCOUNT_ID: 
        print("⚠️ Instagram ID missing, skipping IG...")
        return False
    try:
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        
        if is_video: 
            payload.update({'media_type': 'REELS', 'video_url': media_url})
        else: 
            payload.update({'image_url': media_url})
            
        print(f"📸 Sending to Instagram: {filename}...")
        c_res = requests.post(f"{ig_base}/media", data=payload).json()
        
        if 'id' in c_res:
            creation_id = c_res['id']
            # Instagram needs processing time
            time.sleep(60 if is_video else 20)
            p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
            if 'id' in p_res:
                print(f"✅ Instagram Success: {filename}")
                return True
        
        print(f"⚠️ Instagram Fail: {c_res.get('error', {}).get('message')}")
        return False
    except Exception as e:
        print(f"❌ IG Exception: {e}")
        return False

def post_to_facebook(folder, filename, is_video):
    if not FB_PAGE_ID:
        print("⚠️ FB Page ID missing, skipping FB...")
        return False
    try:
        print(f"🔵 Sending to Facebook: {filename}...")
        if is_video:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
            res = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            file_path = os.path.join(folder, filename)
            with open(file_path, 'rb') as f:
                res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()
        
        if 'id' in res:
            print(f"✅ Facebook Success: {filename}")
            return True
        else:
            print(f"⚠️ Facebook Fail: {res.get('error', {}).get('message')}")
            return False
    except Exception as e:
        print(f"❌ FB Exception: {e}")
        return False

def main():
    posted = get_posted_files()
    v_folder, i_folder = 'video', 'images'
    
    # 1. VIDEO ROTATION (IG then FB)
    v_files = [f for f in sorted(os.listdir(v_folder)) if f not in posted and not f.startswith('.')] if os.path.exists(v_folder) else []
    if v_files:
        fname = v_files[0]
        # Instagram First
        ig = post_to_instagram(v_folder, fname, True)
        # Then Facebook
        fb = post_to_facebook(v_folder, fname, True)
        if ig or fb: mark_as_posted(fname)
        time.sleep(30)

    # 2. IMAGE ROTATION (IG then FB)
    i_files = [f for f in sorted(os.listdir(i_folder)) if f not in posted and not f.startswith('.')] if os.path.exists(i_folder) else []
