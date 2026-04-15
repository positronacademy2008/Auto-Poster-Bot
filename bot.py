import os
import requests
import time

# Secrets se data
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")
BRANCH = "main"

CAPTION = "Positron Academy Bhilwara - Success Starts Here! 🚀 \nContact: 8104894648"

def post_to_fb_and_ig():
    if not os.path.exists("images"):
        print("❌ Error: 'images' folder nahi mila.")
        return
    
    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f:
            posted_images = f.read().splitlines()

    target_image = next((img for img in all_images if img not in posted_images), None)
    
    if not target_image:
        print("✅ Sabhi photos post ho chuki hain!")
        return

    print(f"🚀 Processing: {target_image}")
    image_path = os.path.join("images", target_image)
    
    # --- 1. FACEBOOK POST (Direct Upload) ---
    fb_url = "https://graph.facebook.com/v25.0/me/photos"
    try:
        with open(image_path, 'rb') as img_file:
            payload = {'caption': CAPTION, 'access_token': ACCESS_TOKEN}
            files = {'source': img_file}
            fb_res = requests.post(fb_url, data=payload, files=files).json()
        
        if 'id' in fb_res:
            print(f"✅ Facebook Success: Post ID {fb_res['id']}")
            # Success hone par hi list mein add karein
            with open("posted.txt", "a") as f:
                f.write(target_image + "\n")
        else:
            print(f"❌ Facebook Fail: {fb_res.get('error', {}).get('message')}")
    except Exception as e:
        print(f"❌ FB Exception: {e}")

    # --- 2. INSTAGRAM POST (URL Method) ---
    if IG_ACCOUNT_ID and REPO:
        # Public URL (Repo must be Public)
        img_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/images/{target_image}"
        
        # Step A: Container
        container_url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
        c_payload = {'image_url': img_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        
        try:
            c_res = requests.post(container_url, data=c_payload).json()
            if 'id' in c_res:
                creation_id = c_res['id']
                time.sleep(10) # Wait for processing
                
                # Step B: Publish
                publish_url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media_publish"
                p_res = requests.post(publish_url, data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}).json()
                
                if 'id' in p_res:
                    print(f"✅ Instagram Success: Post ID {p_res['id']}")
                else:
                    print(f"❌ IG Publish Fail: {p_res.get('error', {}).get('message')}")
            else:
                print(f"❌ IG Container Fail: {c_res.get('error', {}).get('message')}")
        except Exception as e:
            print(f"❌ IG Exception: {e}")

if __name__ == "__main__":
    post_to_fb_and_ig()
