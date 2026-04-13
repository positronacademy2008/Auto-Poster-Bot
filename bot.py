import os
import requests

ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
CAPTION = "Positron Academy Bhilwara - Success Starts Here! 🚀 \nContact: 8104894648"

def post_to_facebook():
    if not os.path.exists("images"): return
    
    all_images = sorted([img for img in os.listdir("images") if img.lower().endswith(('.png', '.jpg', '.jpeg'))])
    posted_images = []
    if os.path.exists("posted.txt"):
        with open("posted.txt", "r") as f: posted_images = f.read().splitlines()

    target_image = next((img for img in all_images if img not in posted_images), None)
    if not target_image: return

    print(f"Final Attempt: Uploading {target_image} using Feed API")
    image_path = os.path.join("images", target_image)
    
    # Naya Endpoint: Isse Metadata error nahi aata
    url = "https://graph.facebook.com/v25.0/me/photos"

    with open(image_path, 'rb') as img_file:
        payload = {
            'caption': CAPTION,
            'access_token': ACCESS_TOKEN
        }
        files = {'source': img_file}
        response = requests.post(url, data=payload, files=files)
        
    result = response.json()
    print(f"Response: {result}")

    if response.status_code == 200 or 'id' in result:
        with open("posted.txt", "a") as f: f.write(target_image + "\n")
        print("BHOOM! Positron Academy par post ho gayi! 🚀")
    else:
        print(f"Error: {result.get('error', {}).get('message')}")

if __name__ == "__main__":
    post_to_facebook()
