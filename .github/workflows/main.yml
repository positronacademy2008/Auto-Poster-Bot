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
    "Admission Open for BSTC, B.Ed, D.Pharma, and more!\n"
    "📍 Pansal Choraya, Bhilwara\n"
    "📞 Contact: 8104894648\n\n"
    "#PositronAcademy #Bhilwara #AdmissionOpen #Education"
)

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def reset_posted_files():
    print("♻️ Sabhi content khatam! Shuru se restart kar raha hoon...")
    with open("posted.txt", "w") as f: f.write("")

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def post_to_facebook(folder, filename, is_video):
    try:
        if is_video:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
            res = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            with open(os.path.join(folder, filename), 'rb') as f:
                res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()
        
        if 'id' in res:
            print(f"✅ Facebook Success: {filename}")
            return True
        else:
            print(f"❌ Facebook Fail: {res.get('error', {}).get('message')}")
            return False
    except Exception as e:
        print(f"❌ FB Exception: {e}")
        return False

def post_to_instagram(folder, filename, is_video):
    if not IG_ACCOUNT_ID: return False
    try:
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        # Step 1: Create Container
        payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        if is_video:
            payload.update({'media_type': 'REELS', 'video_url': media_url})
        else:
            payload.update({'image_url': media_url})
            
        c_res = requests.post(f"{ig_base}/media", data=payload).json()
        
        if 'id' in c_res:
            creation_id = c_res['id']
            print(f"⏳ Instagram processing {filename}...")
            time.sleep(60 if is_video else 20) # Video needs more time
            
            # Step 2: Publish
            p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
            if 'id' in p_res:
                print(f"✅ Instagram Success: {filename}")
                return True
            else:
                print(f"❌ Instagram Publish Fail: {p_res.get('error', {}).get('message')}")
        else:
            print(f"❌ Instagram Container Fail: {c_res.get('error', {}).get('message')}")
        return False
    except Exception as e:
        print(f"❌ IG Exception: {e}")
        return False

def main():
    posted = get_posted_files()
    folders = ['video', 'images']
    
    pending = []
    for fld in folders:
        if os.path.exists(fld):
            files = [os.path.join(fld, f) for f in sorted(os.listdir(fld)) if f not in posted and not f.startswith('.')]
            pending.extend(files)

    if not pending:
        reset_posted_files()
        posted = set()
        for fld in folders:
            if os.path.exists(fld):
                files = [os.path.join(fld, f) for f in sorted(os.listdir(fld)) if not f.startswith('.')]
                pending.extend(files)

    if pending:
        v_done, i_done = False, False
        for p_file in pending:
            fld, fname = os.path.split(p_file)
            is_v = fld == 'video'
            
            if is_v and not v_done:
                # FB aur IG dono par koshish karenge
                fb_ok = post_to_facebook(fld, fname, True)
                ig_ok = post_to_instagram(fld, fname, True)
                if fb_ok or ig_ok: 
                    mark_as_posted(fname)
                    v_done = True
                    time.sleep(30)
            
            elif fld == 'images' and not i_done:
                fb_ok = post_to_facebook(fld, fname, False)
                ig_ok = post_to_instagram(fld, fname, False)
                if fb_ok or ig_ok:
                    mark_as_posted(fname)
                    i_done = True
            
            if v_done and i_done: break
    else:
        print("📭 Folders khali hain!")

if __name__ == "__main__":
    main()
