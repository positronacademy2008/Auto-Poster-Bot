import os
import requests
import time

# --- CONFIG ---
FB_PAGE_ID = "YOUR_FB_PAGE_ID" # Yahan apna FB Page ID daalein
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_USER_ID = os.environ.get("IG_ACCOUNT_ID")
IMAGE_DIR = "./images"
POSTED_FILE = "posted.txt"

def get_posted_files():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE, "r") as f:
        return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open(POSTED_FILE, "a") as f:
        f.write(filename + "\n")

def post_to_meta(file_path, filename):
    caption = f"Positron Academy Bhilwara 🚀\nAdmission Open for BSTC, B.Ed, D.Pharma!\nContact: 8104894648\n#PositronAcademy #Bhilwara #Education"
    
    # 1. Check if Image or Video
    is_video = filename.lower().endswith(('.mp4', '.mov', '.avi'))
    
    # Raw URL for GitHub (GitHub Actions temporary link nahi deta, isliye raw use karenge)
    # Note: Repo public honi chahiye image/video access ke liye
    repo_url = f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY')}/main/images/{filename}"

    print(f"📤 Processing {filename}...")

    # --- FACEBOOK POSTING ---
    if is_video:
        fb_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/videos"
        fb_payload = {'description': caption, 'file_url': repo_url, 'access_token': ACCESS_TOKEN}
    else:
        fb_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
        fb_payload = {'caption': caption, 'url': repo_url, 'access_token': ACCESS_TOKEN}

    res_fb = requests.post(fb_url, data=fb_payload)
    
    # --- INSTAGRAM POSTING (Reels/Photos) ---
    if IG_USER_ID:
        ig_base = f"https://graph.facebook.com/v18.0/{IG_USER_ID}"
        if is_video:
            # IG Reel
            ig_cont = requests.post(f"{ig_base}/media", data={
                'media_type': 'REELS', 'video_url': repo_url, 'caption': caption, 'access_token': ACCESS_TOKEN
            }).json()
        else:
            # IG Photo
            ig_cont = requests.post(f"{ig_base}/media", data={
                'image_url': repo_url, 'caption': caption, 'access_token': ACCESS_TOKEN
            }).json()

        if 'id' in ig_cont:
            creation_id = ig_cont['id']
            # Wait for processing
            time.sleep(30 if is_video else 10)
            requests.post(f"{ig_base}/media_publish", data={
                'creation_id': creation_id, 'access_token': ACCESS_TOKEN
            })

    if res_fb.status_code == 200:
        print(f"✅ Successfully posted: {filename}")
        return True
    else:
        print(f"❌ Error posting {filename}: {res_fb.text}")
        return False

def main():
    posted_files = get_posted_files()
    for filename in os.listdir(IMAGE_DIR):
        if filename not in posted_files and filename != ".gitkeep":
            success = post_to_meta(os.path.join(IMAGE_DIR, filename), filename)
            if success:
                mark_as_posted(filename)
                break # Ek baar mein ek hi post (spam se bachne ke liye)

if __name__ == "__main__":
    main()
