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
    """Patti lagao aur direct URL lao (Fastest Method)"""
    print(f"🎨 Image Processing (9:16 Padding): {input_path}")
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    
    new_h = int(w / target_ratio) if (int(w / target_ratio) >= h) else h
    new_w = int(h * target_ratio) if new_h == h else w
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='JPEG', quality=95)
    img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    print("☁️ Generating Live URL...")
    res = requests.post(
        f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}",
        data={'image': img_b64, 'expiration': 600} # 10 min auto-delete
    ).json()
    
    if res.get('success'):
        url = res['data']['display_url']
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

    # Chota wait taaki link internet par active ho jaye
    time.sleep(10)

    try:
        # --- INSTAGRAM STORY ---
        print("🤳 IG Story: Uploading...")
        ig_res = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media", 
            data={'media_type': 'STORY', 'image_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in ig_res:
            time.sleep(20) # Processing buffer
            pub = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN}).json()
            if 'id' in pub: print("✅ IG Story LIVE!")
            else: print(f"❌ IG Publish Fail: {pub}")
        else:
            print(f"❌ IG Error: {ig_res.get('error', {}).get('message')}")

        # --- FACEBOOK STORY ---
        print("🎬 FB Story: Uploading...")
        fb_res = requests.post(f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories", 
            data={'url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in fb_res: 
            print("✅ FB Story LIVE!")
        else: 
            print(f"❌ FB Error: {fb_res.get('error', {}).get('message')}")

    except Exception as e: print(f"❌ Crash Error: {e}")

def main():
    if not IMGBB_API_KEY:
        print("⚠️ Secret 'IMGBB_API_KEY' is missing!")
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

if __name__ == "__main__":
    main()
