import os
import requests
import time
from PIL import Image
import io
import base64

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def process_and_get_url(input_path):
    """Image ko 9:16 ratio me pad karke direct link generate karta hai"""
    print(f"🎨 Image Processing (9:16 Padding): {input_path}")
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    
    # Calculate aspect ratio padding
    if (w / h) > target_ratio:
        new_h = int(w / target_ratio)
        new_w = w
    else:
        new_w = int(h * target_ratio)
        new_h = h
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    # High quality JPEG buffer
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='JPEG', quality=95)
    img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    print("☁️ Generating Live URL...")
    res = requests.post(
        f"https://imgbb.com{IMGBB_API_KEY}",
        data={'image': img_b64, 'expiration': 1200} # 20 min link life
    ).json()
    
    if res.get('success'):
        # 'url' is the direct link to image, 'display_url' causes API errors
        url = res['data']['url']
        print(f"✅ URL Ready: {url}")
        return url
    return None

def post_story(filename):
    file_path = os.path.join('images', filename)
    print(f"🚀 Started: {filename}")
    
    media_url = process_and_get_url(file_path)
    if not media_url:
        print("❌ URL Generation Failed. Skipping.")
        return

    # Buffer for Meta servers to index the URL
    time.sleep(15)

    try:
        # --- INSTAGRAM STORY ---
        print("🤳 IG Story: Uploading...")
        ig_res = requests.post(f"https://facebook.com{IG_ACCOUNT_ID}/media", 
            data={'media_type': 'STORY', 'image_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in ig_res:
            creation_id = ig_res['id']
            time.sleep(25) # Extra buffer for IG processing
            pub = requests.post(f"https://facebook.com{IG_ACCOUNT_ID}/media_publish", 
                data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
            if 'id' in pub: print("✅ IG Story LIVE!")
            else: print(f"❌ IG Publish Fail: {pub}")
        else:
            print(f"❌ IG Error: {ig_res.get('error', {}).get('message')}")

        # --- FACEBOOK STORY (New Method) ---
        print("🎬 FB Story: Uploading...")
        # Step 1: Upload as temporary photo
        fb_photo = requests.post(f"https://facebook.com{FB_PAGE_ID}/photos", 
            data={
                'url': media_url, 
                'published': 'false', 
                'temporary': 'true', 
                'access_token': ACCESS_TOKEN
            }).json()
        
        if 'id' in fb_photo:
            # Step 2: Publish photo ID to Story
            fb_story = requests.post(f"https://facebook.com{FB_PAGE_ID}/photo_stories", 
                data={
                    'photo_id': fb_photo['id'], 
                    'access_token': ACCESS_TOKEN
                }).json()
            
            if 'id' in fb_story: print("✅ FB Story LIVE!")
            else: print(f"❌ FB Story conversion fail: {fb_story}")
        else: 
            print(f"❌ FB Initial Upload Fail: {fb_photo.get('error', {}).get('message')}")

    except Exception as e: print(f"❌ Crash Error: {e}")

def main():
    if not all([IMGBB_API_KEY, ACCESS_TOKEN, FB_PAGE_ID, IG_ACCOUNT_ID]):
        print("⚠️ One or more Secrets are missing! Check GitHub Secrets.")
        return

    if os.path.exists('images'):
        posted = get_posted_files()
        all_files = [f for f in sorted(os.listdir('images')) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        pending = [f for f in all_files if f not in posted]
        
        if all_files and not pending:
            print("♻️ List Finished. Resetting...")
            if os.path.exists("posted.txt"): os.remove("posted.txt")
            pending = all_files

        if pending:
            post_story(pending[0])
            mark_as_posted(pending[0])
        else:
            print("📂 No images found in 'images' folder.")

if __name__ == "__main__":
    main()
