import os
import requests
import csv

# GitHub Secrets se IDs uthana
WA_TOKEN = os.environ.get("WA_TOKEN")
WA_PHONE_ID = os.environ.get("WA_PHONE_NUMBER_ID")

def send_whatsapp_bulk():
    csv_path = "whatsapp/contacts.csv"
    if not os.path.exists(csv_path):
        print("❌ Error: whatsapp/contacts.csv file nahi mili!")
        return
    
    print("📢 Starting Positron Academy WhatsApp Bulk System...")
    
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Phone number saaf karna (sirf digits rakhein)
            phone = "".join(filter(str.isdigit, row['phone']))
            name = row['name']
            
            url = f"https://graph.facebook.com/v25.0/{WA_PHONE_ID}/messages"
            headers = {
                "Authorization": f"Bearer {WA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Shuruat mein 'hello_world' template use kar rahe hain
            data = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {
                    "name": "hello_world",
                    "language": { "code": "en_US" }
                }
            }
            
            try:
                res = requests.post(url, headers=headers, json=data).json()
                if 'messages' in res:
                    print(f"✅ Success: Message sent to {name} ({phone})")
                else:
                    print(f"❌ WA Error for {name}: {res.get('error', {}).get('message')}")
            except Exception as e:
                print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    send_whatsapp_bulk()
