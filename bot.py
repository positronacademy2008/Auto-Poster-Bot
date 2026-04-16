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

def reset_posted_files():
    print("♻️ Sabhi content post ho chuka hai. List reset kar raha hoon taaki shuru se start ho sake...")
    with open("posted.txt", "w") as f:
        f.write("") # File khali kar di

def mark_as_posted(filename):
    with open("posted.txt", "a") as f:
        f.write(filename + "\n")

def post_file(folder, filename):
    file_path = os.path.join(folder, filename)
    is_video = filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
    
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
    
    # Folders define karein (Aapke mutabik 'video' aur 'images')
    folders = ['video', 'images']
    
    # Sabhi pending files dhoondhein
    pending_files = []
    for folder in folders:
        if os.path.exists(folder):
            files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f not in posted and not f.startswith('.')]
            pending_files.extend(files)

    # RE-START LOGIC: Agar koi pending file nahi hai, toh reset karke dobara list banayein
    if not pending_files:
        reset_posted_files()
        posted = set() # Empty set for current run
        for folder in folders:
            if os.path.exists(folder):
                files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if not f.startswith('.')]
                pending_files.extend(files)

    # Posting Process
    if pending_files:
        # Ek run mein ek Video aur ek Image bhejte hain (taaki dono folders rotate hote rahein)
        video_done = False
        image_done = False
        
        for file_path in pending_files:
            folder, filename = os.path.split(file_path)
            
            if folder == 'video' and not video_done:
                post_file(folder, filename)
                video_done = True
                print("⏳ 45 sec wait before image post...")
                time.sleep(45)
            
            elif folder == 'images' and not image_done:
                post_file(folder, filename)
                image_done = True
            
            # Agar dono ho gaye toh bahar nikal jao
            if video_done and image_done:
                break
    else:
        print("⚠️ Folders khali hain! Please images/video folder mein content dalein.")

if __name__ == "__main__":
    main()
