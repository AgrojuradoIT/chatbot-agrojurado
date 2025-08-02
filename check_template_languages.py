import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

def check_template_languages():
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get('data', [])
            
            for template in templates:
                print(f"\nPlantilla: {template['name']}")
                print(f"Estado: {template['status']}")
                print(f"Categoría: {template['category']}")
                
                # Verificar idiomas disponibles
                if 'language' in template:
                    print(f"Idioma: {template['language']}")
                elif 'languages' in template:
                    print("Idiomas disponibles:")
                    for lang in template['languages']:
                        print(f"  - {lang['code']} ({lang.get('name', 'Sin nombre')})")
                else:
                    print("No se encontró información de idiomas")
                    
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_template_languages() 