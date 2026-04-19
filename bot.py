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
    """Image ko 9:16 Story format mein convert karke ImgBB URL laata hai"""
    print(f"🎨 Processing Image: {input_path}")
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    
    if (w / h) > target_ratio:
        new_h = int(w / target_ratio)
        new_w = w
    else:
        new_w = int(h * target_ratio)
        new_h = h
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    # Save to buffer
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='JPEG', quality=95)
    img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    print("☁️ Uploading to ImgBB...")
    # Sahi tareeka: Base URL aur Params alag-alag
    url = "https://api.imgbb.com/1/upload"
    params = {"key": IMGBB_API_KEY}
    data = {"image": img_b64, "expiration": 1200}
    
    res = requests.post(url, params=params, data=data).json()
    
    if res.get('success'):
        direct_url = res['data']['url']
        print(f"✅ URL Ready: {direct_url}")
        return direct_url
    else:
        print(f"❌ ImgBB Fail: {res}")
        return None

def post_story(filename):
    file_path = os.path.join('images', filename)
    print(f"🚀 Starting Story Post: {filename}")
    
    media_url = process_and_get_url(file_path)
    if not media_url: return

    # Meta ko URL milne mein thoda samay dein
    time.sleep(15)

    try:
        # --- INSTAGRAM STORY ---
        print("🤳 IG Story: Posting...")
        ig_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        ig_res = requests.post(ig_url, data={
            'media_type': 'STORY', 
            'image_url': media_url, 
            'access_token': ACCESS_TOKEN
        }).json()
        
        if 'id' in ig_res:
            time.sleep(25)
            requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                          data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN})
            print("✅ Instagram Story LIVE!")
        else:
            print(f"❌ IG Error: {ig_res.get('error', {}).get('message')}")

        # --- FACEBOOK STORY ---
        print("🎬 FB Story: Posting...")
        fb_photo_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        fb_photo = requests.post(fb_photo_url, data={
            'url': media_url, 
            'published': 'false', 
            'temporary': 'true', 
            'access_token': ACCESS_TOKEN
        }).json()
        
        if 'id' in fb_photo:
            requests.post(f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories", 
                          data={'photo_id': fb_photo['id'], 'access_token': ACCESS_TOKEN})
            print("✅ Facebook Story LIVE!")
        else:
            print(f"❌ FB Error: {fb_photo.get('error', {}).get('message')}")

    except Exception as e: print(f"❌ Crash: {e}")

def main():
    if not all([IMGBB_API_KEY, ACCESS_TOKEN, FB_PAGE_ID, IG_ACCOUNT_ID]):
        print("⚠️ Secrets missing!")
        return

    if os.path.exists('images'):
        posted = get_posted_files()
        all_files = [f for f in sorted(os.listdir('images')) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        pending = [f for f in all_files if f not in posted]
        
        if all_files and not pending:
            os.remove("posted.txt")
            pending = all_files

        if pending:
            post_story(pending[0])
            mark_as_posted(pending[0])

if __name__ == "__main__":
    main()
