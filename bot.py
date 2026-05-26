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
    "Admission Open for BPED, BSTC, B.Ed, D.Pharma, DPED and more!\n"
    "📍 Pansal Choraya, Bhilwara\n"
    "📞 Contact: 8104894648\n\n"
    "#PositronAcademy #Bhilwara #AdmissionOpen #Education"
)

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def post_to_instagram(folder, filename, is_video):
    if not IG_ACCOUNT_ID: return False
    try:
        print(f"📸 Instagram: Uploading {filename}...")
        ig_base = f"https://graph.facebook.com/v20.0/{IG_ACCOUNT_ID}"
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        if is_video: payload.update({'media_type': 'REELS', 'video_url': media_url})
        else: payload.update({'image_url': media_url})
            
        c_res = requests.post(f"{ig_base}/media", data=payload).json()
        if 'id' in c_res:
            creation_id = c_res['id']
            
            # --- IMAGE PUBLISH ---
            if not is_video:
                time.sleep(30)
                p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
                if 'id' in p_res:
                    print(f"✅ Instagram Image Success!")
                    return True
            # --- VIDEO (REEL) PUBLISH WITH BYPASS ---
            else:
                video_published = False
                for i in range(15): 
                    print(f"⏳ IG Video Processing... Attempt {i+1}/15")
                    time.sleep(30)
                    
                    status_res = requests.get(f"https://graph.facebook.com/v20.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}").json()
                    status_code = status_res.get('status_code')
                    
                    if status_code == 'FINISHED':
                        print("✅ IG Video Ready! Publishing now...")
                        p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
                        if 'id' in p_res:
                            print(f"✅ Instagram Reel Success!")
                            return True
                        video_published = True
                        break
                    elif status_code == 'ERROR':
                        print(f"❌ IG Processing Error: {status_res}")
                        return False
                
                # --- FORCE PUBLISH BYPASS ---
                if not video_published:
                    print("⏳ Timeout reached, but Meta has the file. Trying a Force Publish anyway...")
                    p_res = requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
                    if 'id' in p_res:
                        print(f"✅ Instagram Reel Success via Force Publish!")
                        return True
                    else:
                        print(f"⚠️ Force Publish also skipped or failed: {p_res}")
        
        print(f"⚠️ Instagram Fail Response: {c_res.get('error', {}).get('message', c_res)}")
        return False
    except Exception as e:
        print(f"❌ IG Exception: {e}")
        return False

def post_to_facebook(folder, filename, is_video):
    if not FB_PAGE_ID: return False
    try:
        print(f"🔵 Facebook: Uploading {filename}...")
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        if is_video:
            fb_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
            res = requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        else:
            fb_url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
            with open(os.path.join(folder, filename), 'rb') as f:
                res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()
        
        if 'id' in res:
            print(f"✅ Facebook Success!")
            return True
        print(f"⚠️ FB Fail: {res.get('error', {}).get('message', res)}")
        return False
    except Exception as e:
        print(f"❌ FB Exception: {e}")
        return False

def main():
    v_f, i_f = 'video', 'images'
    v_ext, i_ext = ('.mp4', '.mov', '.avi'), ('.png', '.jpg', '.jpeg')
    posted = get_posted_files()

    all_v = [f for f in sorted(os.listdir(v_f)) if f.lower().endswith(v_ext)] if os.path.exists(v_f) else []
    all_i = [f for f in sorted(os.listdir(i_f)) if f.lower().endswith(i_ext)] if os.path.exists(i_f) else []
    
    pending_v = [f for f in all_v if f not in posted]
    pending_i = [f for f in all_i if f not in posted]

    # --- INDEPENDENT RESTART LOGIC ---
    if all_v and not pending_v:
        print("🎬 Resetting Video Loop...")
        posted = {f for f in posted if f not in all_v}
        pending_v = all_v
    
    if all_i and not pending_i:
        print("📸 Resetting Image Loop...")
        posted = {f for f in posted if f not in all_i}
        pending_i = all_i

    with open("posted.txt", "w") as f:
        for item in posted: f.write(item + "\n")

    # --- NEW ORDERED EXECUTION ---
    
    # 1. FACEBOOK IMAGE
    fb_i_success = False
    if pending_i:
        i_name = pending_i[0]
        fb_i_success = post_to_facebook(i_f, i_name, False)
        
        # 2. INSTAGRAM IMAGE (Facebook Image ke baad)
        print("⏳ Waiting 15 seconds before hitting Instagram Image...")
        time.sleep(15)
        ig_i_success = post_to_instagram(i_f, i_name, False)
        
        if fb_i_success or ig_i_success:
            mark_as_posted(i_name)
            
        print("⏳ Waiting 30 seconds buffer before launching Video logic...")
        time.sleep(30)

    # 3. FACEBOOK VIDEO
    fb_v_success = False
    if pending_v:
        v_name = pending_v[0]
        fb_v_success = post_to_facebook(v_f, v_name, True)
        
        # 4. INSTAGRAM VIDEO (Sabse aakhiri mein, taaki loop yahan chale)
        print("⏳ Waiting 30 seconds before launching Instagram Video loop...")
        time.sleep(30)
        ig_v_success = post_to_instagram(v_f, v_name, True)
        
        if fb_v_success or ig_v_success:
            mark_as_posted(v_name)

if __name__ == "__main__":
    main()
