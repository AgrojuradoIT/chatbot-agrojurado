from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, get_db
from models.whatsapp_models import WhatsappUser, WebhookRequest, Message, Template, TemplateRequest, TemplateResponse, SendTemplateRequest, ContactCreateRequest, ContactUpdateRequest, ContactResponse
from typing import List, Dict, Set
import uuid
from services.whatsapp_service import send_whatsapp_message, create_or_update_whatsapp_user, get_whatsapp_templates, create_whatsapp_template, send_whatsapp_template, delete_whatsapp_template
import os
import json
from datetime import datetime
import asyncio

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WhatsApp Chatbot API",
    description="API para el chatbot de WhatsApp de Agropecuaria Juradó S.A.S",
    version="1.0.0"
)

# Configuración de CORS
origins = [
    "http://localhost:5173",  # Frontend URL
    "http://localhost:8000",  # Backend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
print(f"VERIFY_TOKEN: {VERIFY_TOKEN}")

# =============================================================================
# GESTIÓN DE CONEXIONES WEBSOCKET
# =============================================================================

class ConnectionManager:
    """Gestiona las conexiones WebSocket para comunicación en tiempo real"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.general_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, phone_number: str):
        """Conecta un WebSocket específico para un número de teléfono"""
        await websocket.accept()
        if phone_number not in self.active_connections:
            self.active_connections[phone_number] = set()
        self.active_connections[phone_number].add(websocket)
        print(f"Cliente conectado para {phone_number}. Total conexiones: {len(self.active_connections[phone_number])}")
    
    async def connect_general(self, websocket: WebSocket):
        """Conecta un WebSocket general para todos los contactos"""
        await websocket.accept()
        self.general_connections.add(websocket)
        print(f"Cliente conectado al WebSocket general. Total conexiones: {len(self.general_connections)}")
    
    def disconnect(self, websocket: WebSocket, phone_number: str):
        """Desconecta un WebSocket específico"""
        if phone_number in self.active_connections:
            self.active_connections[phone_number].discard(websocket)
            if not self.active_connections[phone_number]:
                del self.active_connections[phone_number]
        print(f"Cliente desconectado de {phone_number}")
    
    def disconnect_general(self, websocket: WebSocket):
        """Desconecta un WebSocket general"""
        self.general_connections.discard(websocket)
        print(f"Cliente desconectado del WebSocket general")
    
    async def send_message_to_phone(self, phone_number: str, message: dict):
        """Envía mensaje a todas las conexiones de un número específico"""
        if phone_number in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[phone_number]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Limpiar conexiones desconectadas
            for connection in disconnected:
                self.active_connections[phone_number].discard(connection)
            
            if not self.active_connections[phone_number]:
                del self.active_connections[phone_number]
    
    async def send_message_to_all(self, message: dict):
        """Envía mensaje a todas las conexiones generales"""
        disconnected = set()
        for connection in self.general_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        
        # Limpiar conexiones desconectadas
        for connection in disconnected:
            self.general_connections.discard(connection)

manager = ConnectionManager()

# =============================================================================
# FUNCIONES HELPER
# =============================================================================

def get_display_name(user_phone_number: str, user_name: str, db: Session) -> str:
    """Obtiene el nombre de display desde la base de datos o usa el nombre de WhatsApp como fallback"""
    db_user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == user_phone_number).first()
    return db_user.name if db_user else user_name

def process_message(message: str, user_name: str, user_phone_number: str, db: Session) -> str:
    """Procesa el mensaje del usuario y retorna la respuesta apropiada"""
    message = message.lower().strip()
    
    # Mapeo de opciones de texto a números
    option_map = {
        '1': '1', 'contacto': '1',
        '2': '2', 'pago': '2', 'comprobante': '2',
        '3': '3', 'animo': '3', 'ánimo': '3',
        '4': '4', 'datos': '4',
        '5': '5', 'cancelar': '5', 'suscripcion': '5', 'suscripción': '5',
    }

    # Determinar la opción elegida
    chosen_option = None
    for keyword, option_number in option_map.items():
        if keyword in message:
            chosen_option = option_number
            break

    # Procesar comando de menú
    if message in ['menu', 'hola']:
        return (
            "¡Bienvenido a Agropecuaria Juradó S.A.S! 👋\n\n"
            "Para poder ayudarte, por favor elige una de las siguientes opciones:\n\n"
            "1. Números de contacto 📲\n"
            "2. Mi comprobante de pago 🧾\n"
            "3. Mi estado de ánimo 😊\n"
            "4. Tratamiento de datos 📄\n"
            "5. Cancelar mi suscripción ❌\n\n"
            "Responde con el número o una palabra clave de la opción que necesitas (ej: 'pago', 'cancelar')."
        )
    
    # Procesar opciones del menú
    elif chosen_option:
        if chosen_option == '5':  # Cancelar suscripción
            user = db.query(WhatsappUser).filter(WhatsappUser.name == user_name).first()
            if user:
                user.is_active = False
                db.commit()
                return "Tu suscripción ha sido cancelada. No recibirás más mensajes de nuestra parte a menos que nos vuelvas a contactar."
            else:
                return "No se pudo encontrar tu suscripción para cancelar."

        elif chosen_option == '1':  # Números de contacto
            return (
                "*Nuestros números de contacto son:* 📞\n\n"
                "👩‍💼 *Área de Talento Humano:*\n"
                "322 5137306\n\n"
                "🧾 *Área de Contabilidad:*\n"
                "310 3367098\n\n"
                "🌐 *Sitio web:*\n"
                "www.agrojurado.com"
            )
        
        elif chosen_option == '4':  # Tratamiento de datos
            display_name = get_display_name(user_phone_number, user_name, db)
            return (
                "📄 *Tratamiento de Datos Personales*\n\n"
                f"Hola {display_name}, te informamos que Agropecuaria Juradó S.A.S., en cumplimiento de la Ley 1581 de 2012, "
                "los datos personales que nos suministras serán tratados conforme a nuestra política de tratamiento de datos "
                "y confidencialidad. No se compartirán con terceros sin tu autorización.\n\n"
                "Para más detalles, puedes consultar nuestra política completa en nuestro sitio web: www.agrojurado.com"
            )
        
        else:
            # TODO: Implementar la lógica para las demás opciones
            return f"Has elegido la opción {chosen_option}. Próximamente implementaremos esta función."
    
    else:
        # Opción no válida
        return "Por favor, elige una opción válida del menú."

# =============================================================================
# RUTAS BÁSICAS
# =============================================================================

@app.get("/")
async def root():
    """Ruta raíz de la API"""
    return {"message": "WhatsApp Chatbot API - Agropecuaria Juradó S.A.S"}

# =============================================================================
# RUTAS WEBSOCKET
# =============================================================================

@app.websocket("/ws/{phone_number}")
async def websocket_endpoint(websocket: WebSocket, phone_number: str):
    """WebSocket específico para un número de teléfono"""
    await manager.connect(websocket, phone_number)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, phone_number)

@app.websocket("/ws")
async def websocket_general_endpoint(websocket: WebSocket):
    """WebSocket general para todos los contactos"""
    await manager.connect_general(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_general(websocket)

# =============================================================================
# RUTAS DE WEBHOOK (WHATSAPP)
# =============================================================================

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verificación del webhook de WhatsApp"""
    print(f"Webhook verification attempt:")
    hub_mode = request.query_params.get("hub.mode")
    hub_challenge = request.query_params.get("hub.challenge")
    hub_verify_token = request.query_params.get("hub.verify_token")

    print(f"  hub_mode: {hub_mode}")
    print(f"  hub_challenge: {hub_challenge}")
    print(f"  hub_verify_token: {hub_verify_token}")
    print(f"  Expected VERIFY_TOKEN: {VERIFY_TOKEN}")
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhook")
async def webhook_notification(request: Request, db: Session = Depends(get_db)):
    """Procesa las notificaciones entrantes de WhatsApp"""
    try:
        body = await request.json()
        print(f"Webhook received: {json.dumps(body, indent=2)}")
        
        # Procesar cada entrada del webhook
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("value", {}).get("messages"):
                    for message in change["value"]["messages"]:
                        # Extraer información del mensaje
                        user_phone_number = message.get("from")
                        user_message = message.get("text", {}).get("body", "")
                        user_name = None
                        
                        # Obtener nombre del contacto si está disponible
                        if change["value"].get("contacts"):
                            contact = change["value"]["contacts"][0]
                            user_name = contact.get("profile", {}).get("name")
                        
                        print(f"Processing message from {user_phone_number}: {user_message}")
                        
                        # Crear o actualizar usuario en la base de datos
                        create_or_update_whatsapp_user(db, user_phone_number, user_name)
                        
                        # Guardar mensaje del usuario
                        user_message_obj = Message(
                            id=f"user_{user_phone_number}_{int(datetime.utcnow().timestamp())}",
                            phone_number=user_phone_number,
                            sender='user',
                            content=user_message,
                            status='received'
                        )
                        db.add(user_message_obj)
                        db.commit()
                        
                        # Notificar a clientes conectados
                        message_data = {
                            "type": "new_message",
                            "message": {
                                "id": user_message_obj.id,
                                "text": user_message_obj.content,
                                "sender": "user",
                                "timestamp": user_message_obj.timestamp.isoformat(),
                                "phone_number": user_phone_number,
                                "status": user_message_obj.status
                            }
                        }
                        
                        await manager.send_message_to_phone(user_phone_number, message_data)
                        await manager.send_message_to_all(message_data)
                        
                        # Procesar mensaje y enviar respuesta
                        response_text = process_message(user_message.lower(), user_name, user_phone_number, db)
                        
                        if response_text:
                            await send_whatsapp_message(to=user_phone_number, message=response_text)
                            
                            # Guardar respuesta del bot
                            bot_message_obj = Message(
                                id=f"bot_{user_phone_number}_{int(datetime.utcnow().timestamp())}",
                                phone_number=user_phone_number,
                                sender='bot',
                                content=response_text,
                                status='sent'
                            )
                            db.add(bot_message_obj)
                            db.commit()
                            
                            # Notificar respuesta del bot
                            bot_message_data = {
                                "type": "new_message",
                                "message": {
                                    "id": bot_message_obj.id,
                                    "text": bot_message_obj.content,
                                    "sender": "bot",
                                    "timestamp": bot_message_obj.timestamp.isoformat(),
                                    "phone_number": user_phone_number,
                                    "status": bot_message_obj.status
                                }
                            }
                            
                            await manager.send_message_to_phone(user_phone_number, bot_message_data)
                            await manager.send_message_to_all(bot_message_data)
        
        return {"status": "ok"}
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

# =============================================================================
# RUTAS DE PLANTILLAS (TEMPLATES)
# =============================================================================

@app.get("/api/templates")
async def get_templates(db: Session = Depends(get_db)):
    """Obtiene las plantillas de WhatsApp Business API (solo las no archivadas)"""
    try:
        from services.whatsapp_service import get_archived_templates as get_archived_templates_service
        
        # Obtener plantillas archivadas de la base de datos local
        archived_templates = get_archived_templates_service(db)
        archived_ids = {template.id for template in archived_templates}
        
        templates_data = get_whatsapp_templates()
        
        # Plantillas de fallback si no hay datos
        if not templates_data or not templates_data.get('data'):
            print("[main.py] No se encontraron plantillas en WhatsApp Business API, usando plantillas de ejemplo")
            return {
                "templates": [
                    {
                        "id": "welcome_message",
                        "name": "Bienvenida Agrojurado",
                        "category": "UTILITY",
                        "language": "es",
                        "status": "APPROVED",
                        "is_archived": False,
                        "components": [
                            {
                                "type": "HEADER",
                                "format": "TEXT",
                                "text": "¡Bienvenido a Agrojurado!"
                            },
                            {
                                "type": "BODY",
                                "text": "Hola {{1}}, gracias por contactar a Agrojurado. ¿En qué podemos ayudarte hoy?"
                            }
                        ]
                    },
                    {
                        "id": "contact_info",
                        "name": "Información de Contacto",
                        "category": "UTILITY",
                        "language": "es",
                        "status": "APPROVED",
                        "is_archived": False,
                        "components": [
                            {
                                "type": "BODY",
                                "text": "Nuestros canales de atención:\n\n📞 WhatsApp: 301 234 5678\n📞 Línea Nacional: 01 8000 123 456\n🕐 Horario: L-V 8AM-6PM, Sáb 8AM-1PM"
                            }
                        ]
                    }
                ]
            }
        else:
            # Convertir plantillas de WhatsApp al formato del frontend
            whatsapp_templates = templates_data.get('data', [])
            templates = []
            
            for template in whatsapp_templates:
                # Filtrar plantillas archivadas
                if template.get("id") not in archived_ids:
                    template_obj = {
                        "id": template.get("id"),
                        "name": template.get("name"),
                        "category": template.get("category"),
                        "language": template.get("language"),
                        "status": template.get("status"),
                        "is_archived": False,  # Las plantillas de WhatsApp no están archivadas por defecto
                        "components": template.get("components", [])
                        }
                    templates.append(template_obj)
            
            return {"templates": templates}
            
    except Exception as e:
        print(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting templates: {e}")

@app.post("/api/templates", status_code=201)
async def create_template(template_request: TemplateRequest):
    """Crea una nueva plantilla en WhatsApp Business API"""
    try:
        result = create_whatsapp_template(
            name=template_request.name,
            content=template_request.content,
            category=template_request.category,
            language=template_request.language,
            footer=template_request.footer
        )
        return {"message": "Template created successfully", "result": result}
    except Exception as e:
        print(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {e}")

@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    """Elimina una plantilla de WhatsApp Business API"""
    try:
        # Primero obtener el nombre de la plantilla desde la base de datos o API
        # Por ahora, asumimos que el template_id es el nombre formateado
        success = delete_whatsapp_template(template_id)
        if success:
            return {"message": "Template deleted successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to delete template")
    except Exception as e:
        print(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting template: {e}")

@app.post("/api/templates/{template_id}/archive")
async def archive_template(template_id: str, db: Session = Depends(get_db)):
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

@app.post("/api/templates/{template_id}/unarchive")
async def unarchive_template(template_id: str, db: Session = Depends(get_db)):
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

@app.get("/api/templates/archived")
async def get_archived_templates(db: Session = Depends(get_db)):
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

@app.post("/api/templates/send")
async def send_template_to_contacts(request: SendTemplateRequest, db: Session = Depends(get_db)):
    """Envía una plantilla a múltiples contactos"""
    try:
        template_name = request.template_name
        phone_numbers = request.phone_numbers
        parameters = request.parameters
        
        results = []
        success_count = 0
        
        for phone_number in phone_numbers:
            try:
                # Enviar plantilla a WhatsApp
                success = send_whatsapp_template(
                    to=phone_number,
                    template_name=template_name,
                    parameters=parameters
                )
                
                if success:
                    # Crear contenido de la plantilla para guardar
                    template_content = f"Plantilla enviada: {template_name}"
                    if parameters:
                        template_content += f" con parámetros: {parameters}"
                    
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
                        "message": "Plantilla enviada exitosamente"
                    })
                    success_count += 1
                else:
                    results.append({
                        "phone_number": phone_number,
                        "success": False,
                        "message": "Error al enviar plantilla"
                    })
                    
            except Exception as e:
                print(f"Error enviando plantilla a {phone_number}: {e}")
                results.append({
                    "phone_number": phone_number,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
        
        return {
            "template_name": template_name,
            "total_contacts": len(phone_numbers),
            "success_count": success_count,
            "results": results
        }
        
    except Exception as e:
        print(f"Error sending template: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending template: {e}")

# =============================================================================
# RUTAS DE CONTACTOS
# =============================================================================

@app.get("/api/contacts")
async def get_contacts():
    """Obtiene todos los contactos de la base de datos"""
    db = SessionLocal()
    try:
        contacts = db.query(WhatsappUser).all()
        return {"contacts": [
            {
                "phone_number": contact.phone_number,
                "name": contact.name,
                "last_interaction": contact.last_interaction.isoformat() if contact.last_interaction else None,
                "is_active": contact.is_active
            }
            for contact in contacts
        ]}
    finally:
        db.close()

@app.post("/api/contacts", status_code=201)
async def create_contact(contact_request: ContactCreateRequest, db: Session = Depends(get_db)):
    """Crea un nuevo contacto"""
    try:
        # Verificar si el contacto ya existe
        existing_contact = db.query(WhatsappUser).filter(
            WhatsappUser.phone_number == contact_request.phone_number
        ).first()
        
        if existing_contact:
            raise HTTPException(status_code=400, detail="Contact already exists")
        
        # Crear nuevo contacto
        new_contact = WhatsappUser(
            phone_number=contact_request.phone_number,
            name=contact_request.name,
            is_active=contact_request.is_active
        )
        
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        
        return {
            "message": "Contact created successfully",
            "contact": {
                "phone_number": new_contact.phone_number,
                "name": new_contact.name,
                "is_active": new_contact.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating contact: {e}")

@app.put("/api/contacts/{phone_number}")
async def update_contact(phone_number: str, contact_request: ContactUpdateRequest, db: Session = Depends(get_db)):
    """Actualiza un contacto existente"""
    try:
        contact = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Actualizar campos
        if contact_request.name is not None:
            contact.name = contact_request.name
        if contact_request.is_active is not None:
            contact.is_active = contact_request.is_active
        
        db.commit()
        db.refresh(contact)
        
        return {
            "message": "Contact updated successfully",
            "contact": {
                "phone_number": contact.phone_number,
                "name": contact.name,
                "is_active": contact.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating contact: {e}")

@app.delete("/api/contacts/{phone_number}")
async def delete_contact(phone_number: str, db: Session = Depends(get_db)):
    """Elimina un contacto"""
    try:
        contact = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        db.delete(contact)
        db.commit()
        
        return {"message": "Contact deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting contact: {e}")

@app.get("/api/contacts/{phone_number}")
async def get_contact(phone_number: str, db: Session = Depends(get_db)):
    """Obtiene un contacto específico"""
    try:
        contact = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return {
            "phone_number": contact.phone_number,
            "name": contact.name,
            "last_interaction": contact.last_interaction.isoformat() if contact.last_interaction else None,
            "is_active": contact.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting contact: {e}")

# =============================================================================
# RUTAS DE MENSAJES
# =============================================================================

@app.get("/api/messages/{phone_number}")
async def get_messages(
    phone_number: str, 
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Mensajes por página"),
    db: Session = Depends(get_db)
):
    """Obtiene mensajes paginados para un número de teléfono"""
    try:
        # Calcular offset
        offset = (page - 1) * limit
        
        # Obtener mensajes (más recientes primero para mostrar los últimos)
        messages = db.query(Message).filter(
            Message.phone_number == phone_number
        ).order_by(Message.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Revertir el orden para mostrar cronológicamente (más antiguos arriba, más recientes abajo)
        messages = list(reversed(messages))
        
        # Contar total de mensajes
        total_messages = db.query(Message).filter(
            Message.phone_number == phone_number
        ).count()
        
        # Calcular información de paginación
        total_pages = (total_messages + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "text": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status
                }
                for msg in messages
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_messages": total_messages,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {e}")

@app.get("/api/messages/{phone_number}/older")
async def get_older_messages(
    phone_number: str,
    before_timestamp: str = Query(..., description="Timestamp del mensaje más antiguo actual"),
    limit: int = Query(50, ge=1, le=100, description="Mensajes a cargar"),
    db: Session = Depends(get_db)
):
    """Obtiene mensajes más antiguos que un timestamp específico"""
    try:
        # Convertir timestamp string a datetime
        before_time = datetime.fromisoformat(before_timestamp.replace('Z', '+00:00'))
        
        # Obtener mensajes más antiguos (ordenados cronológicamente)
        messages = db.query(Message).filter(
            Message.phone_number == phone_number,
            Message.timestamp < before_time
        ).order_by(Message.timestamp.asc()).limit(limit).all()
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "text": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status
                }
                for msg in messages
            ],
            "has_more": len(messages) == limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting older messages: {e}")

@app.get("/api/debug/messages/{phone_number}")
async def debug_messages(phone_number: str, db: Session = Depends(get_db)):
    """Endpoint de debug para ver todos los mensajes de un número"""
    try:
        messages = db.query(Message).filter(
            Message.phone_number == phone_number
        ).order_by(Message.timestamp.asc()).all()
        
        return {
            "phone_number": phone_number,
            "total_messages": len(messages),
            "messages": [
                {
                    "id": msg.id,
                    "text": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting debug messages: {e}")

@app.get("/api/messages/{phone_number}/recent")
async def get_recent_messages(
    phone_number: str,
    limit: int = Query(20, ge=1, le=50, description="Mensajes recientes a obtener"),
    db: Session = Depends(get_db)
):
    """Obtiene los mensajes más recientes para un número de teléfono"""
    try:
        messages = db.query(Message).filter(
            Message.phone_number == phone_number
        ).order_by(Message.timestamp.desc()).limit(limit).all()
        
        # Revertir el orden para mostrar cronológicamente (más antiguos arriba, más recientes abajo)
        messages = list(reversed(messages))
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "text": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recent messages: {e}")

@app.post("/api/messages/send")
async def send_message(request: Request, db: Session = Depends(get_db)):
    """Envía un mensaje desde el frontend"""
    try:
        data = await request.json()
        phone_number = data.get("phone_number")
        message_text = data.get("message")
        
        if not phone_number or not message_text:
            raise HTTPException(status_code=400, detail="phone_number and message are required")
        
        # Enviar mensaje a WhatsApp
        success = send_whatsapp_message(to=phone_number, message=message_text)
        
        if success:
            # Guardar mensaje en la base de datos
            message_obj = Message(
                id=f"user_frontend_{phone_number}_{int(datetime.utcnow().timestamp())}",
                phone_number=phone_number,
                sender='bot',
                content=message_text,
                status='sent'
            )
            db.add(message_obj)
            db.commit()
            
            return {"success": True, "message": "Message sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send message to WhatsApp")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {e}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)