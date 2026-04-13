import os
import requests
import time

# Secrets se data
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID") 
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY") # GitHub apne aap dega
BRANCH = "main" # Agar aapki branch ka naam 'master' hai toh ise badal dein

CAPTION = "Positron Academy Bhilwara - Success Starts Here! 🚀 \nContact: 8104894648"

def post_to_fb_and_ig():
    if not os.path.exists("images"): return
    
    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f: posted_images = f.read().splitlines()

    target_image = next((img for img in all_images if img not in posted_images), None)
    if not target_image:
        print("Sabhi photos post ho chuki hain!")
        return

    print(f"Toh chaliye shuru karte hain: {target_image}")
    image_path = os.path.join("images", target_image)
    
    # --- 1. FACEBOOK POST (Seedha file upload) ---
    fb_url = "https://graph.facebook.com/v25.0/me/photos"
    with open(image_path, 'rb') as img_file:
        fb_res = requests.post(fb_url, data={'caption': CAPTION, 'access_token': ACCESS_TOKEN}, files={'source': img_file}).json()
        
    if 'id' in fb_res:
        print("✅ Facebook BHOOM! 🚀")
        # Record save kar rahe hain
        with open("posted.txt", "a") as f: f.write(target_image + "\n")
    else:
        print(f"❌ Facebook Error: {fb_res.get('error', {}).get('message')}")

    # --- 2. INSTAGRAM POST (Link ke zariye) ---
    if IG_ACCOUNT_ID and GITHUB_REPO:
        # GitHub se photo ka public link banana
        img_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/images/{target_image}"
        print("Instagram ke liye photo process ho rahi hai...")
        
        # IG Step A: Container banana (Meta pehle photo upload karta hai)
        ig_container_url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media"
        container_payload = {'image_url': img_url, 'caption': CAPTION, 'access_token': ACCESS_TOKEN}
        container_res = requests.post(ig_container_url, data=container_payload).json()
        
        if 'id' in container_res:
            creation_id = container_res['id']
            # Instagram ko thoda time chahiye hota hai process karne ke liye
            time.sleep(5) 
            
            # IG Step B: Container ko Publish karna
            ig_publish_url = f"https://graph.facebook.com/v25.0/{IG_ACCOUNT_ID}/media_publish"
            publish_payload = {'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
            publish_res = requests.post(ig_publish_url, data=publish_payload).json()
            
            if 'id' in publish_res:
                print("✅ Instagram BHOOM! 🚀")
            else:
                print(f"❌ IG Publish Error: {publish_res.get('error', {}).get('message')}")
        else:
            print(f"❌ IG Container Error: {container_res.get('error', {}).get('message')}")
            print("Tip: Check karein ki GitHub repo Public hai aur Token mein IG permissions hain.")

if __name__ == "__main__":
    post_to_fb_and_ig()
