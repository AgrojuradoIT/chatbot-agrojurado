"""
Módulo de medios de WhatsApp Business API
Contiene funciones para subida y manejo de archivos multimedia
"""

import os
import tempfile
import base64
import requests
from typing import Optional
from .core import (
    get_whatsapp_headers,
    get_whatsapp_media_api_url,
    get_whatsapp_app_id
)

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
            
            response = requests.post(get_whatsapp_media_api_url(), headers=headers, files=files, data=data)
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
        filename = os.path.basename(file_url)
        
        # Crear un archivo temporal
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
        # Paso 1: Inicializar la sesión de subida reanudable
        # Según la documentación, debe usar APP_ID, no BUSINESS_ACCOUNT_ID
        app_id = get_whatsapp_app_id()
        if not app_id:
            print(f"❌ Error: WHATSAPP_APP_ID no está configurado en las variables de entorno")
            return None
            
        init_url = f"https://graph.facebook.com/v20.0/{app_id}/uploads"
        
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
        
        response = requests.post(get_whatsapp_media_api_url(), headers=headers, files=files, data=data)
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
