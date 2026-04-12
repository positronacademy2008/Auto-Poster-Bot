import os
import requests

# GitHub Secrets se data uthayega
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
# v25.0 mein hum Page Token use kar rahe hain, isliye 'me' ka matlab hi Page hai
CAPTION = "Positron Academy Bhilwara - Shaping Your Future! 🚀 \nContact: 8104894648"

def post_to_facebook():
    # Folder check
    if not os.path.exists("images"):
        print("ERROR: 'images' folder nahi mila!")
        return

    # Sirf images files uthayega
    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f:
            posted_images = f.read().splitlines()

    # Nayi image select karna
    target_image = None
    for img in all_images:
        if img not in posted_images:
            target_image = img
            break

    if not target_image:
        print("INFO: Sabhi images post ho chuki hain.")
        return

    print(f"Uploading to Facebook: {target_image} using API v25.0")
    image_path = os.path.join("images", target_image)
    
    # v25.0 use kar rahe hain aur PAGE_ID ki jagah 'me' kyunki humne Page Token daala hai
    url = "https://graph.facebook.com/v25.0/me/photos"

    with open(image_path, 'rb') as img_file:
        files = {'source': img_file}
        data = {
            'message': CAPTION, 
            'access_token': ACCESS_TOKEN
        }
        response = requests.post(url, files=files, data=data)
        
    result = response.json()
    print(f"Response: {result}")

    if response.status_code == 200:
        with open("posted.txt", "a") as f:
            f.write(target_image + "\n")
        print("BHOOM! Post Successful 🚀")
    else:
        print(f"Fail ho gaya bhai: {result.get('error', {}).get('message')}")

if __name__ == "__main__":
    post_to_facebook()
