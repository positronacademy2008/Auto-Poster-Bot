import os
import requests
import time
from PIL import Image, ImageOps
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")
REPO = os.environ.get("GITHUB_REPOSITORY")

def resize_image_for_story(input_path, output_path):
    print(f"🎨 Resizing Image: {input_path}")
    img = Image.open(input_path)
    w, h = img.size
    target_ratio = 9 / 16
    current_ratio = w / h

    if abs(current_ratio - target_ratio) > 0.01:
        # Nayi canvas 9:16 ratio ki
        new_h = int(w / target_ratio)
        if new_h < h:
            new_w = int(h * target_ratio)
            new_h = h
        else:
            new_w = w
        
        background = Image.new('RGB', (new_w, new_h), (0, 0, 0))
        offset = ((new_w - w) // 2, (new_h - h) // 2)
        background.paste(img, offset)
        background.save(output_path, quality=95)
    else:
        img.save(output_path)

def resize_video_for_story(input_path, output_path):
    print(f"🎬 Resizing Video: {input_path}")
    clip = VideoFileClip(input_path)
    w, h = clip.size
    target_ratio = 9/16
    
    if abs((w/h) - target_ratio) > 0.01:
        target_w = int(h * target_ratio)
        if target_w < w: # Agar video bahut wide hai
            target_h = int(w / target_ratio)
            target_w = w
        else:
            target_h = h

        bg = ColorClip(size=(target_w, target_h), color=(0,0,0)).set_duration(clip.duration)
        final_video = CompositeVideoClip([bg, clip.set_position("center")])
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    else:
        clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

def post_story_to_meta(folder, filename, is_video):
    temp_file = f"temp_{filename}"
    original_path = os.path.join(folder, filename)
    
    # Resize Logic
    if is_video: resize_video_for_story(original_path, temp_file)
    else: resize_image_for_story(original_path, temp_file)

    media_url = f"https://raw.githubusercontent.com/{REPO}/main/{temp_file}"
    
    try:
        # --- Instagram Story ---
        print(f"🤳 IG Story: Sending {filename}...")
        ig_base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
        payload = {'media_type': 'STORY', 'access_token': ACCESS_TOKEN}
        if is_video: payload['video_url'] = media_url
        else: payload['image_url'] = media_url
        
        res = requests.post(ig_base, data=payload).json()
        if 'id' in res:
            time.sleep(40) # Wait for processing
            requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish", 
                          data={'creation_id': res['id'], 'access_token': ACCESS_TOKEN})
            print("✅ IG Story Live!")

        # --- FB Story ---
        print(f"🎬 FB Story: Sending {filename}...")
        fb_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories"
        if not is_video:
            f_res = requests.post(fb_url, data={'url': media_url, 'access_token': ACCESS_TOKEN}).json()
            if 'id' in f_res: print("✅ FB Story Live!")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    # ... logic same as before but only calling post_story_to_meta ...
    # Testing for 1 file only for now to save time
    v_f, i_f = 'video', 'images'
    # Sirf pehli pending file uthayega testing ke liye
    if os.path.exists(i_f):
        imgs = [f for f in os.listdir(i_f) if f.endswith(('.png', '.jpg'))]
        if imgs: post_story_to_meta(i_f, imgs[0], False)

if __name__ == "__main__":
    main()
