#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del webhook de WhatsApp.
Este script simula el envío de un mensaje al webhook.
"""

import requests
import json

# URL del webhook local
WEBHOOK_URL = "http://localhost:8000/webhook"

# Ejemplo de payload que envía WhatsApp
test_payload = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "102290509592979",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "15550463664",
                            "phone_number_id": "105602542611421"
                        },
                        "contacts": [
                            {
                                "profile": {
                                    "name": "Test User"
                                },
                                "wa_id": "573001234567"
                            }
                        ],
                        "messages": [
                            {
                                "from": "573001234567",
                                "id": "wamid.HBgNNTczMDAxMjM0NTY3FQIAERgSODFFNDAzMENDNzZBQjU4QkMyMA==",
                                "timestamp": "1671727849",
                                "text": {
                                    "body": "hola"
                                },
                                "type": "text"
                            }
                        ]
                    },
                    "field": "messages"
                }
            ]
        }
    ]
}

def test_webhook():
    """Prueba el webhook con un mensaje de prueba."""
    print("🧪 Probando webhook de WhatsApp...")
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=test_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✅ Estado de respuesta: {response.status_code}")
        print(f"📄 Respuesta: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook funcionando correctamente!")
        else:
            print("❌ Error en el webhook")
            
    except Exception as e:
        print(f"❌ Error al conectar con el webhook: {e}")

if __name__ == "__main__":
    test_webhook()