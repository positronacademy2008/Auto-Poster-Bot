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

def process_and_upload_to_imgbb(input_path):
    """Patti lagao aur imgbb par direct raw link lo"""
    print(f"🎨 Processing Image: {input_path}")
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    new_h = int(w / target_ratio) if (int(w / target_ratio) >= h) else h
    new_w = int(h * target_ratio) if new_h == h else w
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='JPEG')
    img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    print("☁️ Uploading to ImgBB...")
    res = requests.post(
        f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}",
        data={'image': img_b64, 'expiration': 600}
    ).json()
    
    if res.get('success'):
        # CRITICAL FIX: Extracting the DIRECT display URL, not the viewing page URL
        direct_url = res['data']['display_url'] 
        print(f"✅ Direct ImgBB URL Ready: {direct_url}")
        return direct_url
    else:
        print(f"❌ ImgBB Error: {res}")
        return None

def post_story(filename):
    file_path = os.path.join('images', filename)
    media_url = process_and_upload_to_imgbb(file_path)
    
    if not media_url:
        print("⚠️ Skipping Meta upload due to ImgBB failure.")
        return

    # Chota wait taaki ImgBB ka link global servers par poori tarah propagate ho jaye
    print("⏳ Waiting 15 seconds for ImgBB link propagation...")
    time.sleep(15)

    try:
        # --- IG STORY ---
        print(f"🤳 IG Story: Sending Direct URL to Meta...")
        ig_res = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media", 
            data={'media_type': 'STORY', 'image_url': media_url, 'access_token': ACCESS_TOKEN}).json()
        
        if 'id' in ig_res:
            print("⏳ IG processing the URL...")
            time.sleep(20) 
            pub = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN}).json()
            if 'id' in pub: print("✅ IG Story Live!")
            else: print(f"❌ IG Publish Fail: {pub}")
        else:
            print(f"❌ IG Fail: {ig_res.get('error', {}).get('message')}")

        # --- FB STORY ---
        print(f"🎬 FB Story: Sending Direct URL to Meta...")
        fb_res = requests.post(f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories", 
            data={'url': media_url, 'access_token': ACCESS_TOKEN}).json()
        if 'id' in fb_res: print("✅ FB Story Live!")
        else: print(f"❌ FB Fail: {fb_res.get('error', {}).get('message')}")

    except Exception as e: print(f"❌ Error: {e}")

def main():
    if not IMGBB_API_KEY:
        print("⚠️ Secret 'IMGBB_API_KEY' is missing! Check GitHub Secrets.")
        return

    if os.path.exists('images'):
        posted = get_posted_files()
        all_files = [f for f in sorted(os.listdir('images')) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        pending = [f for f in all_files if f not in posted]
        
        if all_files and not pending:
            os.remove("posted.txt")
            pending = all_files

        if pending:
            print(f"🚀 Current File: {pending[0]}")
            post_story(pending[0])
            mark_as_posted(pending[0])

if __name__ == "__main__":
    main()
