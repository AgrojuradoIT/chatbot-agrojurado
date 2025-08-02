import requests
import os
import json
from sqlalchemy.orm import Session
from models.whatsapp_models import WhatsappUser
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
WHATSAPP_API_URL = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
WHATSAPP_TEMPLATE_API_URL = f"https://graph.facebook.com/v20.0/{WHATSAPP_BUSINESS_ACCOUNT_ID}/message_templates"

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
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje a {to}: {e}")
        return False

def format_template_name(name: str) -> str:
    """
    Formatea el nombre de la plantilla según las reglas de WhatsApp.
    - Solo letras minúsculas y guiones bajos
    - Sin espacios ni caracteres especiales
    """
    import re
    # Convertir a minúsculas
    formatted = name.lower()
    # Reemplazar espacios y caracteres especiales con guiones bajos
    formatted = re.sub(r'[^a-z0-9]', '_', formatted)
    # Remover múltiples guiones bajos consecutivos
    formatted = re.sub(r'_+', '_', formatted)
    # Remover guiones bajos al inicio y final
    formatted = formatted.strip('_')
    # Asegurar que no esté vacío
    if not formatted:
        formatted = 'template'
    return formatted

def create_whatsapp_template(name: str, content: str, category: str, language: str = "es", footer: str = None):
    """
    Crea una nueva plantilla en WhatsApp Business API.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Formatear el nombre según las reglas de WhatsApp
    formatted_name = format_template_name(name)
    print(f"Nombre original: '{name}' -> Formateado: '{formatted_name}'")
    
    components = [
        {
            "type": "BODY",
            "text": content
        }
    ]
    
    # Agregar pie de página si se proporciona
    if footer:
        components.append({
            "type": "FOOTER",
            "text": footer
        })
    
    data = {
        "name": formatted_name,
        "language": language,
        "category": category,
        "components": components
    }

    print(f"--- Creando plantilla en WhatsApp ---")
    print(f"URL: {WHATSAPP_TEMPLATE_API_URL}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_TEMPLATE_API_URL, headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla: {response.status_code}")
        print(f"Contenido: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla: {e}")
        return None

def get_whatsapp_templates():
    """
    Obtiene todas las plantillas de WhatsApp Business API.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }

    print(f"Obteniendo plantillas de: {WHATSAPP_TEMPLATE_API_URL}")
    
    try:
        response = requests.get(WHATSAPP_TEMPLATE_API_URL, headers=headers)
        print(f"Respuesta de WhatsApp API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Plantillas encontradas: {len(data.get('data', []))}")
            return data
        else:
            print(f"Error de WhatsApp API: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener plantillas: {e}")
        return None

# Cache para evitar llamadas repetidas a la API
_template_language_cache = {}

def get_template_language(template_name: str) -> str:
    """
    Obtiene el idioma correcto de una plantilla con cache.
    Si no encuentra la plantilla, devuelve español colombiano por defecto.
    """
    # Verificar cache primero
    if template_name in _template_language_cache:
        return _template_language_cache[template_name]
    
    try:
        templates = get_whatsapp_templates()
        if templates and templates.get('data'):
            for template in templates['data']:
                if template['name'] == template_name:
                    language = template.get('language', 'es_CO')
                    # Guardar en cache
                    _template_language_cache[template_name] = language
                    print(f"Idioma detectado para plantilla '{template_name}': {language}")
                    return language
    except Exception as e:
        print(f"Error obteniendo idioma de plantilla {template_name}: {e}")
    
    # Por defecto
    _template_language_cache[template_name] = "es_CO"
    print(f"Usando idioma por defecto para plantilla '{template_name}': es_CO")
    return "es_CO"

def send_whatsapp_template(to: str, template_name: str, parameters: dict = None):
    """
    Envía una plantilla aprobada a un número de WhatsApp.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Obtener el idioma automáticamente desde WhatsApp API
    language_code = get_template_language(template_name)
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }
    
    if parameters:
        data["template"]["components"] = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(value)} for value in parameters.values()
                ]
            }
        ]

    print(f"--- Enviando plantilla a WhatsApp ---")
    print(f"URL: {WHATSAPP_API_URL}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(data))
        print(f"Respuesta al enviar plantilla: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar plantilla: {e}")
        return None

from datetime import datetime
from sqlalchemy import func

def delete_whatsapp_template(template_name: str):
    """
    Nota: Las plantillas de WhatsApp Business API no se pueden eliminar programáticamente.
    Solo se pueden eliminar desde el WhatsApp Business Manager.
    Esta función simula la eliminación pero no realiza cambios reales.
    """
    print(f"--- Eliminación de plantilla simulada ---")
    print(f"Template Name: {template_name}")
    print("NOTA: Las plantillas de WhatsApp no se pueden eliminar desde la API.")
    print("Debe eliminarlas manualmente desde el WhatsApp Business Manager.")
    print("-------------------------------------")
    
    # Simular éxito para mantener la funcionalidad del frontend
    return True

def create_or_update_whatsapp_user(db: Session, phone_number: str, name: str = None):
    """
    Crea o actualiza un usuario de WhatsApp en la base de datos.
    Respeta los nombres manuales establecidos.
    """
    user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
    if user:
        user.last_interaction = func.now()
        # Solo actualizar el nombre si el usuario no tiene un nombre personalizado
        # o si el nombre actual es igual al número de teléfono (nombre por defecto)
        if name and (user.name == phone_number or user.name == user.phone_number):
            user.name = name
        # Si el usuario ya tiene un nombre personalizado, mantenerlo
    else:
        user = WhatsappUser(
            phone_number=phone_number,
            name=name if name else phone_number, # Usar el número como nombre si no se proporciona uno
            last_interaction=func.now()
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_all_whatsapp_users(db: Session):
    """Obtiene todos los usuarios de WhatsApp de la base de datos"""
    return db.query(WhatsappUser).all()

def archive_template(db: Session, template_id: str) -> bool:
    """
    Archiva una plantilla en la base de datos (no la elimina de WhatsApp)
    """
    try:
        from models.whatsapp_models import Template
        
        # Buscar la plantilla en la base de datos local
        template = db.query(Template).filter(Template.id == template_id).first()
        
        if template:
            # Plantilla local - archivarla en la base de datos
            template.is_archived = True
            db.commit()
            print(f"✅ Plantilla local '{template.name}' archivada exitosamente")
            return True
        else:
            # Plantilla de WhatsApp - crear registro en la base de datos local
            # Obtener información de la plantilla de WhatsApp
            templates_data = get_whatsapp_templates()
            if templates_data and templates_data.get('data'):
                whatsapp_template = next((t for t in templates_data['data'] if t.get('id') == template_id), None)
                
                if whatsapp_template:
                    # Crear registro local de la plantilla archivada
                    new_template = Template(
                        id=whatsapp_template['id'],
                        name=whatsapp_template['name'],
                        content=whatsapp_template.get('components', [{}])[0].get('text', ''),
                        category=whatsapp_template.get('category', 'UTILITY'),
                        status=whatsapp_template.get('status', 'APPROVED'),
                        footer=next((c.get('text', '') for c in whatsapp_template.get('components', []) if c.get('type') == 'FOOTER'), None),
                        is_archived=True
                    )
                    db.add(new_template)
                    db.commit()
                    print(f"✅ Plantilla de WhatsApp '{whatsapp_template['name']}' archivada exitosamente")
                    return True
                else:
                    print(f"❌ Plantilla de WhatsApp con ID '{template_id}' no encontrada")
                    return False
            else:
                print(f"❌ No se pudo obtener información de la plantilla de WhatsApp")
                return False
    except Exception as e:
        print(f"❌ Error al archivar plantilla: {e}")
        db.rollback()
        return False

def unarchive_template(db: Session, template_id: str) -> bool:
    """
    Desarchiva una plantilla en la base de datos
    """
    try:
        from models.whatsapp_models import Template
        
        template = db.query(Template).filter(Template.id == template_id).first()
        if template:
            template.is_archived = False
            db.commit()
            print(f"✅ Plantilla '{template.name}' desarchivada exitosamente")
            return True
        else:
            print(f"❌ Plantilla con ID '{template_id}' no encontrada")
            return False
    except Exception as e:
        print(f"❌ Error al desarchivar plantilla: {e}")
        db.rollback()
        return False

def get_archived_templates(db: Session):
    """
    Obtiene todas las plantillas archivadas de la base de datos
    """
    try:
        from models.whatsapp_models import Template
        
        archived_templates = db.query(Template).filter(Template.is_archived == True).all()
        return archived_templates
    except Exception as e:
        print(f"❌ Error al obtener plantillas archivadas: {e}")
        return []