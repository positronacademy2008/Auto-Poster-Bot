import os
import requests
import time
from PIL import Image
import io

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")

def get_posted_files():
    if not os.path.exists("posted.txt"): return set()
    with open("posted.txt", "r") as f: return set(line.strip() for line in f)

def mark_as_posted(filename):
    with open("posted.txt", "a") as f: f.write(filename + "\n")

def get_padded_image_bytes(input_path):
    """Patti laga kar virtual file banata hai"""
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    target_ratio = 9 / 16
    new_h = int(w / target_ratio) if (int(w / target_ratio) >= h) else h
    new_w = int(h * target_ratio) if new_h == h else w
    
    new_img = Image.new('RGB', (new_w, new_h), (0, 0, 0))
    new_img.paste(img, ((new_w - w) // 2, (new_h - h) // 2))
    
    img_byte_arr = io.BytesIO()
    # Save with highest quality to trick Meta's filter
    new_img.save(img_byte_arr, format='JPEG', quality=100)
    # Move pointer to beginning of file
    img_byte_arr.seek(0)
    return img_byte_arr

def post_story(filename):
    file_path = os.path.join('images', filename)
    print(f"🚀 Processing: {filename}")
    
    # Ye bytes nahi hain, ek virtual file object hai!
    image_file = get_padded_image_bytes(file_path)

    try:
        # --- FACEBOOK STORY (FormData approach) ---
        print("🎬 FB Story: Uploading File Form Data...")
        fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories"
        # Bhejne ka tareeka badla hai: 'source' ke andar proper file format diya hai
        fb_res = requests.post(
            fb_url, 
            data={'access_token': ACCESS_TOKEN},
            files={'source': ('story.jpg', image_file, 'image/jpeg')}
        ).json()
        
        if 'id' in fb_res: 
            print("✅ FB Story Live!")
        else: 
            print(f"❌ FB Fail: {fb_res}")

        # Resetting file pointer for next upload
        image_file.seek(0)

        # --- INSTAGRAM STORY (Reel API as fallback) ---
        # Note: Instagram ki Story API direct Form Data mana karti hai!
        # Isliye hum Instagram Feed/Reel endpoint use kar rahe hain test ke liye.
        # Agar error solve ho gaya tab hum wapis Story endpoint daalenge.
        print("🤳 IG Post: Uploading as Feed (To bypass Story Filter)...")
        ig_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        # Is test mein hum image_url nahi, seedha media dalenge
        ig_res = requests.post(
            ig_url,
            data={'caption': 'Positron Academy Admission Open!', 'access_token': ACCESS_TOKEN},
            files={'image': ('story.jpg', image_file, 'image/jpeg')}
        ).json()

        if 'id' in ig_res:
            time.sleep(20)
            pub = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                data={'creation_id': ig_res['id'], 'access_token': ACCESS_TOKEN}).json()
            if 'id' in pub: 
                print("✅ IG Media Live!")
            else: 
                print(f"❌ IG Publish Fail: {pub}")
        else:
            print(f"❌ IG Fail: {ig_res}")

    except Exception as e: print(f"❌ Error: {e}")

def main():
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
