"""
Módulo core de WhatsApp Business API
Contiene funciones de configuración y utilidades base
"""

import os
from typing import Dict
from .whatsapp_config import (
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_BUSINESS_ACCOUNT_ID,
    WHATSAPP_APP_ID,
    WHATSAPP_API_URL,
    WHATSAPP_TEMPLATE_API_URL,
    WHATSAPP_MEDIA_API_URL
)

def validate_whatsapp_config() -> bool:
    """
    Valida que todas las credenciales de WhatsApp estén configuradas.
    
    Returns:
        bool: True si todas las credenciales están presentes
    """
    required_vars = [
        WHATSAPP_ACCESS_TOKEN,
        WHATSAPP_PHONE_NUMBER_ID,
        WHATSAPP_BUSINESS_ACCOUNT_ID
    ]
    return all(required_vars)

def get_whatsapp_headers() -> Dict[str, str]:
    """
    Retorna los headers HTTP estándar para todas las llamadas a la API de WhatsApp.
    
    Returns:
        dict: Headers con Authorization y Content-Type
    """
    return {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

def get_base_whatsapp_data(to: str, message_type: str) -> Dict[str, str]:
    """
    Retorna la estructura base de datos para mensajes de WhatsApp.
    
    Args:
        to: Número de teléfono destino
        message_type: Tipo de mensaje (text, template, document, etc.)
    
    Returns:
        dict: Estructura base de datos
    """
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": message_type,
    }

def get_whatsapp_app_id() -> str:
    """
    Obtiene el WhatsApp App ID configurado.
    
    Returns:
        str: WhatsApp App ID o cadena vacía si no está configurado
    """
    return WHATSAPP_APP_ID or ""

def get_whatsapp_api_url() -> str:
    """
    Obtiene la URL base de la API de WhatsApp.
    
    Returns:
        str: URL de la API de WhatsApp
    """
    return WHATSAPP_API_URL

def get_whatsapp_template_api_url() -> str:
    """
    Obtiene la URL de la API de plantillas de WhatsApp.
    
    Returns:
        str: URL de la API de plantillas
    """
    return WHATSAPP_TEMPLATE_API_URL

def get_whatsapp_media_api_url() -> str:
    """
    Obtiene la URL de la API de medios de WhatsApp.
    
    Returns:
        str: URL de la API de medios
    """
    return WHATSAPP_MEDIA_API_URL
