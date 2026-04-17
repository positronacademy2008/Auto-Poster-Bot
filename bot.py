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
    if not IG_ACCOUNT_ID: return False
    try:
        print(f"📸 Instagram: Sending {filename}...")
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        if is_video: payload.update({'media_type': 'REELS', 'video_url': media_url})
        else: payload.update({'image_url': media_url})
            
        c_res = requests.post(f"{ig_base}/media", data=payload).json()
        if 'id' in c_res:
            creation_id = c_res['id']
            time.sleep(60 if is_video else 25)
            p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
            if 'id' in p_res: return True
        return False
    except: return False

def post_to_facebook(folder, filename, is_video):
    try:
        print(f"🔵 Facebook: Sending {filename}...")
        if is_video:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
            res = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            with open(os.path.join(folder, filename), 'rb') as f:
                res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()
        return 'id' in res
    except: return False

def main():
    v_folder, i_folder = 'video', 'images'
    v_ext, i_ext = ('.mp4', '.mov', '.avi'), ('.png', '.jpg', '.jpeg')
    
    posted = get_posted_files()

    # 1. VIDEO LOGIC
    all_v = [f for f in sorted(os.listdir(v_folder)) if f.lower().endswith(v_ext)] if os.path.exists(v_folder) else []
    pending_v = [f for f in all_v if f not in posted]
    
    if all_v and not pending_v: # Agar saari videos post ho chuki hain
        print("🎬 Videos finished. Resetting video history...")
        posted = {f for f in posted if f not in all_v} # Posted list se sirf videos hatao
        pending_v = all_v

    # 2. IMAGE LOGIC
    all_i = [f for f in sorted(os.listdir(i_folder)) if f.lower().endswith(i_ext)] if os.path.exists(i_folder) else []
    pending_i = [f for f in all_i if f not in posted]
    
    if all_i and not pending_i: # Agar saari images post ho chuki hain
        print("📸 Images finished. Resetting image history...")
        posted = {f for f in posted if f not in all_i} # Posted list se sirf images hatao
        pending_i = all_i

    # Update posted.txt with new filtered set
    with open("posted.txt", "w") as f:
        for item in posted: f.write(item + "\n")

    # EXECUTE POSTING
    if pending_v:
        fname = pending_v[0]
        ig = post_to_instagram(v_folder, fname, True)
        fb = post_to_facebook(v_folder, fname, True)
        if ig or fb: mark_as_posted(fname)
        time.sleep(30)

    if pending_i:
        fname = pending_i[0]
        ig = post_to_instagram(i_folder, fname, False)
        fb = post_to_facebook(i_folder, fname, False)
        if ig or fb: mark_as_posted(fname)

if __name__ == "__main__":
    main()
