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

def reset_list():
    print("♻️ Sabhi content khatam! Restarting cycle...")
    if os.path.exists("posted.txt"): os.remove("posted.txt")
    with open("posted.txt", "w") as f: f.write("")

def post_to_instagram(folder, filename, is_video):
    if not IG_ACCOUNT_ID: return False
    try:
        print(f"📸 Instagram: Uploading {filename}...")
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        if is_video: payload.update({'media_type': 'REELS', 'video_url': media_url})
        else: payload.update({'image_url': media_url})
            
        c_res = requests.post(f"{ig_base}/media", data=payload).json()
        if 'id' in c_res:
            creation_id = c_res['id']
            if not is_video: # Images turant publish ho jati hain
                time.sleep(20)
                p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
                return 'id' in p_res
            
            # Videos ke liye Wait Loop
            for i in range(10): # Max 5 minutes wait
                print(f"⏳ IG Video Processing... Attempt {i+1}")
                time.sleep(30)
                status_res = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}").json()
                if status_res.get('status_code') == 'FINISHED':
                    print("✅ IG Video Ready! Publishing...")
                    p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
                    return 'id' in p_res
        return False
    except: return False

def post_to_facebook(folder, filename, is_video):
    if not FB_PAGE_ID: return False
    try:
        print(f"🔵 Facebook: Uploading {filename}...")
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        if is_video:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            res = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            # Photos ke liye direct upload best hai
            with open(os.path.join(folder, filename), 'rb') as f:
                res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()
        
        if 'id' in res:
            print(f"✅ Facebook Success!")
            return True
        print(f"⚠️ FB Fail: {res.get('error', {}).get('message')}")
        return False
    except: return False

def main():
    v_f, i_f = 'video', 'images'
    v_ext, i_ext = ('.mp4', '.mov', '.avi'), ('.png', '.jpg', '.jpeg')
    posted = get_posted_files()

    all_v = [f for f in sorted(os.listdir(v_f)) if f.lower().endswith(v_ext)] if os.path.exists(v_f) else []
    all_i = [f for f in sorted(os.listdir(i_f)) if f.lower().endswith(i_ext)] if os.path.exists(i_f) else []
    
    pending_v = [f for f in all_v if f not in posted]
    pending_i = [f for f in all_i if f not in posted]

    # Smart Restart: Jo khatam ho jaye use reset karo
    if all_v and not pending_v:
        print("🎬 Resetting Video Loop")
        posted = {f for f in posted if f not in all_v}
        pending_v = all_v
    if all_i and not pending_i:
        print("📸 Resetting Image Loop")
        posted = {f for f in posted if f not in all_i}
        pending_i = all_i

    # Update state
    with open("posted.txt", "w") as f:
        for item in posted: f.write(item + "\n")

    # Final Posting Order
    if pending_v:
        fname = pending_v[0]
        ig = post_to_instagram(v_f, fname, True)
        fb = post_to_facebook(v_f, fname, True)
        if ig or fb: mark_as_posted(fname)
        time.sleep(10)

    if pending_i:
        fname = pending_i[0]
        ig = post_to_instagram(i_f, fname, False)
        fb = post_to_facebook(i_f, fname, False)
        if ig or fb: mark_as_posted(fname)

if __name__ == "__main__":
    main()
