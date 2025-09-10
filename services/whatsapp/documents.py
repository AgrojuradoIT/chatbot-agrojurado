"""
Módulo de documentos de WhatsApp Business API
Contiene funciones específicas para envío de documentos PDF
"""

import json
import os
import requests
from typing import Optional
from .core import get_whatsapp_headers, get_whatsapp_api_url
from .media import upload_media_to_whatsapp, upload_media_from_url_to_whatsapp

def send_whatsapp_document(to: str, file_path: str, filename: str = None) -> bool:
    """
    Envía un documento (PDF) a un número de WhatsApp a través de la API de Meta.
    
    Args:
        to: Número de teléfono destino
        file_path: Ruta del archivo PDF
        filename: Nombre del archivo (opcional, si no se proporciona usa el nombre del archivo)
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    if not filename:
        filename = os.path.basename(file_path)
    
    # Primero subir el archivo a WhatsApp
    media_id = upload_media_to_whatsapp(file_path, "application/pdf")
    
    if not media_id:
        print(f"❌ Error: No se pudo subir el archivo PDF")
        return False
    
    # Luego enviar el documento usando el media_id
    headers = get_whatsapp_headers()
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename
        }
    }

    print(f"--- Enviando documento PDF a WhatsApp ---")
    print(f"URL: {get_whatsapp_api_url()}")
    print(f"Archivo: {filename}")
    print(f"Media ID: {media_id}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        print(f"Documento PDF enviado a {to} exitosamente.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar documento PDF a {to}: {e}")
        return False

def send_whatsapp_document_url(to: str, file_url: str, filename: str = None) -> bool:
    """
    Envía un documento (PDF) desde una URL a un número de WhatsApp a través de la API de Meta.
    
    Args:
        to: Número de teléfono destino
        file_url: URL del archivo PDF
        filename: Nombre del archivo (opcional)
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    if not filename:
        filename = os.path.basename(file_url)
    
    # Primero subir el archivo desde la URL a WhatsApp
    media_id = upload_media_from_url_to_whatsapp(file_url, "application/pdf")
    
    if not media_id:
        print(f"❌ Error: No se pudo subir el archivo PDF desde la URL")
        return False
    
    # Luego enviar el documento usando el media_id
    headers = get_whatsapp_headers()
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename
        }
    }

    print(f"--- Enviando documento PDF desde URL a WhatsApp ---")
    print(f"URL: {get_whatsapp_api_url()}")
    print(f"Archivo: {filename}")
    print(f"URL del archivo: {file_url}")
    print(f"Media ID: {media_id}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        print(f"Documento PDF enviado a {to} exitosamente.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar documento PDF a {to}: {e}")
        return False
