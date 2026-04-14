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
from selenium.webdriver.common.keys import Keys # Naya: Enter marne ke liye

# --- CONFIGURATION ---
GITHUB_USER = "positronacademy2008" 
PRIVATE_REPO = "positron-storage"
BRANCH = "main" 
PARTS = ["whatsapp_session_2.zip.001", "whatsapp_session_2.zip.002", "whatsapp_session_2.zip.003", "whatsapp_session_2.zip.004"]

def download_and_combine_session():
    token = os.environ.get("MY_GITHUB_TOKEN")
    print(f"🛡️ Private Storage se parts download ho rahe hain...")
    try:
        with open("full_session.zip", "wb") as combined_file:
            for part in PARTS:
                url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{PRIVATE_REPO}/{BRANCH}/{part}"
                headers = {'Authorization': f'token {token}'}
                res = requests.get(url, headers=headers)
                if res.status_code == 200:
                    combined_file.write(res.content)
                    print(f"✅ Joined: {part}")
                else:
                    return False
        with zipfile.ZipFile("full_session.zip", 'r') as zip_ref:
            zip_ref.extractall("session_data")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def setup_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080") # Screen size fix
    session_path = os.path.join(os.getcwd(), "session_data", "whatsapp_session")
    chrome_options.add_argument(f"--user-data-dir={session_path}")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def send_bulk_messages(driver):
    print("⏳ Loading WhatsApp Web...")
    driver.get("https://web.whatsapp.com")
    time.sleep(50) # Thoda extra time loading ke liye

    csv_path = "whatsapp/contacts.csv"
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            phone = "".join(filter(str.isdigit, row['phone']))
            name = row['name']
            msg = f"Namaste {name}, Positron Academy Bhilwara mein naya batch shuru ho raha hai! 🚀 Admission Open. Contact: 8104894648"
            
            print(f"📩 Sending to {name} ({phone})...")
            # WhatsApp link par jaana
            url = f"https://web.whatsapp.com/send?phone={phone}&text={requests.utils.quote(msg)}"
            driver.get(url)
            
            # Message box load hone ka wait
            time.sleep(25) 

            try:
                # Jugaad: Button dhoondhne ke bajaye seedha ENTER marna
                actions = webdriver.ActionChains(driver)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                
                print(f"✅ Message sent to {name} (via Enter Key)!")
                time.sleep(8) # Agle message se pehle gap
            except Exception as e:
                print(f"⚠️ Skip: {name} | Error: {e}")

if __name__ == "__main__":
    if download_and_combine_session():
        browser = setup_browser()
        try:
            send_bulk_messages(browser)
        finally:
            browser.quit()
            print("🏁 Automation Task Finished.")
