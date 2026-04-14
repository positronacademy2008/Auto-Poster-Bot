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

# --- CONFIGURATION ---
# Yahan apna asli GitHub Username likhein
GITHUB_USER = "positronacademy2008" 
PRIVATE_REPO = "positron-storage"
# Parts ke naam check kar lein jo aapne upload kiye hain
PARTS = ["whatsapp_session.zip.001", "whatsapp_session.zip.002", "whatsapp_session.zip.003", "whatsapp_session.zip.004"]

def download_and_combine_session():
    token = os.environ.get("MY_GITHUB_TOKEN")
    if not token:
        print("❌ Error: MY_GITHUB_TOKEN secret nahi mila!")
        return False

    print("🛡️ Private Storage se parts download ho rahe hain...")
    try:
        with open("full_session.zip", "wb") as combined_file:
            for part in PARTS:
                url = f"https://raw.githubusercontent.com/positronacademy2008/positron-storage/main/{part}"
                headers = {'Authorization': f'token {token}'}
                res = requests.get(url, headers=headers)
                
                if res.status_code == 200:
                    combined_file.write(res.content)
                    print(f"✅ Downloaded and joined: {part}")
                else:
                    print(f"❌ Failed to download {part}. Status: {res.status_code}")
                    return False

        # Extracting the combined zip
        print("📦 Extracting session data...")
        with zipfile.ZipFile("full_session.zip", 'r') as zip_ref:
            zip_ref.extractall("session_data")
        return True
    except Exception as e:
        print(f"❌ Critical Error during download: {e}")
        return False

def setup_browser():
    print("🌐 Setting up Headless Chrome...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") # GitHub par screen nahi hoti
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Path logic: Session data folder ke andar jo whatsapp_session folder hai
    session_path = os.path.join(os.getcwd(), "session_data", "whatsapp_session")
    chrome_options.add_argument(f"--user-data-dir={session_path}")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def send_bulk_messages(driver):
    print("⏳ Loading WhatsApp Web...")
    driver.get("https://web.whatsapp.com")
    time.sleep(40) # Session bada hai toh load hone mein waqt lag sakta hai

    csv_path = "whatsapp/contacts.csv"
    if not os.path.exists(csv_path):
        print("❌ Error: whatsapp/contacts.csv file nahi mili!")
        return

    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            phone = "".join(filter(str.isdigit, row['phone']))
            name = row['name']
            # Aapka customized message
            msg = f"Namaste {name}, Positron Academy Bhilwara mein naya batch shuru ho raha hai! 🚀 Admsission Open. Contact: 8104894648"
            
            print(f"📩 Sending to {name} ({phone})...")
            # WhatsApp Direct Link ka use
            url = f"https://web.whatsapp.com/send?phone={phone}&text={requests.utils.quote(msg)}"
            driver.get(url)
            time.sleep(20) # Page aur Chat load hone ka wait

            try:
                # WhatsApp Web ka naya send button find karna
                send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                send_btn.click()
                print(f"✅ Message sent successfully to {name}!")
                time.sleep(10) # Gap zaroori hai block hone se bachne ke liye
            except Exception as e:
                print(f"⚠️ Skip: {name} ko message nahi gaya. (Error: {e})")

if __name__ == "__main__":
    # Step 1: Download session parts
    if download_and_combine_session():
        # Step 2: Setup Browser
        browser = setup_browser()
        # Step 3: Run Automation
        try:
            send_bulk_messages(browser)
        finally:
            browser.quit()
            print("🏁 Automation Task Finished.")
    else:
        print("❌ Session setup failed. Bot stopped.")
