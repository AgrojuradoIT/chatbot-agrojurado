import requests
import os
import json

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

def send_whatsapp_message(to: str, message: str):
    """
    Envía un mensaje de texto a un número de WhatsApp a través de la API de Meta.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    print(f"--- Enviando mensaje a WhatsApp ---")
    print(f"URL: {WHATSAPP_API_URL}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        print(f"Mensaje enviado a {to} exitosamente.")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a {to}: {e}")
        return None