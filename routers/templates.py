from fastapi import APIRouter, HTTPException, Depends, Query, Form, File, UploadFile
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import json
import logging

logger = logging.getLogger(__name__)

from database import get_db
from models.template_models import TemplateRequest, TemplateResponse, SendTemplateRequest, TemplateMediaRequest
from models.whatsapp_models import SendTemplateWithMediaRequest
from middleware.auth import get_current_user
from middleware.permissions import require_permission, require_any_permission
from services.whatsapp_service import (
    get_whatsapp_templates, 
    create_whatsapp_template, 
    send_whatsapp_template, 
    delete_whatsapp_template,
    upload_media_to_whatsapp,
    create_template_with_local_media,
    create_template_with_base64_media
)
from typing import List
import base64

router = APIRouter(prefix="/api/templates", tags=["templates"])

@router.get("/")
async def get_templates(
    db: Session = Depends(get_db), 
    current_user: dict = Depends(require_permission("chatbot.templates.use"))
):
    """Obtiene las plantillas de WhatsApp Business API (solo las no archivadas)"""
    try:
        from services.whatsapp_service import get_archived_templates as get_archived_templates_service
        
        # Obtener plantillas archivadas de la base de datos local
        archived_templates = get_archived_templates_service(db)
        archived_ids = {template.id for template in archived_templates}
        
        templates_data = get_whatsapp_templates()
        
        # Plantillas de fallback si no hay datos
        if not templates_data or not templates_data.get('data'):
            print("[templates.py] No se encontraron plantillas en WhatsApp Business API, usando plantillas de ejemplo")
            return {
                "data": [
                    {
                        "id": "example_template_1",
                        "name": "saludo_inicial",
                        "status": "APPROVED",
                        "category": "UTILITY",
                        "language": "es",
                        "components": [
                            {
                                "type": "BODY",
                                "text": "¡Hola! Gracias por contactarnos. ¿En qué podemos ayudarte hoy?"
                            }
                        ]
                    }
                ]
            }
        
        # Convertir plantillas de WhatsApp al formato del frontend
        whatsapp_templates = templates_data.get('data', [])
        templates = []
        
        for template in whatsapp_templates:
            # Filtrar plantillas archivadas
            if template.get("id") not in archived_ids:
                components = template.get("components", [])
                
                # Extraer información de multimedia del header
                header_component = next((c for c in components if c.get("type") == "HEADER"), None)
                media_info = {}
                
                if header_component:
                    format_type = header_component.get("format", "")
                    if format_type in ["IMAGE", "VIDEO", "DOCUMENT"]:
                        media_info = {
                            "has_media": True,
                            "media_type": format_type,
                            "header_text": header_component.get("text", "")
                        }
                        # Si tiene ejemplo con header_handle, incluirlo
                        example = header_component.get("example", {})
                        if "header_handle" in example:
                            media_info["header_handle"] = example["header_handle"]
                    else:
                        media_info = {"has_media": False}
                else:
                    media_info = {"has_media": False}
                
                # Extraer contenido del body y footer
                body_component = next((c for c in components if c.get("type") == "BODY"), None)
                footer_component = next((c for c in components if c.get("type") == "FOOTER"), None)
                
                template_obj = {
                    "id": template.get("id"),
                    "name": template.get("name"),
                    "category": template.get("category"),
                    "language": template.get("language"),
                    "status": template.get("status"),
                    "is_archived": False,
                    "components": components,
                    "content": body_component.get("text", "") if body_component else "",
                    "footer": footer_component.get("text", "") if footer_component else "",
                    "header_text": header_component.get("text", "") if header_component else "",
                    **media_info  # Incluir información de multimedia
                }
                templates.append(template_obj)
        
        return {"templates": templates}
        
    except Exception as e:
        print(f"Error al obtener plantillas: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener plantillas")

@router.post("/")
async def create_template(
    template: TemplateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.templates.create"))
):
    """Crea una nueva plantilla de WhatsApp"""
    try:
        result = create_whatsapp_template(
            name=template.name,
            content=template.content,
            category=template.category,
            footer=template.footer
        )
        
        if result and result.get('id'):
            return {"message": "Plantilla creada exitosamente", "template_id": result['id']}
        else:
            raise HTTPException(status_code=400, detail="Error creando plantilla")
            
    except Exception as e:
        print(f"Error al crear plantilla: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear plantilla: {e}")

@router.post("/send")
async def send_template_to_contacts(
    request: SendTemplateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.messages.send.massive"))
):
    """Envía una plantilla a múltiples contactos"""
    try:
        from models.whatsapp_models import Message
        from datetime import datetime
        from utils.websocket_manager import manager
        
        results = []
        success_count = 0
        
        for phone_number in request.phone_numbers:
            try:
                result = send_whatsapp_template(
                    to=phone_number,
                    template_name=request.template_name,
                    parameters=request.parameters
                )
                
                if result:
                    # Crear contenido de la plantilla para guardar
                    template_content = f"Plantilla enviada: {request.template_name}"
                    if request.parameters:
                        template_content += f" con parámetros: {request.parameters}"
                    
                    # Guardar mensaje del bot
                    bot_message_obj = Message(
                        id=f"bot_template_{phone_number}_{int(datetime.utcnow().timestamp())}",
                        phone_number=phone_number,
                        sender='bot',
                        content=template_content,
                        status='sent'
                    )
                    db.add(bot_message_obj)
                    db.commit()
                    
                    # Notificar a clientes conectados
                    template_message_data = {
                        "type": "new_message",
                        "message": {
                            "id": bot_message_obj.id,
                            "text": bot_message_obj.content,
                            "sender": "bot",
                            "timestamp": bot_message_obj.timestamp.isoformat(),
                            "phone_number": phone_number,
                            "status": bot_message_obj.status
                        }
                    }
                    
                    await manager.send_message_to_phone(phone_number, template_message_data)
                    await manager.send_message_to_all(template_message_data)
                    
                    results.append({
                        "phone_number": phone_number,
                        "success": True,
                        "message_id": result.get('messages', [{}])[0].get('id') if result else None
                    })
                    success_count += 1
                else:
                    results.append({
                        "phone_number": phone_number,
                        "success": False,
                        "error": "Error al enviar plantilla"
                    })
                    
            except Exception as e:
                print(f"Error enviando plantilla a {phone_number}: {e}")
                results.append({
                    "phone_number": phone_number,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "template_name": request.template_name,
            "total_contacts": len(request.phone_numbers),
            "success_count": success_count,
            "results": results
        }
        
    except Exception as e:
        print(f"Error enviando plantilla: {e}")
        raise HTTPException(status_code=500, detail=f"Error enviando plantilla: {e}")

@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.templates.delete"))
):
    """Elimina una plantilla de WhatsApp"""
    try:
        result = delete_whatsapp_template(template_id)
        
        if result:
            return {"message": "Plantilla eliminada exitosamente"}
        else:
            raise HTTPException(status_code=400, detail="Error eliminando plantilla")
            
    except Exception as e:
        print(f"Error al eliminar plantilla: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar plantilla: {e}")

@router.post("/{template_id}/archive")
async def archive_template(
    template_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.templates.delete"))
):
    """Archiva una plantilla en lugar de eliminarla"""
    try:
        from services.whatsapp_service import archive_template as archive_template_service
        
        success = archive_template_service(db, template_id)
        if success:
            return {"message": "Template archived successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to archive template")
    except Exception as e:
        print(f"Error archiving template: {e}")
        raise HTTPException(status_code=500, detail=f"Error archiving template: {e}")


@router.post("/{template_id}/unarchive")
async def unarchive_template(
    template_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.templates.delete"))
):
    """Desarchiva una plantilla"""
    try:
        from services.whatsapp_service import unarchive_template as unarchive_template_service
        
        success = unarchive_template_service(db, template_id)
        if success:
            return {"message": "Template unarchived successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to unarchive template")
    except Exception as e:
        print(f"Error unarchiving template: {e}")
        raise HTTPException(status_code=500, detail=f"Error unarchiving template: {e}")


@router.get("/archived")
async def get_archived_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.templates.use"))
):
    """Obtiene todas las plantillas archivadas"""
    try:
        from services.whatsapp_service import get_archived_templates as get_archived_templates_service
        
        # Obtener plantillas archivadas de la base de datos local
        archived_templates = get_archived_templates_service(db)
        
        # Convertir a formato JSON
        templates_data = []
        for template in archived_templates:
            templates_data.append({
                "id": template.id,
                "name": template.name,
                "content": template.content,
                "category": template.category,
                "status": template.status,
                "rejected_reason": template.rejected_reason,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "footer": template.footer,
                "is_archived": template.is_archived
            })
        
        return {"templates": templates_data}
        
    except Exception as e:
        print(f"Error getting archived templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting archived templates: {e}")


@router.post("/send-with-media")
async def send_template_with_media_to_contacts(
    request: SendTemplateWithMediaRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.send.massive"))
):
    """Envía una plantilla con contenido multimedia a múltiples contactos"""
    try:
        from services.whatsapp_service import send_whatsapp_template_with_media, send_whatsapp_template, upload_media_to_whatsapp
        from models.whatsapp_models import Message
        from datetime import datetime
        from utils.websocket_manager import manager
        
        template_name = request.template_name
        phone_numbers = request.phone_numbers
        media_id = request.media_id
        parameters = request.parameters or {}
        header_parameters = request.header_parameters or {}
        
        results = []
        success_count = 0
        
        # Obtener información de la plantilla para determinar el tipo de multimedia y media_id
        templates_info = get_whatsapp_templates()
        template_info = None
        media_type = "IMAGE"  # Default
        template_media_id = None
        
        print(f"🔍 Buscando plantilla: {template_name}")
        
        if templates_info and 'data' in templates_info:
            for template in templates_info['data']:
                if template['name'] == template_name:
                    template_info = template
                    print(f"✅ Plantilla encontrada: {template_name}")
                    print(f"📋 Componentes de la plantilla: {template.get('components', [])}")
                    
                    # Buscar componente de header para determinar el tipo y obtener media_id
                    for component in template.get('components', []):
                        if component.get('type') == 'HEADER':
                            format_type = component.get('format', '').upper()
                            print(f"🎯 Componente HEADER encontrado con formato: {format_type}")
                            
                            if format_type in ['IMAGE', 'VIDEO', 'DOCUMENT']:
                                media_type = format_type
                                print(f"🎨 Tipo de medio detectado: {media_type}")
                                
                                # Intentar extraer media_id del ejemplo
                                example = component.get('example', {})
                                print(f"📝 Ejemplo del componente: {example}")
                                
                                if 'header_handle' in example and example['header_handle']:
                                    # El header_handle puede contener el media_id o URL
                                    handle_data = example['header_handle']
                                    print(f"🔗 Header handle encontrado: {handle_data}")
                                    
                                    if isinstance(handle_data, list) and len(handle_data) > 0:
                                        # Si es una URL, intentar extraer ID o usar como media_id
                                        template_media_id = handle_data[0]
                                        print(f"📎 Media ID extraído de lista: {template_media_id}")
                                    elif isinstance(handle_data, str):
                                        template_media_id = handle_data
                                        print(f"📎 Media ID extraído de string: {template_media_id}")
                            else:
                                print(f"⚠️ Formato no reconocido: {format_type}")
                    break
        else:
            print(f"❌ No se pudieron obtener las plantillas de WhatsApp")
        
        print(f"🎯 Tipo de medio final: {media_type}")
        print(f"📎 Media ID de la plantilla: {template_media_id}")
        
        # Si no tenemos media_id específico, usar el de la plantilla
        if not media_id and template_media_id:
            media_id = template_media_id
            print(f"📎 Usando media_id de la plantilla: {media_id}")
        
        for phone_number in phone_numbers:
            try:
                # Para plantillas multimedia, necesitamos obtener un media_id válido
                if media_id and media_id.startswith('http'):
                    # Si tenemos una URL, intentar subir el archivo para obtener media_id
                    print(f" Subiendo archivo desde URL para obtener media_id válido...")
                    print(f" Tipo de medio detectado: {media_type}")
                    try:
                        import requests
                        import tempfile
                        import os
                        import mimetypes
                        
                        # Descargar el archivo temporalmente
                        response = requests.get(media_id, timeout=10)
                        if response.status_code == 200:
                            # Determinar la extensión correcta basada en el tipo de medio y la URL
                            file_extension = '.png'  # Por defecto
                            mime_type = 'image/png'  # Por defecto
                            
                            # Primero intentar detectar desde la URL
                            url_lower = media_id.lower()
                            if '.pdf' in url_lower:
                                file_extension = '.pdf'
                                mime_type = 'application/pdf'
                            elif '.mp4' in url_lower:
                                file_extension = '.mp4'
                                mime_type = 'video/mp4'
                            elif '.3gp' in url_lower or '.3gpp' in url_lower:
                                file_extension = '.3gp'
                                mime_type = 'video/3gpp'
                            elif '.jpg' in url_lower or '.jpeg' in url_lower:
                                file_extension = '.jpg'
                                mime_type = 'image/jpeg'
                            elif '.png' in url_lower:
                                file_extension = '.png'
                                mime_type = 'image/png'
                            else:
                                # Si no se puede detectar desde la URL, usar el media_type detectado
                                if media_type == 'VIDEO':
                                    file_extension = '.mp4'
                                    mime_type = 'video/mp4'
                                elif media_type == 'DOCUMENT':
                                    file_extension = '.pdf'
                                    mime_type = 'application/pdf'
                                elif media_type == 'IMAGE':
                                    file_extension = '.png'
                                    mime_type = 'image/png'
                            
                            print(f" Usando extensión: {file_extension}, MIME type: {mime_type}")
                            
                            # Crear archivo temporal con la extensión correcta
                            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                                temp_file.write(response.content)
                                temp_path = temp_file.name
                            
                            # Subir a WhatsApp para obtener media_id
                            whatsapp_media_id = upload_media_to_whatsapp(temp_path, mime_type)
                            
                            # Limpiar archivo temporal
                            os.unlink(temp_path)
                            
                            if whatsapp_media_id:
                                print(f" Media_id obtenido: {whatsapp_media_id} (tipo: {media_type})")
                                media_id = whatsapp_media_id
                            else:
                                print(f" Error al subir archivo, usando plantilla regular")
                                media_id = None
                        else:
                            print(f" Error al descargar archivo: {response.status_code}")
                            media_id = None
                    except Exception as e:
                        print(f" Error procesando archivo: {e}")
                        media_id = None
                
                # Ahora enviar con el media_id correcto o como plantilla regular
                if media_id and not media_id.startswith('http'):
                    # Si tenemos un media_id válido, usar función multimedia
                    success = send_whatsapp_template_with_media(
                        to=phone_number,
                        template_name=template_name,
                        media_type=media_type,
                        media_id=media_id,
                        parameters=parameters,
                        header_parameters=header_parameters
                    )
                else:
                    # Como último recurso, usar función regular
                    print(f" Enviando plantilla '{template_name}' como plantilla regular")
                    success = send_whatsapp_template(
                        to=phone_number,
                        template_name=template_name,
                        parameters=parameters
                    )
                
                if success:
                    # Crear contenido de la plantilla para guardar
                    template_content = f"Plantilla con medio enviada: {template_name}"
                    if parameters:
                        template_content += f" con parámetros: {parameters}"
                    
                    # Guardar mensaje del bot
                    bot_message_obj = Message(
                        id=f"bot_template_media_{phone_number}_{int(datetime.utcnow().timestamp())}",
                        phone_number=phone_number,
                        sender='bot',
                        content=template_content,
                        status='sent'
                    )
                    db.add(bot_message_obj)
                    db.commit()
                    
                    # Notificar a clientes conectados
                    template_message_data = {
                        "type": "new_message",
                        "message": {
                            "id": bot_message_obj.id,
                            "text": bot_message_obj.content,
                            "sender": "bot",
                            "timestamp": bot_message_obj.timestamp.isoformat(),
                            "phone_number": phone_number,
                            "status": bot_message_obj.status
                        }
                    }
                    
                    await manager.send_message_to_phone(phone_number, template_message_data)
                    await manager.send_message_to_all(template_message_data)
                    
                    results.append({
                        "phone_number": phone_number,
                        "success": True,
                        "message": "Plantilla con medio enviada exitosamente"
                    })
                    success_count += 1
                else:
                    results.append({
                        "phone_number": phone_number,
                        "success": False,
                        "message": "Error al enviar plantilla con medio"
                    })
                    
            except Exception as e:
                print(f"Error enviando plantilla con medio a {phone_number}: {e}")
                results.append({
                    "phone_number": phone_number,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
        
        return {
            "template_name": template_name,
            "media_id": media_id,
            "total_contacts": len(phone_numbers),
            "success_count": success_count,
            "results": results
        }
        
    except Exception as e:
        print(f"Error sending template with media: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending template with media: {e}")


@router.post("/create-with-file")
async def create_template_with_file(
    name: str = Form(...),
    content: str = Form(...),
    category: str = Form(...),
    media_type: str = Form("IMAGE"),
    language: str = Form("es"),
    footer: str = Form(None),
    header_text: str = Form(None),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.templates.create"))
):
    """
    Crea una nueva plantilla de WhatsApp con archivo multimedia subido.
    Usa la API de subida reanudable para obtener header_handle.
    """
    # Log template creation attempt
    logger.info(f"Creating template '{name}' with media file: {file.filename}")
    logger.debug(f"User: {current_user.get('email', 'Unknown')}, Category: {category}, Media Type: {media_type}")
    
    try:
        # Validar el tipo de archivo
        import mimetypes
        
        # Obtener la extensión del archivo
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        # Mapeo de extensiones a tipos MIME para WhatsApp
        extension_to_mime = {
            # Imágenes
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            # Videos
            'mp4': 'video/mp4',
            '3gp': 'video/3gpp',
            '3gpp': 'video/3gpp',
            # Documentos
            'pdf': 'application/pdf'
        }
        
        # Detectar el tipo MIME del archivo
        detected_mime = extension_to_mime.get(file_extension)
        if not detected_mime:
            detected_mime = file.content_type
        
        # Validar que el tipo MIME sea soportado por WhatsApp
        whatsapp_supported_mimes = [
            'image/jpeg', 'image/jpg', 'image/png',
            'video/mp4', 'video/3gpp', 'video/3gp',
            'application/pdf'
        ]
        
        if detected_mime not in whatsapp_supported_mimes:
            raise HTTPException(
                status_code=400, 
                detail=f"Formato de archivo no soportado: {detected_mime}. Formatos soportados: JPEG, PNG, MP4, 3GPP, PDF"
            )
        
        # Detectar automáticamente el tipo de medio basado en el archivo
        detected_media_type = "IMAGE"  # Por defecto
        if detected_mime.startswith('image/'):
            detected_media_type = "IMAGE"
        elif detected_mime.startswith('video/'):
            detected_media_type = "VIDEO"
        elif detected_mime.startswith('application/'):
            detected_media_type = "DOCUMENT"
        
        # Si el usuario especificó un tipo diferente, validar que sea compatible
        if media_type.upper() != detected_media_type:
            logger.warning(f"Tipo de medio especificado ({media_type}) no coincide con el detectado ({detected_media_type})")
            # Usar el tipo detectado automáticamente
            media_type = detected_media_type
        
        logger.info(f"Archivo: {file.filename}, MIME: {detected_mime}, Tipo: {media_type}")
        
        # Guardar archivo temporalmente
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content_bytes = await file.read()
            temp_file.write(content_bytes)
            temp_file_path = temp_file.name
        
        try:
            # Crear plantilla con archivo local usando la nueva función
            result = create_template_with_local_media(
                name=name,
                content=content,
                category=category,
                file_path=temp_file_path,
                media_type=media_type.upper(),
                language=language,
                footer=footer,
                header_text=header_text
            )
            
            if result:
                return {
                    "success": True,
                    "message": "Template with media created successfully",
                    "template": result,
                    "detected_type": media_type,
                    "file_info": {
                        "filename": file.filename,
                        "mime_type": detected_mime,
                        "size": len(content_bytes)
                    }
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to create template with media")
                
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating template with file: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.post("/with-media", status_code=201)
async def create_template_with_media(
    template_request: dict,
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.templates.create"))
):
    """Crea una nueva plantilla con contenido multimedia en WhatsApp Business API"""
    try:
        from services.whatsapp_service import create_whatsapp_template_with_media, create_whatsapp_template_with_image_url
        
        if template_request.get("media_id"):
            # Crear plantilla con medio subido
            result = create_whatsapp_template_with_media(
                name=template_request.get("name"),
                content=template_request.get("content"),
                category=template_request.get("category"),
                media_id=template_request.get("media_id"),
                media_type=template_request.get("media_type", "IMAGE"),
                language=template_request.get("language", "es"),
                footer=template_request.get("footer"),
                header_text=template_request.get("header_text")
            )
        elif template_request.get("image_url"):
            # Crear plantilla con imagen desde URL
            result = create_whatsapp_template_with_image_url(
                name=template_request.get("name"),
                content=template_request.get("content"),
                category=template_request.get("category"),
                image_url=template_request.get("image_url"),
                language=template_request.get("language", "es"),
                footer=template_request.get("footer"),
                header_text=template_request.get("header_text")
            )
        else:
            raise HTTPException(status_code=400, detail="Either media_id or image_url is required")
        
        if result:
            return {"message": "Template with media created successfully", "result": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to create template with media")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating template with media: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating template with media: {e}")
