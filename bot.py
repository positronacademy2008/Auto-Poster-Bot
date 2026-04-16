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

def post_file(folder, filename):
    file_path = os.path.join(folder, filename)
    is_video = folder == 'videos' or filename.lower().endswith(('.mp4', '.mov'))
    
    print(f"🚀 Processing {folder}: {filename}")
    
    # --- FACEBOOK ---
    if is_video:
        # Video ke liye Page ID aur Raw URL zaroori hai
        fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
        video_url = f"https://raw.githubusercontent.com/{REPO}/main/videos/{filename}"
        res_fb = requests.post(fb_url, data={'description': CAPTION, 'file_url': video_url, 'access_token': ACCESS_TOKEN}).json()
    else:
        # Photo ke liye /me/ shortcut (Jo aapka pehle work kar raha tha)
        fb_url = "https://graph.facebook.com/v19.0/me/photos"
        with open(file_path, 'rb') as f:
            res_fb = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': f}).json()

    # --- INSTAGRAM ---
    if IG_ACCOUNT_ID:
        media_url = f"https://raw.githubusercontent.com/{REPO}/main/{folder}/{filename}"
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
        if is_video:
            c_res = requests.post(f"{ig_base}/media", data={'media_type': 'REELS', 'video_url': media_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()
        else:
            c_res = requests.post(f"{ig_base}/media", data={'image_url': media_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}).json()

        if 'id' in c_res:
            time.sleep(45 if is_video else 15)
            requests.post(f"{ig_base}/media_publish", data={'creation_id': c_res['id'], 'access_token': ACCESS_TOKEN})

    if 'id' in res_fb:
        print(f"✅ Success! Posted: {filename}")
        with open("posted.txt", "a") as f:
            f.write(filename + "\n")
    else:
        print(f"❌ FB Fail: {res_fb.get('error', {}).get('message')}")

def main():
    posted = get_posted_files()
    
    # Dono folders ko check karega aur har folder se ek-ek file post karega
    for folder in ['images', 'videos']:
        if os.path.exists(folder):
            # Sirf wahi files jo posted.txt mein nahi hain
            files_to_post = [f for f in sorted(os.listdir(folder)) if f not in posted and not f.startswith('.')]
            
            if files_to_post:
                post_file(folder, files_to_post[0])
                # Video upload mein time lagta hai isliye thoda break
                if folder == 'images':
                    print("⏳ Image post ho gayi, ab 30 second wait video ke liye...")
                    time.sleep(30) 

if __name__ == "__main__":
    main()
