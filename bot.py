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

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def post_to_instagram(folder, filename, is_video):
    if not IG_ACCOUNT_ID: return False
    try:
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        # --- IG Feed/Reel ---
        print(f"📸 IG Feed/Reel: Uploading {filename}...")
        payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        if is_video: payload.update({'media_type': 'REELS', 'video_url': media_url})
        else: payload.update({'image_url': media_url})
        c_res = requests.post(f"{ig_base}/media", data=payload).json()
        if 'id' in c_res:
            creation_id = c_res['id']
            for i in range(10):
                time.sleep(30)
                status = requests.get(f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}").json().get('status_code')
                if status == 'FINISHED':
                    requests.post(f"{ig_base}/media_publish", data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN})
                    print(f"✅ IG Feed/Reel Success!")
                    break

        # --- IG Story ---
        print(f"🤳 IG Story: Uploading {filename}...")
        story_payload = {'media_type': 'STORY', 'access_token': ACCESS_TOKEN}
        if is_video: story_payload.update({'video_url': media_url})
        else: story_payload.update({'image_url': media_url})
        s_res = requests.post(f"{ig_base}/media", data=story_payload).json()
        if 'id' in s_res:
            time.sleep(30)
            requests.post(f"{ig_base}/media_publish", data={'creation_id': s_res['id'], 'access_token': ACCESS_TOKEN})
            print(f"✅ IG Story Success!")
    except: pass

def post_to_facebook(folder, filename, is_video):
    if not FB_PAGE_ID: return False
    try:
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        
        # --- FB Page Post ---
        print(f"🔵 FB Post: Uploading {filename}...")
        if is_video:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
            requests.post(fb_url, data={'description': CAPTION, 'file_url': media_url, 'access_token': ACCESS_TOKEN})
        else:
            fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
            with open(os.path.join(folder, filename), 'rb') as f:
                requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f})
        print(f"✅ FB Post Success!")

        # --- FB Story (Experimental API Support) ---
        # Note: FB Story API requires specific Page permissions. If it fails, the rest will still work.
        print(f"🎬 FB Story: Attempting {filename}...")
        fb_story_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_stories" if is_video else f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories"
        story_data = {'access_token': ACCESS_TOKEN}
        if is_video: story_data['video_url'] = media_url
        else: story_data['url'] = media_url
        requests.post(fb_story_url, data=story_data)
        print(f"✅ FB Story Processed!")
        
    except: pass

def main():
    v_f, i_f = 'video', 'images'
    v_ext, i_ext = ('.mp4', '.mov', '.avi'), ('.png', '.jpg', '.jpeg')
    posted = get_posted_files()

    all_v = [f for f in sorted(os.listdir(v_f)) if f.lower().endswith(v_ext)] if os.path.exists(v_f) else []
    all_i = [f for f in sorted(os.listdir(i_f)) if f.lower().endswith(i_ext)] if os.path.exists(i_f) else []
    
    pending_v = [f for f in all_v if f not in posted]
    pending_i = [f for f in all_i if f not in posted]

    if all_v and not pending_v:
        posted = {f for f in posted if f not in all_v}
        pending_v = all_v
    if all_i and not pending_i:
        posted = {f for f in posted if f not in all_i}
        pending_i = all_i

    with open("posted.txt", "w") as f:
        for item in posted: f.write(item + "\n")

    if pending_v:
        v_name = pending_v[0]
        post_to_instagram(v_f, v_name, True)
        post_to_facebook(v_f, v_name, True)
        mark_as_posted(v_name)
        time.sleep(60)

    if pending_i:
        i_name = pending_i[0]
        post_to_instagram(i_f, i_name, False)
        post_to_facebook(i_f, i_name, False)
        mark_as_posted(i_name)

if __name__ == "__main__":
    main()
