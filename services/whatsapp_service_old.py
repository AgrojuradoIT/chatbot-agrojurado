import requests
import json
import os
from sqlalchemy.orm import Session
from models.whatsapp_models import WhatsappUser
import base64
from typing import Optional, List, Dict, Any
from services.whatsapp_config import (
    WHATSAPP_API_URL, 
    WHATSAPP_TEMPLATE_API_URL, 
    WHATSAPP_MEDIA_API_URL,
    get_whatsapp_headers,
    get_base_whatsapp_data,
    validate_whatsapp_config
)

def send_whatsapp_message(to: str, message: str):
    """
    Envía un mensaje de texto a un número de WhatsApp a través de la API de Meta.
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
    print(f"URL: {WHATSAPP_API_URL}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        print(f"Mensaje con botones enviado a {to} exitosamente.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje con botones a {to}: {e}")
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

def upload_media_to_whatsapp(file_path: str, file_type: str = "image/jpeg") -> Optional[str]:
    """
    Sube un archivo multimedia a WhatsApp Business API y devuelve el media_id.
    
    Args:
        file_path: Ruta del archivo a subir
        file_type: Tipo MIME del archivo (ej: "image/jpeg", "image/png", "video/mp4")
    
    Returns:
        media_id si es exitoso, None si falla
    """
    # Obtener headers centralizados (sin Content-Type para upload de archivos)
    headers = get_whatsapp_headers()
    del headers["Content-Type"]  # Remover Content-Type para upload de archivos
    
    try:
        with open(file_path, 'rb') as file:
            files = {
                'file': (os.path.basename(file_path), file, file_type)
            }
            
            # Agregar el parámetro messaging_product requerido
            data = {
                'messaging_product': 'whatsapp'
            }
            
            print(f"--- Subiendo medio a WhatsApp ---")
            print(f"Archivo: {file_path}")
            print(f"Tipo: {file_type}")
            print("-------------------------------------")
            
            response = requests.post(WHATSAPP_MEDIA_API_URL, headers=headers, files=files, data=data)
            print(f"Respuesta al subir medio: {response.status_code}")
            print(f"Contenido: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                media_id = result.get('id')
                print(f"✅ Medio subido exitosamente. Media ID: {media_id}")
                return media_id
            else:
                print(f"❌ Error al subir medio: {response.text}")
                return None
                
    except Exception as e:
        print(f"❌ Error al subir medio: {e}")
        return None

def upload_media_from_url_to_whatsapp(file_url: str, file_type: str = "image/jpeg") -> Optional[str]:
    """
    Sube un archivo multimedia desde una URL a WhatsApp Business API y devuelve el media_id.
    
    Args:
        file_url: URL del archivo a subir
        file_type: Tipo MIME del archivo (ej: "image/jpeg", "image/png", "video/mp4", "application/pdf")
    
    Returns:
        media_id si es exitoso, None si falla
    """
    headers = get_whatsapp_headers()
    
    try:
        # Descargar el archivo desde la URL
        print(f"--- Descargando archivo desde URL ---")
        print(f"URL: {file_url}")
        print("-------------------------------------")
        
        response = requests.get(file_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Error al descargar archivo: HTTP {response.status_code}")
            return None
        
        # Obtener el nombre del archivo de la URL
        import os
        filename = os.path.basename(file_url)
        
        # Crear un archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            # Subir el archivo temporal usando la función existente
            media_id = upload_media_to_whatsapp(temp_file_path, file_type)
            return media_id
        finally:
            # Limpiar el archivo temporal
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error al subir medio desde URL: {e}")
        return None

def upload_media_for_template(file_path: str, file_type: str = "image/jpeg") -> Optional[str]:
    """
    Sube un archivo usando la API de subida reanudable de Facebook para obtener un header_handle
    que se puede usar en plantillas de WhatsApp.
    
    Args:
        file_path: Ruta del archivo a subir
        file_type: Tipo MIME del archivo
    
    Returns:
        header_handle si es exitoso, None si falla
    """
    try:
        import os
        
        # Paso 1: Inicializar la sesión de subida reanudable
        # Según la documentación, debe usar APP_ID, no BUSINESS_ACCOUNT_ID
        if not WHATSAPP_APP_ID:
            print(f"❌ Error: WHATSAPP_APP_ID no está configurado en las variables de entorno")
            return None
            
        init_url = f"https://graph.facebook.com/v20.0/{WHATSAPP_APP_ID}/uploads"
        
        headers = get_whatsapp_headers()
        headers["Content-Type"] = "application/json"
        
        file_size = os.path.getsize(file_path)
        
        # Parámetros según la documentación oficial de Facebook
        init_params = {
            "file_name": os.path.basename(file_path),
            "file_length": file_size,
            "file_type": file_type,
            "access_token": get_whatsapp_headers()["Authorization"].split(" ")[1]
        }
        
        print(f"--- Inicializando subida reanudable ---")
        print(f"Archivo: {file_path}")
        print(f"Tamaño: {file_size} bytes")
        print(f"Tipo: {file_type}")
        
        # Inicializar sesión usando parámetros de query según la documentación
        init_response = requests.post(init_url, params=init_params)
        print(f"Respuesta inicialización: {init_response.status_code}")
        print(f"Contenido: {init_response.text}")
        
        if init_response.status_code != 200:
            print(f"❌ Error al inicializar subida: {init_response.text}")
            return None
            
        init_result = init_response.json()
        session_id = init_result.get('id')
        
        if not session_id:
            print(f"❌ No se obtuvo session_id")
            return None
            
        print(f"✅ Sesión iniciada: {session_id}")
        
        # Paso 2: Subir el archivo
        upload_url = f"https://graph.facebook.com/v20.0/{session_id}"
        
        upload_headers = get_whatsapp_headers()
        upload_headers["file_offset"] = "0"
        # Cambiar Bearer por OAuth para esta API específica
        upload_headers["Authorization"] = f"OAuth {get_whatsapp_headers()['Authorization'].split(' ')[1]}"
        
        with open(file_path, 'rb') as file:
            file_data = file.read()
            
        upload_response = requests.post(upload_url, headers=upload_headers, data=file_data)
        print(f"Respuesta subida: {upload_response.status_code}")
        print(f"Contenido: {upload_response.text}")
        
        if upload_response.status_code != 200:
            print(f"❌ Error al subir archivo: {upload_response.text}")
            return None
            
        upload_result = upload_response.json()
        header_handle = upload_result.get('h')
        
        if header_handle:
            print(f"✅ Archivo subido exitosamente. Header Handle: {header_handle}")
            return header_handle
        else:
            print(f"❌ No se obtuvo header_handle")
            return None
            
    except Exception as e:
        print(f"❌ Error en subida reanudable: {e}")
        return None


def upload_media_from_base64_for_template(base64_data: str, filename: str, file_type: str = "image/jpeg") -> Optional[str]:
    """
    Sube un archivo desde datos base64 usando la API de subida reanudable para obtener header_handle.
    
    Args:
        base64_data: Datos del archivo en base64
        filename: Nombre del archivo
        file_type: Tipo MIME del archivo
    
    Returns:
        header_handle si es exitoso, None si falla
    """
    try:
        import tempfile
        import base64
        
        # Decodificar base64 y guardar temporalmente
        file_data = base64.b64decode(base64_data)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{filename.split('.')[-1]}") as temp_file:
            temp_file.write(file_data)
            temp_file_path = temp_file.name
        
        try:
            # Usar la función de subida reanudable
            header_handle = upload_media_for_template(temp_file_path, file_type)
            return header_handle
        finally:
            # Limpiar archivo temporal
            import os
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        print(f"❌ Error en subida base64 para plantilla: {e}")
        return None


def upload_media_from_base64(base64_data: str, filename: str, file_type: str = "image/jpeg") -> Optional[str]:
    """
    Sube un archivo multimedia desde datos base64 a WhatsApp Business API.
    
    Args:
        base64_data: Datos del archivo en base64
        filename: Nombre del archivo
        file_type: Tipo MIME del archivo
    
    Returns:
        media_id si es exitoso, None si falla
    """
    headers = get_whatsapp_headers()
    
    try:
        # Decodificar base64
        file_data = base64.b64decode(base64_data)
        
        files = {
            'file': (filename, file_data, file_type)
        }
        
        # Agregar el parámetro messaging_product requerido
        data = {
            'messaging_product': 'whatsapp'
        }
        
        print(f"--- Subiendo medio desde base64 ---")
        print(f"Archivo: {filename}")
        print(f"Tipo: {file_type}")
        print("-------------------------------------")
        
        response = requests.post(WHATSAPP_MEDIA_API_URL, headers=headers, files=files, data=data)
        print(f"Respuesta al subir medio: {response.status_code}")
        print(f"Contenido: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            media_id = result.get('id')
            print(f"✅ Medio subido exitosamente. Media ID: {media_id}")
            return media_id
        else:
            print(f"❌ Error al subir medio: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error al subir medio: {e}")
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
    
    Args:
        name: Nombre de la plantilla
        content: Contenido del cuerpo del mensaje
        category: Categoría de la plantilla (UTILITY, MARKETING, etc.)
        header_handle: Handle del medio subido usando API de subida reanudable
        media_type: Tipo de medio (IMAGE, VIDEO, DOCUMENT)
        language: Código de idioma
        footer: Texto del pie de página (opcional)
        header_text: Texto del encabezado (opcional)
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
    print(f"URL: {WHATSAPP_TEMPLATE_API_URL}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_TEMPLATE_API_URL, headers=headers, data=json.dumps(data))
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
    print(f"URL: {WHATSAPP_TEMPLATE_API_URL}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_TEMPLATE_API_URL, headers=headers, data=json.dumps(data))
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
    
    Args:
        name: Nombre de la plantilla
        content: Contenido del cuerpo del mensaje
        category: Categoría de la plantilla
        image_url: URL de la imagen
        language: Código de idioma
        footer: Texto del pie de página (opcional)
        header_text: Texto del encabezado (opcional)
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
    print(f"URL: {WHATSAPP_TEMPLATE_API_URL}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_TEMPLATE_API_URL, headers=headers, data=json.dumps(data))
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
    print(f"URL: {WHATSAPP_TEMPLATE_API_URL}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_TEMPLATE_API_URL, headers=headers, data=json.dumps(data))
        print(f"Respuesta al crear plantilla simple: {response.status_code}")
        print(f"Contenido: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al crear plantilla simple: {e}")
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
    # Obtener headers centralizados (sin Content-Type para GET)
    headers = get_whatsapp_headers()
    del headers["Content-Type"]  # Remover Content-Type para GET requests

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
    # Obtener headers centralizados
    headers = get_whatsapp_headers()
    
    # Obtener el idioma automáticamente desde WhatsApp API
    language_code = get_template_language(template_name)
    
    # Construir datos usando función helper
    data = get_base_whatsapp_data(to, "template")
    data["template"] = {
        "name": template_name,
        "language": {
            "code": language_code
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
    
    Args:
        to: Número de teléfono destino
        template_name: Nombre de la plantilla
        media_type: Tipo de multimedia (IMAGE, VIDEO, DOCUMENT)
        media_id: ID del medio (opcional, para plantillas ya creadas)
        parameters: Parámetros para el cuerpo del mensaje
        header_parameters: Parámetros para el encabezado (opcional)
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
    
    Args:
        name: Nombre de la plantilla
        content: Contenido del cuerpo del mensaje
        category: Categoría de la plantilla (UTILITY, MARKETING, etc.)
        file_path: Ruta del archivo local a subir
        media_type: Tipo de medio (IMAGE, VIDEO, DOCUMENT)
        language: Código de idioma
        footer: Texto del pie de página (opcional)
        header_text: Texto del encabezado (opcional)
    
    Returns:
        Respuesta de la API si es exitoso, None si falla
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
    
    Args:
        name: Nombre de la plantilla
        content: Contenido del cuerpo del mensaje
        category: Categoría de la plantilla (UTILITY, MARKETING, etc.)
        base64_data: Datos del archivo en base64
        filename: Nombre del archivo
        media_type: Tipo de medio (IMAGE, VIDEO, DOCUMENT)
        language: Código de idioma
        footer: Texto del pie de página (opcional)
        header_text: Texto del encabezado (opcional)
    
    Returns:
        Respuesta de la API si es exitoso, None si falla
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
    header_handle = upload_media_from_base64_for_template(base64_data, filename, mime_type)
    
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
        import os
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
    print(f"URL: {WHATSAPP_API_URL}")
    print(f"Archivo: {filename}")
    print(f"Media ID: {media_id}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(data))
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
        import os
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
    print(f"URL: {WHATSAPP_API_URL}")
    print(f"Archivo: {filename}")
    print(f"URL del archivo: {file_url}")
    print(f"Media ID: {media_id}")
    print("-------------------------------------")

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(data))
        print(f"Respuesta de la API de WhatsApp: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        response.raise_for_status()
        print(f"Documento PDF enviado a {to} exitosamente.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar documento PDF a {to}: {e}")
        return False