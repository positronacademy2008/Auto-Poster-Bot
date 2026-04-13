import os
import requests
import time

# Secrets se data uthana
FB_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")
BRANCH = "main" # Agar aapki branch ka naam master hai toh ise badal dein

CAPTION = "Positron Academy Bhilwara - Shaping Your Future! 🚀 \nContact: 8104894648"

def post_to_fb_and_ig():
    if not os.path.exists("images"):
        print("❌ ERROR: 'images' folder nahi mila!")
        return
    
    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f:
            posted_images = f.read().splitlines()

    target_image = next((img for img in all_images if img not in posted_images), None)
    
    if not target_image:
        print("✅ INFO: Sabhi images post ho chuki hain.")
        return

    print(f"🚀 Processing: {target_image} for Facebook & Instagram...")
    image_path = os.path.join("images", target_image)
    
    # --- 1. FACEBOOK POST ---
    fb_url = "https://graph.facebook.com/v25.0/me/photos"
    try:
        with open(image_path, 'rb') as img_file:
            fb_res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': FB_TOKEN}, files={'source': img_file}).json()
        
        if 'id' in fb_res:
            print(f"✅ FACEBOOK SUCCESS: Post ID {fb_res['id']}")
            with open("posted.txt", "a") as f:
                f.write(target_image + "\n")
        else:
            print(f"❌ FACEBOOK FAIL: {fb_res.get('error', {}).get('message')}")
    except Exception as e:
        print(f"❌ FB CRITICAL ERROR: {e}")

    # --- 2. INSTAGRAM POST ---
    if IG_ID:
        # Public URL banana: Ye tabhi chalega jab aapki REPO PUBLIC hogi
        img_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/images/{target_image}"
        print(f"📸 Instagram Image URL: {img_url}")

        # Step A: Container Upload
        container_url = f"https://graph.facebook.com/v25.0/{IG_ID}/media"
        c_payload = {'image_url': img_url, 'caption': CAPTION, 'access_token': FB_TOKEN}
        
        try:
            c_res = requests.post(container_url, data=c_payload).json()
            if 'id' in c_res:
                creation_id = c_res['id']
                print(f"🔄 IG Image Process ho rahi hai (ID: {creation_id})...")
                time.sleep(10) # 10 seconds wait taaki Meta photo process kar le

                # Step B: Publish
                publish_url = f"https://graph.facebook.com/v25.0/{IG_ID}/media_publish"
                p_res = requests.post(publish_url, data={'creation_id': creation_id, 'access_token': FB_TOKEN}).json()
                
                if 'id' in p_res:
                    print(f"✅ INSTAGRAM SUCCESS: Post ID {p_res['id']}")
                else:
                    print(f"❌ INSTAGRAM PUBLISH FAIL: {p_res.get('error', {}).get('message')}")
            else:
                print(f"❌ INSTAGRAM CONTAINER FAIL: {c_res.get('error', {}).get('message')}")
                print("💡 Tip: Check karein ki GitHub Repo 'Public' hai ya nahi.")
        except Exception as e:
            print(f"❌ IG CRITICAL ERROR: {e}")
    else:
        print("⚠️ SKIP: IG_ACCOUNT_ID nahi mila.")

if __name__ == "__main__":
    post_to_fb_and_ig()
