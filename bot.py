import os
import requests
import time

FB_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")
BRANCH = "main"

CAPTION = "Positron Academy Bhilwara 🚀 \nContact: 8104894648"

def post_content():
    # --- Pehle Videos (Reels) check karein ---
    if os.path.exists("videos"):
        all_vids = sorted([v for v in os.listdir("videos") if v.lower().endswith('.mp4')])
        # Yahan Reels ka logic add hoga jab aap file daal denge
        if all_vids: print(f"📹 Found {len(all_vids)} reels to post.")

    # --- Phir Images check karein (Purana Logic) ---
    if os.path.exists("images"):
        all_imgs = sorted([i for i in os.listdir("images") if i.lower().endswith(('.png', '.jpg'))])
        posted = []
        if os.path.exists("posted.txt"):
            with open("posted.txt", "r") as f: posted = f.read().splitlines()
        
        target = next((i for i in all_imgs if i not in posted), None)
        if target:
            print(f"📸 Posting Image: {target}")
            # ... (Wahi purana successful FB/IG image posting code)
            # Yahan humne jo kal successful code chalaya tha wahi use hoga.

if __name__ == "__main__":
    post_content()
