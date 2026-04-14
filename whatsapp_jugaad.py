import os
import requests
import zipfile
import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# --- CONFIGURATION ---
GITHUB_USER = "positronacademy2008" 
PRIVATE_REPO = "positron-storage"
BRANCH = "main" 
PARTS = ["whatsapp_session_2.zip.001", "whatsapp_session_2.zip.002", "whatsapp_session_2.zip.003", "whatsapp_session_2.zip.004"]

def download_and_combine_session():
    token = os.environ.get("MY_GITHUB_TOKEN")
    print("🛡️ Private Storage se login data download ho raha hai...")
    try:
        with open("full_session.zip", "wb") as combined_file:
            for part in PARTS:
                url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{PRIVATE_REPO}/{BRANCH}/{part}"
                headers = {'Authorization': f'token {token}'}
                res = requests.get(url, headers=headers)
                if res.status_code == 200:
                    combined_file.write(res.content)
                    print(f"✅ Part joined: {part}")
                else:
                    print(f"❌ Part download fail: {part} (Status: {res.status_code})")
                    return False
        
        # Extract karna (Direct folder mein)
        with zipfile.ZipFile("full_session.zip", 'r') as zip_ref:
            zip_ref.extractall("session_data")
        print("📦 Extraction complete.")
        return True
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return False

def setup_browser():
    print("🌐 Setting up Chrome...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Path ko ek dum perfect point karna
    # Note: Aapki zip ke andar folder ka naam 'whatsapp_session' hona chahiye
    base_path = os.getcwd()
    session_path = os.path.join(base_path, "session_data", "whatsapp_session")
    
    print(f"📂 Looking for session at: {session_path}")
    chrome_options.add_argument(f"--user-data-dir={session_path}")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def send_bulk_messages(driver):
    print("⏳ WhatsApp Web load ho raha hai...")
    driver.get("https://web.whatsapp.com")
    time.sleep(60) # Pura load hone ka wait (GitHub Actions slow hota hai)

    # Check if logged in or asking for QR
    if "landing" in driver.current_url:
        print("❌ ERROR: Login session kaam nahi kar raha! QR Code mang raha hai.")
        # Iska matlab aapka zip wala session data sahi nahi hai
        return

    csv_path = "whatsapp/contacts.csv"
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            phone = "".join(filter(str.isdigit, row['phone']))
            name = row['name']
            msg = f"Namaste {name}, Positron Academy Bhilwara mein naya batch shuru ho raha hai! 🚀 Contact: 8104894648"
            
            print(f"📩 Sending to {name} ({phone})...")
            url = f"https://web.whatsapp.com/send?phone={phone}&text={requests.utils.quote(msg)}"
            driver.get(url)
            
            # Message box load hone ka lamba wait
            time.sleep(45) 

            try:
                # 1. Pehle click karke focus laana
                actions = webdriver.ActionChains(driver)
                actions.send_keys(Keys.TAB) # Kabhi-kabhi focus ke liye zaroori hai
                time.sleep(2)
                
                # 2. Double Enter marna
                actions.send_keys(Keys.ENTER)
                time.sleep(2)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                
                print(f"✅ Message sent to {name}!")
                time.sleep(15) # Sync hone ke liye waqt
            except Exception as e:
                print(f"⚠️ Skip: {name} | Error: {e}")

if __name__ == "__main__":
    if download_and_combine_session():
        browser = setup_browser()
        try:
            send_bulk_messages(browser)
        finally:
            browser.quit()
            print("🏁 Process Finished.")
