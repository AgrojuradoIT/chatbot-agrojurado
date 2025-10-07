from fastapi import APIRouter, HTTPException, Request, Query, Depends
from sqlalchemy.orm import Session
from database import get_db, get_db_sync
from models.whatsapp_models import WebhookRequest, Message
from utils.websocket_manager import manager
from services.bot_service import process_message, handle_webhook_message
from config.settings import settings
import asyncio

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("/")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token")
):
    """Verificación del webhook de WhatsApp"""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        print("Webhook verificado exitosamente")
        return int(hub_challenge)
    else:
        print("Error en la verificación del webhook")
        raise HTTPException(status_code=403, detail="Forbidden")

@router.post("/")
async def receive_webhook(request: Request):
    """Recibe webhooks de WhatsApp Business API"""
    db = None
    try:
        body = await request.json()
        
        # Obtener conexión a la base de datos
        db = get_db_sync()
        
        # Procesar el webhook
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        
                        # Procesar mensajes recibidos
                        for message in value.get("messages", []):
                            message_id = message.get("id")
                            from_number = message.get("from")
                            message_type = message.get("type")
                            
                            # Procesar mensajes de texto y respuestas de botones
                            message_text = ""
                            
                            if message_type == "text":
                                message_text = message.get("text", {}).get("body", "")
                            elif message_type == "interactive":
                                # Procesar respuesta de botón interactivo
                                interactive_data = message.get("interactive", {})
                                if interactive_data.get("type") == "button_reply":
                                    button_reply = interactive_data.get("button_reply", {})
                                    message_text = button_reply.get("id", "")
                            
                            if message_text:  # Solo procesar si tenemos texto válido
                                # Obtener información del contacto
                                contacts = value.get("contacts", [])
                                contact_name = "Usuario"
                                for contact in contacts:
                                    if contact.get("wa_id") == from_number:
                                        contact_name = contact.get("profile", {}).get("name", "Usuario")
                                        break
                                
                                # Usar la función de manejo de mensajes del webhook
                                result = handle_webhook_message(message, db)
                                
                                if result["success"]:
                                    user_message = result["message"]
                                    
                                    # Procesar mensaje y generar respuesta
                                    response_text = await process_message(message_text, contact_name, from_number, db)
                                    
                                    # Notificar a los clientes WebSocket
                                    websocket_message = {
                                        "type": "new_message",
                                        "message": {
                                            "id": str(user_message.id),
                                            "phone_number": from_number,
                                            "text": message_text,
                                            "sender": "user",
                                            "timestamp": user_message.timestamp.isoformat(),
                                            "contact_name": contact_name
                                        }
                                    }
                                    
                                    # Enviar a conexiones específicas del número
                                    await manager.send_message_to_phone(from_number, websocket_message)
                                    
                                    # Enviar a conexiones generales
                                    await manager.send_message_to_all(websocket_message)
                            
                        # Procesar estados de mensajes
                        for status in value.get("statuses", []):
                            message_id = status.get("id")
                            recipient_id = status.get("recipient_id")
                            status_value = status.get("status")
                            timestamp = status.get("timestamp")
                            
                            # Actualizar estado del mensaje en la base de datos si es necesario
                            message = db.query(Message).filter(Message.id == message_id).first()
                            if message:
                                # Aquí podrías actualizar el estado del mensaje si tienes ese campo
                                pass
                            
                            # Notificar cambio de estado por WebSocket
                            status_message = {
                                "type": "status",
                                "data": {
                                    "message_id": message_id,
                                    "phone_number": recipient_id,
                                    "status": status_value,
                                    "timestamp": timestamp
                                }
                            }
                            
                            await manager.send_message_to_phone(recipient_id, status_message)
                            await manager.send_message_to_all(status_message)
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if db:
            db.close()
