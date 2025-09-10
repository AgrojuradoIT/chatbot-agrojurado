import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de WhatsApp
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
WHATSAPP_APP_ID = os.getenv("WHATSAPP_APP_ID")

# URLs de la API
WHATSAPP_API_URL = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
WHATSAPP_TEMPLATE_API_URL = f"https://graph.facebook.com/v20.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"
WHATSAPP_MEDIA_API_URL = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/media"

# Headers comunes reutilizables
def get_whatsapp_headers() -> dict:
    """
    Retorna los headers HTTP estándar para todas las llamadas a la API de WhatsApp.
    
    Returns:
        dict: Headers con Authorization y Content-Type
    """
    return {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

# Estructuras de datos comunes
def get_base_whatsapp_data(to: str, message_type: str) -> dict:
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

# Validaciones comunes
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
