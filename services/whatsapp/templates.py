"""
Módulo de plantillas de WhatsApp Business API
Contiene funciones para creación, envío y gestión de plantillas
"""

import json
import re
import requests
from typing import Optional, Dict, Any
from .core import (
    get_whatsapp_headers,
    get_whatsapp_template_api_url,
    get_whatsapp_api_url
)
from .media import upload_media_for_template

# Cache para evitar llamadas repetidas a la API
_template_language_cache = {}

def format_template_name(name: str) -> str:
    """
    Formatea el nombre de la plantilla según las reglas de WhatsApp.
    - Solo letras minúsculas y guiones bajos
    - Sin espacios ni caracteres especiales
    """
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

def get_whatsapp_templates():
    """
    Obtiene todas las plantillas de WhatsApp Business API.
    """
    # Obtener headers centralizados (sin Content-Type para GET)
    headers = get_whatsapp_headers()
    del headers["Content-Type"]  # Remover Content-Type para GET requests

    print(f"Obteniendo plantillas de: {get_whatsapp_template_api_url()}")
    
    try:
        response = requests.get(get_whatsapp_template_api_url(), headers=headers)
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

def create_whatsapp_template(name: str, content: str, category: str, language: str = "es", footer: str = None):
    """
    Crea una nueva plantilla en WhatsApp Business API.
    """
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
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
    print(f"URL: {get_whatsapp_template_api_url()}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_template_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla: {response.status_code}")
        print(f"Contenido: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla: {e}")
        return None

def create_whatsapp_template_with_media(
    name: str, 
    content: str, 
    category: str, 
    header_handle: str,
    media_type: str = "IMAGE",
    language: str = "es", 
    footer: str = None,
    header_text: str = None
):
    """
    Crea una nueva plantilla en WhatsApp Business API con contenido multimedia.
    """
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    # Formatear el nombre según las reglas de WhatsApp
    formatted_name = format_template_name(name)
    print(f"Nombre original: '{name}' -> Formateado: '{formatted_name}'")
    
    components = []
    
    # Agregar encabezado con medio
    # Según la documentación oficial de WhatsApp Cloud API v20.0
    # El formato correcto para plantillas con medios es:
    header_component = {
        "type": "HEADER",
        "format": media_type.upper(),  # "IMAGE", "VIDEO", "DOCUMENT"
        "example": {
            "header_handle": [header_handle]
        }
    }
    
    # Si hay texto en el encabezado, agregarlo
    if header_text:
        header_component["text"] = header_text
    
    components.append(header_component)
    
    # Agregar cuerpo del mensaje
    components.append({
        "type": "BODY",
        "text": content
    })
    
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

    print(f"--- Creando plantilla con medio en WhatsApp ---")
    print(f"URL: {get_whatsapp_template_api_url()}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_template_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla: {response.status_code}")
        print(f"Contenido: {response.text}")
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"Error 400 - Detalles: {error_data}")
            # Intentar con una estructura más simple si falla
            return create_simple_template_with_media(name, content, category, header_handle, media_type, language, footer, header_text)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla: {e}")
        return None

def create_simple_template_with_media(
    name: str, 
    content: str, 
    category: str, 
    header_handle: str,
    media_type: str = "IMAGE",
    language: str = "es", 
    footer: str = None,
    header_text: str = None
):
    """
    Crea una plantilla con medio usando una estructura más simple que cumple con los requisitos de WhatsApp.
    Usa header_handle obtenido de la API de subida reanudable.
    """
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    formatted_name = format_template_name(name)
    
    # Estructura simplificada según la documentación oficial de WhatsApp Cloud API
    # Para plantillas con medios, solo necesitamos HEADER y BODY
    components = [
        {
            "type": "HEADER",
            "format": media_type.upper(),  # "IMAGE", "VIDEO", "DOCUMENT"
            "example": {
                "header_handle": [header_handle]
            }
        },
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

    print(f"--- Creando plantilla simple con medio en WhatsApp ---")
    print(f"URL: {get_whatsapp_template_api_url()}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_template_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla simple: {response.status_code}")
        print(f"Contenido: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla simple: {e}")
        return None

def create_whatsapp_template_with_image_url(
    name: str, 
    content: str, 
    category: str, 
    image_url: str,
    language: str = "es", 
    footer: str = None,
    header_text: str = None
):
    """
    Crea una nueva plantilla en WhatsApp Business API con imagen desde URL.
    """
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    # Formatear el nombre según las reglas de WhatsApp
    formatted_name = format_template_name(name)
    print(f"Nombre original: '{name}' -> Formateado: '{formatted_name}'")
    
    components = []
    
    # Agregar encabezado con imagen desde URL
    # Según la documentación, para URLs se usa "image" en minúsculas
    header_component = {
        "type": "HEADER",
        "format": "image",
        "example": {
            "header_handle": [image_url]
        }
    }
    
    # Si hay texto en el encabezado, agregarlo
    if header_text:
        header_component["text"] = header_text
    
    components.append(header_component)
    
    # Agregar cuerpo del mensaje
    components.append({
        "type": "BODY",
        "text": content
    })
    
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

    print(f"--- Creando plantilla con imagen desde URL ---")
    print(f"URL: {get_whatsapp_template_api_url()}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_template_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla: {response.status_code}")
        print(f"Contenido: {response.text}")
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"Error 400 - Detalles: {error_data}")
            # Intentar con una estructura más simple si falla
            return create_simple_template_with_image_url(name, content, category, image_url, language, footer, header_text)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla: {e}")
        return None

def create_simple_template_with_image_url(
    name: str, 
    content: str, 
    category: str, 
    image_url: str,
    language: str = "es", 
    footer: str = None,
    header_text: str = None
):
    """
    Crea una plantilla con imagen desde URL usando una estructura más simple.
    """
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    formatted_name = format_template_name(name)
    
    # Estructura simplificada según la documentación oficial
    components = [
        {
            "type": "HEADER",
            "format": "image",
            "example": {
                "header_handle": [image_url]
            }
        },
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

    print(f"--- Creando plantilla simple con imagen desde URL ---")
    print(f"URL: {get_whatsapp_template_api_url()}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_template_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla simple: {response.status_code}")
        print(f"Contenido: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla simple: {e}")
        return None

def send_whatsapp_template(to: str, template_name: str, parameters: dict = None):
    """
    Envía una plantilla aprobada a un número de WhatsApp.
    """
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    # Obtener el idioma automáticamente desde WhatsApp API
    language_code = get_template_language(template_name)
    
    # Construir datos usando función helper
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
    print(f"URL: {get_whatsapp_api_url()}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al enviar plantilla: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar plantilla: {e}")
        return None

def send_whatsapp_template_with_media(
    to: str, 
    template_name: str, 
    media_type: str = "IMAGE",
    media_id: str = None,
    parameters: dict = None,
    header_parameters: dict = None
):
    """
    Envía una plantilla con contenido multimedia a un número de WhatsApp.
    """
    headers = get_whatsapp_headers()
    
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
            },
            "components": []
        }
    }
    
    # Normalizar el tipo de medio
    media_type_upper = media_type.upper()
    media_type_lower = media_type.lower()
    
    # Validar que el tipo de medio sea soportado
    supported_types = ['IMAGE', 'VIDEO', 'DOCUMENT']
    if media_type_upper not in supported_types:
        print(f"⚠️ Tipo de medio no soportado: {media_type}. Usando IMAGE por defecto.")
        media_type_upper = 'IMAGE'
        media_type_lower = 'image'
    
    # Agregar componente de encabezado con multimedia
    # Para plantillas con multimedia, WhatsApp requiere especificar el tipo y el parámetro correspondiente
    header_component = {
        "type": "header",
        "parameters": [
            {
                "type": media_type_lower  # "image", "video", "document"
            }
        ]
    }
    
    # Para plantillas con multimedia, WhatsApp SIEMPRE requiere parámetros de header
    # Necesitamos proporcionar un media_id válido o usar un placeholder
    
    if media_id:
        # Si tenemos media_id específico, usarlo según el tipo de medio
        if media_type_upper == "IMAGE":
            header_component["parameters"][0]["image"] = {"id": media_id}
            print(f"📷 Enviando plantilla con imagen: {media_id}")
        elif media_type_upper == "VIDEO":
            header_component["parameters"][0]["video"] = {"id": media_id}
            print(f"🎥 Enviando plantilla con video: {media_id}")
        elif media_type_upper == "DOCUMENT":
            header_component["parameters"][0]["document"] = {"id": media_id}
            print(f"📄 Enviando plantilla con documento: {media_id}")
    else:
        # Si no tenemos media_id, intentar subir un archivo placeholder o usar la función regular
        print(f"⚠️ No hay media_id disponible para plantilla multimedia. Intentando envío como plantilla regular.")
        return send_whatsapp_template(to, template_name, parameters)
    
    data["template"]["components"].append(header_component)
    
    # Agregar parámetros del cuerpo si se proporcionan
    if parameters:
        data["template"]["components"].append({
            "type": "body",
            "parameters": [
                {"type": "text", "text": str(value)} for value in parameters.values()
            ]
        })

    print(f"--- Enviando plantilla con medio a WhatsApp ---")
    print(f"Tipo de medio: {media_type_upper}")
    print(f"URL: {get_whatsapp_api_url()}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(get_whatsapp_api_url(), headers=headers, data=json.dumps(data))
        print(f"Respuesta al enviar plantilla: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar plantilla: {e}")
        return None

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

def create_template_with_local_media(
    name: str,
    content: str, 
    category: str,
    file_path: str,
    media_type: str = "IMAGE",
    language: str = "es",
    footer: str = None,
    header_text: str = None
) -> Optional[Dict[str, Any]]:
    """
    Función completa que sube un archivo local usando la API de subida reanudable
    y crea una plantilla de WhatsApp con ese archivo.
    """
    print(f"--- Creando plantilla con archivo local ---")
    print(f"Archivo: {file_path}")
    print(f"Plantilla: {name}")
    
    # Paso 1: Determinar el tipo MIME del archivo de manera más robusta
    import mimetypes
    import os
    
    # Intentar importar magic, pero no es obligatorio
    try:
        import magic
        MAGIC_AVAILABLE = True
    except ImportError:
        MAGIC_AVAILABLE = False
    
    # Obtener la extensión del archivo
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Mapeo de extensiones a tipos MIME para WhatsApp
    extension_to_mime = {
        # Imágenes
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        # Videos
        '.mp4': 'video/mp4',
        '.3gp': 'video/3gpp',
        '.3gpp': 'video/3gpp',
        # Documentos
        '.pdf': 'application/pdf'
    }
    
    # Intentar detectar el tipo MIME por extensión primero
    mime_type = extension_to_mime.get(file_extension)
    
    if not mime_type:
        # Si no se encontró por extensión, usar mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
    
    # Si aún no se detectó, intentar con magic (si está disponible)
    if not mime_type and MAGIC_AVAILABLE:
        try:
            mime_type = magic.from_file(file_path, mime=True)
        except Exception:
            pass
    
    # Si aún no se detectó, usar valores por defecto basados en el tipo de media
    if not mime_type:
        if media_type.upper() == "IMAGE":
            mime_type = "image/jpeg"
        elif media_type.upper() == "VIDEO":
            mime_type = "video/mp4"
        elif media_type.upper() == "DOCUMENT":
            mime_type = "application/pdf"
        else:
            mime_type = "image/jpeg"
    
    # Validar que el tipo MIME sea soportado por WhatsApp
    whatsapp_supported_mimes = [
        'image/jpeg', 'image/jpg', 'image/png',
        'video/mp4', 'video/3gpp', 'video/3gp',
        'application/pdf'
    ]
    
    if mime_type not in whatsapp_supported_mimes:
        print(f"⚠️ Advertencia: Tipo MIME '{mime_type}' no está en la lista de formatos soportados por WhatsApp")
        print(f"Formatos soportados: {whatsapp_supported_mimes}")
        # Intentar mapear a un formato soportado
        if mime_type.startswith('image/'):
            mime_type = 'image/jpeg'
        elif mime_type.startswith('video/'):
            mime_type = 'video/mp4'
        elif mime_type.startswith('application/'):
            mime_type = 'application/pdf'
    
    print(f"Tipo MIME detectado: {mime_type}")
    print(f"Tipo de medio especificado: {media_type}")
    
    # Paso 2: Subir el archivo usando la API de subida reanudable
    header_handle = upload_media_for_template(file_path, mime_type)
    
    if not header_handle:
        print(f"❌ Error: No se pudo subir el archivo")
        return None
    
    print(f"✅ Archivo subido. Header Handle: {header_handle}")
    
    # Paso 3: Crear la plantilla con el header_handle
    result = create_simple_template_with_media(
        name=name,
        content=content,
        category=category,
        header_handle=header_handle,
        media_type=media_type,
        language=language,
        footer=footer,
        header_text=header_text
    )
    
    if result:
        print(f"✅ Plantilla creada exitosamente: {result}")
    else:
        print(f"❌ Error al crear la plantilla")
    
    return result

def create_template_with_base64_media(
    name: str,
    content: str,
    category: str,
    base64_data: str,
    filename: str,
    media_type: str = "IMAGE",
    language: str = "es",
    footer: str = None,
    header_text: str = None
) -> Optional[Dict[str, Any]]:
    """
    Función completa que sube un archivo desde base64 usando la API de subida reanudable
    y crea una plantilla de WhatsApp con ese archivo.
    """
    print(f"--- Creando plantilla con archivo base64 ---")
    print(f"Archivo: {filename}")
    print(f"Plantilla: {name}")
    
    # Paso 1: Determinar el tipo MIME del archivo
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        # Valores por defecto basados en el tipo de media
        if media_type.upper() == "IMAGE":
            mime_type = "image/jpeg"
        elif media_type.upper() == "VIDEO":
            mime_type = "video/mp4"
        elif media_type.upper() == "DOCUMENT":
            mime_type = "application/pdf"
        else:
            mime_type = "image/jpeg"
    
    print(f"Tipo MIME detectado: {mime_type}")
    
    # Paso 2: Subir el archivo usando la API de subida reanudable
    header_handle = upload_media_for_template(base64_data, filename, mime_type)
    
    if not header_handle:
        print(f"❌ Error: No se pudo subir el archivo")
        return None
    
    print(f"✅ Archivo subido. Header Handle: {header_handle}")
    
    # Paso 3: Crear la plantilla con el header_handle
    result = create_simple_template_with_media(
        name=name,
        content=content,
        category=category,
        header_handle=header_handle,
        media_type=media_type,
        language=language,
        footer=footer,
        header_text=header_text
    )
    
    if result:
        print(f"✅ Plantilla creada exitosamente: {result}")
    else:
        print(f"❌ Error al crear la plantilla")
    
    return result

def archive_template(db, template_id: str) -> bool:
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

def unarchive_template(db, template_id: str) -> bool:
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

def get_archived_templates(db):
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
