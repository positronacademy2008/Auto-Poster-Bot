import os
import requests
import time

# --- CONFIG ---
# Yahan check karein ki FB_PAGE_ID mil rahi hai ya nahi
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

def reset_posted_files():
    print("♻️ Sabhi content khatam! Shuru se shuru kar raha hoon...")
    with open("posted.txt", "w") as f:
        f.write("")

def mark_as_posted(filename):
    with open("posted.txt", "a") as f:
        f.write(filename + "\n")

def post_file(folder, filename):
    file_path = os.path.join(folder, filename)
    is_video = filename.lower().endswith(('.mp4', '.mov', '.avi'))
    
    # ID Check for Videos
    if is_video and not FB_PAGE_ID:
        print("❌ ERROR: Video ke liye FB_PAGE_ID secret zaroori hai!")
        return False

    print(f"🚀 Processing {folder}: {filename} (Is Video: {is_video})")
    
    try:
        # --- FACEBOOK ---
        if is_video:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
            res_fb = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            fb_url = "https://graph.facebook.com/v19.0/me/photos"
            with open(file_path, 'rb') as f:
                res_fb = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()

        # --- INSTAGRAM ---
        if IG_ACCOUNT_ID:
            ig_media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
            ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
            if is_video:
                c_res = requests.post(f"{ig_base}/media", data={'media_type': 'REELS', 'video_url': ig_media_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()
            else:
                c_res = requests.post(f"{ig_base}/media", data={'image_url': ig_media_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()

            if 'id' in c_res:
                time.sleep(60 if is_video else 20)
                requests.post(f"{ig_base}/media_publish", data={'creation_id': c_res['id'], 'access_token': ACCESS_TOKEN})

        if 'id' in res_fb:
            print(f"✅ Success! Posted: {filename}")
            mark_as_posted(filename)
            return True
        else:
            print(f"❌ FB Fail: {res_fb.get('error', {}).get('message')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    posted = get_posted_files()
    folders = ['video', 'images']
    
    # Check what's left
    pending = []
    for fld in folders:
        if os.path.exists(fld):
            files = [os.path.join(fld, f) for f in sorted(os.listdir(fld)) if f not in posted and not f.startswith('.')]
            pending.extend(files)

    # Infinite Loop Logic
    if not pending:
        reset_posted_files()
        posted = set()
        for fld in folders:
            if os.path.exists(fld):
                files = [os.path.join(fld, f) for f in sorted(os.listdir(fld)) if not f.startswith('.')]
                pending.extend(files)

    if pending:
        # Har run mein 1 Video aur 1 Image rotate hogi
        v_done = False
        i_done = False
        for p_file in pending:
            fld, fname = os.path.split(p_file)
            if fld == 'video' and not v_done:
                post_file(fld, fname)
                v_done = True
                time.sleep(30)
            elif fld == 'images' and not i_done:
                post_file(fld, fname)
                i_done = True
            
            if v_done and i_done: break

if __name__ == "__main__":
    main()
