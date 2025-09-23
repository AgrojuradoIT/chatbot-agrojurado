from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.whatsapp_models import WhatsappUser, Message
from utils.websocket_manager import manager
from services.whatsapp_service import send_whatsapp_message
from services.bot_service import process_message, send_message_to_user
from datetime import datetime
import json

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/{phone_number}")
async def websocket_endpoint(websocket: WebSocket, phone_number: str):
    """WebSocket específico para un número de teléfono"""
    await manager.connect(websocket, phone_number)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Mensaje recibido para {phone_number}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, phone_number)

@router.websocket("/ws")
async def websocket_general(websocket: WebSocket):
    """WebSocket general para todos los contactos"""
    await manager.connect_general(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                # Intentar parsear el mensaje como JSON
                message_data = json.loads(data)
                
                if message_data.get("type") == "send_message":
                    # Enviar mensaje a WhatsApp
                    phone_number = message_data.get("phone_number")
                    message_text = message_data.get("message")
                    
                    if phone_number and message_text:
                        # Obtener sesión de base de datos
                        db = next(get_db())
                        
                        try:
                            # Usar el servicio para enviar mensaje
                            success, new_message, error_msg = send_message_to_user(
                                db=db,
                                phone_number=phone_number,
                                message=message_text
                            )
                            
                            if success:
                                # Notificar a todos los clientes conectados
                                response = {
                                    "type": "message_sent",
                                    "data": {
                                        "id": str(new_message.id),
                                        "phone_number": phone_number,
                                        "message": message_text,
                                        "sender": "bot",
                                        "timestamp": new_message.timestamp.isoformat(),
                                        "status": "sent"
                                    }
                                }
                                
                                await manager.send_message_to_all(response)
                                await manager.send_message_to_phone(phone_number, response)
                            else:
                                # Error enviando mensaje
                                error_response = {
                                    "type": "error",
                                    "data": {
                                        "message": error_msg,
                                        "phone_number": phone_number
                                    }
                                }
                                await websocket.send_json(error_response)
                        
                        finally:
                            db.close()
                
                else:
                    # Echo del mensaje recibido
                    await websocket.send_text(f"Mensaje recibido: {data}")
                    
            except json.JSONDecodeError:
                # Si no es JSON válido, enviar como texto simple
                await websocket.send_text(f"Mensaje recibido: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect_general(websocket)
