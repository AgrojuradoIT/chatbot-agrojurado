"""
Módulo de mensajería de WhatsApp Business API
Contiene funciones para envío de mensajes de texto e interactivos
"""

import json
import requests
from typing import List, Dict
from .core import (
    validate_whatsapp_config,
    get_whatsapp_headers,
    get_base_whatsapp_data,
    get_whatsapp_api_url
)

def send_whatsapp_message(to: str, message: str) -> bool:
    """
    Envía un mensaje de texto a un número de WhatsApp a través de la API de Meta.
    
    Args:
        to: Número de teléfono destino
        message: Mensaje de texto a enviar
    
    Returns:
        bool: True si se envió exitosamente, False en caso contrario
    """
    # Validar configuración
    if not validate_whatsapp_config():
        print("❌ Error: Configuración de WhatsApp incompleta")
        return False
    
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    # Construir datos usando función helper
    data = get_base_whatsapp_data(to, "text")
    data["text"] = {"body": message}

    print(f"--- Enviando mensaje a WhatsApp ---")
    print(f"URL: {get_whatsapp_api_url()}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        print(f"Mensaje enviado a {to} exitosamente.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a {to}: {e}")
        return False

def send_whatsapp_interactive_buttons(to: str, body_text: str, buttons: List[Dict[str, str]]) -> bool:
    """
    Envía un mensaje interactivo con botones de respuesta rápida a WhatsApp.
    
    Args:
        to: Número de teléfono destino
        body_text: Texto principal del mensaje
        buttons: Lista de botones, cada uno con 'id' y 'title'
                Ejemplo: [{'id': '1', 'title': 'Quincena Anterior'}, {'id': '2', 'title': 'Quincena Reciente'}]
    
    Returns:
        bool: True si se envió exitosamente, False si hubo error
    """
    if not buttons or len(buttons) > 3:
        print("❌ Error: Se requieren entre 1 y 3 botones")
        return False
    
    # Validar que cada botón tenga los campos requeridos
    for i, button in enumerate(buttons):
        if not isinstance(button, dict) or 'id' not in button or 'title' not in button:
            print(f"❌ Error: El botón {i+1} debe tener 'id' y 'title'")
            return False
        if len(button['title']) > 20:
            print(f"❌ Error: El título del botón {i+1} no puede exceder 20 caracteres")
            return False
    
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    # Construir la estructura de botones para la API de WhatsApp
    interactive_buttons = []
    for button in buttons:
        interactive_buttons.append({
            "type": "reply",
            "reply": {
                "id": button['id'],
                "title": button['title']
            }
        })
    
    # Construir datos usando función helper
    data = get_base_whatsapp_data(to, "interactive")
    data["interactive"] = {
        "type": "button",
        "body": {
            "text": body_text
        },
        "action": {
            "buttons": interactive_buttons
        }
    }

    print(f"--- Enviando mensaje con botones a WhatsApp ---")
    print(f"URL: {get_whatsapp_api_url()}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        print(f"Mensaje con botones enviado a {to} exitosamente.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje con botones a {to}: {e}")
        return False
