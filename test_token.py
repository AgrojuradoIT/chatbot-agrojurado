import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

print(f"Token: {WHATSAPP_ACCESS_TOKEN[:20]}..." if WHATSAPP_ACCESS_TOKEN else "No token found")
print(f"Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")

# Probar el token con una llamada simple
url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}"
headers = {
    "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ Token válido")
    else:
        print("❌ Token inválido o expirado")
        
except Exception as e:
    print(f"Error: {e}") 