from fastapi import APIRouter, HTTPException, Request, Query, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.whatsapp_models import WebhookRequest, Message
from utils.websocket_manager import manager
from routers.websocket import process_message
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
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """Recibe webhooks de WhatsApp Business API"""
    try:
        body = await request.json()
        print(f"Webhook recibido: {body}")
        
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
                            
                            # Solo procesar mensajes de texto por ahora
                            if message_type == "text":
                                message_text = message.get("text", {}).get("body", "")
                                timestamp = message.get("timestamp")
                                
                                # Obtener información del contacto
                                contacts = value.get("contacts", [])
                                contact_name = "Usuario"
                                for contact in contacts:
                                    if contact.get("wa_id") == from_number:
                                        contact_name = contact.get("profile", {}).get("name", "Usuario")
                                        break
                                
                                print(f"Mensaje recibido de {from_number} ({contact_name}): {message_text}")
                                
                                # Guardar mensaje del usuario en la base de datos
                                user_message = Message(
                                    id=message_id,  # Usar message_id como id
                                    phone_number=from_number,
                                    content=message_text,
                                    sender="user"
                                )
                                
                                db.add(user_message)
                                db.commit()
                                db.refresh(user_message)
                                
                                # Procesar mensaje y generar respuesta
                                response_text = await process_message(message_text, contact_name, from_number, db)
                                
                                # La respuesta se envía automáticamente en process_message
                                # También se guarda en la base de datos y se notifica por WebSocket
                                
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
                            
                            print(f"Estado de mensaje {message_id} para {recipient_id}: {status_value}")
                            
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
        print(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}
