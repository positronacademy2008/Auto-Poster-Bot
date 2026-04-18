import os
import requests
import time
from PIL import Image
import io

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")

CAPTION = (
    "Positron Academy Bhilwara 🚀\n"
    "Admission Open for BSTC, B.Ed, D.Pharma!\n"
    "📞 Contact: 8104894648"
)

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def prepare_media_for_story(input_path):
    """Image ko memory mein Story size banata hai"""
    try:
        img = Image.open(input_path).convert("RGB")
        w, h = img.size
        target_ratio = 9 / 16
        current_ratio = w / h

        if abs(current_ratio - target_ratio) > 0.05:
            print(f"📏 Auto-Padding: {input_path}")
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
        
        with open(input_path, "rb") as f: return f.read()
    except Exception as e:
        print(f"❌ Resize Error: {e}")
        return None

def post_story(filename):
    file_path = os.path.join('images', filename)
    story_bytes = prepare_media_for_story(file_path)
    if not story_bytes: return

    try:
        # --- INSTAGRAM STORY ---
        print(f"🤳 IG Story: {filename}...")
        ig_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        res = requests.post(ig_url, 
            params={'media_type': 'STORY', 'access_token': ACCESS_TOKEN},
            files={'image': story_bytes}
        ).json()
        
        if 'id' in res:
            time.sleep(30)
            requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                          data={'creation_id': res['id'], 'access_token': ACCESS_TOKEN})
            print("✅ IG Story Success!")

        # --- FACEBOOK STORY ---
        print(f"🎬 FB Story: {filename}...")
        fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories"
        f_res = requests.post(fb_url, 
            params={'access_token': ACCESS_TOKEN},
            files={'source': story_bytes}
        ).json()
        if 'id' in f_res: print("✅ FB Story Success!")

    except Exception as e: print(f"❌ Story Error: {e}")

def main():
    i_folder = 'images'
    posted = get_posted_files()
    
    if not os.path.exists(i_folder): return
    
    all_files = [f for f in sorted(os.listdir(i_folder)) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    pending_files = [f for f in all_files if f not in posted]

    # Restart Logic
    if all_files and not pending_files:
        print("♻️ Resetting Loop...")
        if os.path.exists("posted.txt"): os.remove("posted.txt")
        pending_files = all_files

    if pending_files:
        current_file = pending_files[0]
        print(f"🚀 Processing: {current_file}")
        post_story(current_file)
        mark_as_posted(current_file)

if __name__ == "__main__":
    main()
