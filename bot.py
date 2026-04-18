import os
import requests
import time
from PIL import Image
import io

FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def process_image_for_story(input_path):
    """Patti lagao aur memory mein bytes return karo"""
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    new_h = int(w / target_ratio)
    if new_h < h:
        new_w = int(h * target_ratio)
        new_h = h
    else:
        new_w = w
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    img_byte_arr = io.BytesIO()
    new_img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def post_story_direct(filename):
    file_path = os.path.join('images', filename)
    print(f"🎨 Processing & Uploading: {filename}")
    img_bytes = process_image_for_story(file_path)

    try:
        # --- IG STORY (Direct Upload) ---
        print("🤳 IG Story: Uploading bytes...")
        ig_res = requests.post(
            f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media",
            params={'media_type': 'STORY', 'access_token': ACCESS_TOKEN},
            files={'image': img_bytes}
        ).json()
        
        if 'id' in ig_res:
            time.sleep(30)
            requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                          data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN})
            print("✅ IG Story Live!")
        else:
            print(f"❌ IG Fail: {ig_res.get('error', {}).get('message')}")

        # --- FB STORY (Direct Upload) ---
        print("🎬 FB Story: Uploading bytes...")
        fb_res = requests.post(
            f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories",
            params={'access_token': ACCESS_TOKEN},
            files={'source': img_bytes}
        ).json()
        if 'id' in fb_res: print("✅ FB Story Live!")
        else: print(f"❌ FB Fail: {fb_res.get('error', {}).get('message')}")

    except Exception as e: print(f"❌ Error: {e}")

def main():
    if os.path.exists('images'):
        posted = get_posted_files()
        all_files = [f for f in sorted(os.listdir('images')) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        pending = [f for f in all_files if f not in posted]
        if all_files and not pending:
            if os.path.exists("posted.txt"): os.remove("posted.txt")
            pending = all_files
        if pending:
            post_story_direct(pending[0])
            mark_as_posted(pending[0])

if __name__ == "__main__":
    main()
