import os
import requests
import json

# --- CONFIGURATION ---
FB_PAGE_ID = os.environ.get("FB_PAGE_ID") 
ACCESS_TOKEN = os.environ.get("FB_PAGE_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")

def test_meta_permissions():
    print("=========================================")
    print("🔍 POSITRON ACADEMY - META DIAGNOSTIC BOT 🔍")
    print("=========================================\n")

    # 1. Test Token Permissions
    print("1️⃣ Testing Access Token Permissions...")
    token_url = f"https://graph.facebook.com/v19.0/debug_token?input_token={ACCESS_TOKEN}&access_token={ACCESS_TOKEN}"
    t_res = requests.get(token_url).json()
    
    if 'data' in t_res:
        scopes = t_res['data'].get('scopes', [])
        print(f"   ✅ Token is Valid.")
        print(f"   ✅ Permissions Found: {len(scopes)}")
        
        # Check specific important ones
        needed = ['pages_manage_posts', 'instagram_content_publish', 'pages_read_engagement']
        for n in needed:
            if n in scopes:
                print(f"   🟢 Has: {n}")
            else:
                print(f"   🔴 MISSING: {n}")
    else:
        print(f"   ❌ Token Error: {t_res}")

    print("\n-----------------------------------------")

    # 2. Test Instagram Account Capabilities
    print("2️⃣ Testing Instagram Account Capabilities...")
    ig_info_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}?fields=id,username,account_type&access_token={ACCESS_TOKEN}"
    ig_res = requests.get(ig_info_url).json()
    
    if 'username' in ig_res:
        print(f"   ✅ Connected IG Account: @{ig_res['username']}")
        
        # Test if the endpoint accepts STORY media type (Dry Run)
        print("   ⏳ Testing STORY endpoint directly...")
        test_payload = {
            'media_type': 'STORY',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/ca/ca.jpg', # Valid public URL
            'access_token': ACCESS_TOKEN
        }
        
        # We expect a failure because it's a dummy image, BUT we check the ERROR TYPE
        dry_run = requests.post(f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media", data=test_payload).json()
        
        error_msg = dry_run.get('error', {}).get('message', '')
        
        if "STORY\" is unknown" in error_msg:
            print("   🔴 CRITICAL FAILURE: Your Instagram account/app is NOT PERMITTED to post Stories.")
            print("      Solution: Your Instagram MUST be a 'Business' account, NOT a 'Creator' account.")
        elif "Invalid parameter" in error_msg:
            print("   ⚠️ WARNING: Story Endpoint is open, but it rejected the format.")
        else:
            print(f"   ℹ️ Meta Response: {dry_run}")
            
    else:
        print(f"   ❌ IG Account Error: {ig_res}")

    print("\n-----------------------------------------")

    # 3. Test Facebook Page Capabilities
    print("3️⃣ Testing Facebook Page Capabilities...")
    fb_info_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}?fields=id,name,access_token&access_token={ACCESS_TOKEN}"
    fb_res = requests.get(fb_info_url).json()

    if 'name' in fb_res:
        print(f"   ✅ Connected FB Page: {fb_res['name']}")
        
        print("   ⏳ Testing FB Photo Story endpoint...")
        # Dry run for FB
        fb_dry_run = requests.post(f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories", 
            data={'url': 'https://upload.wikimedia.org/wikipedia/commons/ca/ca.jpg', 'access_token': ACCESS_TOKEN}).json()
        
        err = fb_dry_run.get('error', {}).get('message', '')
        if err:
            print(f"   🔴 FB Story Post Error: {err}")
            print(f"   ℹ️ Full details: {fb_dry_run}")
    else:
        print(f"   ❌ FB Page Error: {fb_res}")

    print("\n=========================================")
    print("📋 END OF DIAGNOSTICS")
    print("=========================================")

if __name__ == "__main__":
    test_meta_permissions()
