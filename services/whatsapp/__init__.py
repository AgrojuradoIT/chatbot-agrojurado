"""
Módulo de WhatsApp Business API
Proporciona funcionalidades para mensajería, multimedia y plantillas
"""

# Importar todas las funciones principales para mantener compatibilidad
from .core import (
    validate_whatsapp_config,
    get_whatsapp_headers,
    get_base_whatsapp_data
)

from .messaging import (
    send_whatsapp_message,
    send_whatsapp_interactive_buttons
)

from .media import (
    upload_media_to_whatsapp,
    upload_media_from_url_to_whatsapp,
    upload_media_for_template,
    upload_media_from_base64,
    upload_media_from_base64_for_template
)

from .templates import (
    create_whatsapp_template,
    create_whatsapp_template_with_media,
    create_simple_template_with_media,
    create_whatsapp_template_with_image_url,
    create_simple_template_with_image_url,
    get_whatsapp_templates,
    send_whatsapp_template,
    send_whatsapp_template_with_media,
    delete_whatsapp_template,
    create_template_with_local_media,
    create_template_with_base64_media,
    archive_template,
    unarchive_template,
    get_archived_templates
)

from .documents import (
    send_whatsapp_document,
    send_whatsapp_document_url
)

from .users import (
    create_or_update_whatsapp_user,
    get_all_whatsapp_users
)

# Función de utilidad para formatear nombres de plantillas
from .templates import format_template_name

# Función de utilidad para obtener idioma de plantillas
from .templates import get_template_language

__all__ = [
    # Core
    'validate_whatsapp_config',
    'get_whatsapp_headers',
    'get_base_whatsapp_data',
    
    # Messaging
    'send_whatsapp_message',
    'send_whatsapp_interactive_buttons',
    
    # Media
    'upload_media_to_whatsapp',
    'upload_media_from_url_to_whatsapp',
    'upload_media_for_template',
    'upload_media_from_base64',
    'upload_media_from_base64_for_template',
    
    # Templates
    'create_whatsapp_template',
    'create_whatsapp_template_with_media',
    'create_simple_template_with_media',
    'create_whatsapp_template_with_image_url',
    'create_simple_template_with_image_url',
    'get_whatsapp_templates',
    'send_whatsapp_template',
    'send_whatsapp_template_with_media',
    'delete_whatsapp_template',
    'create_template_with_local_media',
    'create_template_with_base64_media',
    'archive_template',
    'unarchive_template',
    'get_archived_templates',
    
    # Documents
    'send_whatsapp_document',
    'send_whatsapp_document_url',
    
    # Users
    'create_or_update_whatsapp_user',
    'get_all_whatsapp_users',
    
    # Utilities
    'format_template_name',
    'get_template_language'
]
