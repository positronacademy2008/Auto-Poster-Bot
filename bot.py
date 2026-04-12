import os
import requests

ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
# Note: Page ID ki zaroorat padegi, check karein ki Secret mein PAGE_ID sahi hai
PAGE_ID = os.environ.get("PAGE_ID")
CAPTION = "Positron Academy Bhilwara - Success Starts Here! 🚀 \nContact: 8104894648"

def post_to_facebook():
    if not os.path.exists("images"):
        print("ERROR: 'images' folder nahi mila!")
        return

    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f:
            posted_images = f.read().splitlines()

    target_image = None
    for img in all_images:
        if img not in posted_images:
            target_image = img
            break

    if not target_image:
        print("INFO: Sabhi images post ho chuki hain.")
        return

    print(f"Uploading using New Method: {target_image}")
    image_path = os.path.join("images", target_image)
    
    # Naya rasta: /me/feed ya /{page_id}/photos bina publish_actions ke
    # Hum seedha Page ID par hit karenge
    url = f"https://graph.facebook.com/v25.0/{61585098452625}/photos"

    with open(image_path, 'rb') as img_file:
        # Dhyan dein: permissions ab 'pages_manage_posts' honi chahiye
        payload = {
            'caption': CAPTION,
            'access_token': ACCESS_TOKEN
        }
        files = {
            'file': img_file
        }
        response = requests.post(url, data=payload, files=files)
        
    result = response.json()
    print(f"Response: {result}")

    if response.status_code == 200 or 'id' in result:
        with open("posted.txt", "a") as f:
            f.write(target_image + "\n")
        print("BHOOM! Post Successful 🚀")
    else:
        print(f"Error: {result.get('error', {}).get('message')}")
        print("Tip: Check karein ki System User ke paas 'pages_manage_posts' permission hai ya nahi.")

if __name__ == "__main__":
    post_to_facebook()
