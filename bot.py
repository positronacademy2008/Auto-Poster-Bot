import os
import requests

# GitHub Secrets se keys apne aap utha lega
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
PAGE_ID = os.environ.get("PAGE_ID")

# Caption jo har post ke saath jayega
CAPTION = "New batches are starting soon at Positron Academy! 🚀 \nContact: 8104894648"

def post_to_facebook():
    # 'images' folder check karna
    if not os.path.exists("images"):
        print("Images folder nahi mila!")
        return
        
    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    
    # Pehle post ho chuki images ki list
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f:
            posted_images = f.read().splitlines()
            
    # Pehli aisi image dhoondna jo naya ho
    target_image = None
    for img in all_images:
        if img not in posted_images:
            target_image = img
            break
            
    if not target_image:
        print("Koi nayi image nahi mili!")
        return
        
    image_path = os.path.join("images", target_image)
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos"
    
    # Facebook par bhejna
    with open(image_path, 'rb') as img_file:
        files = {'source': img_file}
        data = {'message': CAPTION, 'access_token': ACCESS_TOKEN}
        response = requests.post(url, files=files, data=data)
        
    if response.status_code == 200:
        print(f"Success! {target_image} post ho gayi.")
        with open("posted.txt", "a") as f:
            f.write(target_image + "\n")
    else:
        print("Error:", response.json())

if __name__ == "__main__":
    post_to_facebook()
