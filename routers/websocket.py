from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.whatsapp_models import WhatsappUser, Message
from utils.websocket_manager import manager
from services.whatsapp_service import send_whatsapp_message, create_or_update_whatsapp_user
import json

router = APIRouter(tags=["websocket"])

def get_display_name(user_phone_number: str, user_name: str, db: Session) -> str:
    """Obtiene el nombre de display desde la base de datos o usa el nombre de WhatsApp como fallback"""
    user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == user_phone_number).first()
    return user.name if user and user.name else user_name

async def process_message(message: str, user_name: str, user_phone_number: str, db: Session) -> str:
    """Procesa el mensaje del usuario y retorna la respuesta apropiada"""
    from datetime import datetime
    
    message = message.lower().strip()
    
    # Crear o actualizar usuario en la base de datos
    create_or_update_whatsapp_user(db, user_phone_number, user_name)
    
    # Obtener el nombre de display
    display_name = get_display_name(user_phone_number, user_name, db)
    
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
        response_text = (
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
            user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == user_phone_number).first()
            if user:
                user.is_active = False
                db.commit()
                response_text = "Tu suscripción ha sido cancelada. No recibirás más mensajes de nuestra parte a menos que nos vuelvas a contactar."
            else:
                response_text = "No se pudo encontrar tu suscripción para cancelar."

        elif chosen_option == '1':  # Números de contacto
            response_text = (
                "*Nuestros números de contacto son:* 📞\n\n"
                "👩‍💼 *Área de Talento Humano:*\n"
                "322 5137306\n\n"
                "🧾 *Área de Contabilidad:*\n"
                "310 3367098\n\n"
                "🌐 *Sitio web:*\n"
                "www.agrojurado.com"
            )
        
        elif chosen_option == '4':  # Tratamiento de datos
            response_text = (
                "📄 *Tratamiento de Datos Personales*\n\n"
                f"Hola {display_name}, te informamos que Agropecuaria Juradó S.A.S., en cumplimiento de la Ley 1581 de 2012, "
                "los datos personales que nos suministras serán tratados conforme a nuestra política de tratamiento de datos "
                "y confidencialidad. No se compartirán con terceros sin tu autorización.\n\n"
                "Para más detalles, puedes consultar nuestra política completa en nuestro sitio web: www.agrojurado.com"
            )
        
        else:
            # TODO: Implementar la lógica para las demás opciones
            response_text = f"Has elegido la opción {chosen_option}. Próximamente implementaremos esta función."
    
    else:
        # Opción no válida
        response_text = "Por favor, elige una opción válida del menú."

    # ENVIAR LA RESPUESTA AUTOMÁTICA A WHATSAPP
    if response_text:
        try:
            print(f"🤖 Enviando respuesta automática a {user_phone_number}: {response_text}")
            success = send_whatsapp_message(to=user_phone_number, message=response_text)
            
            if success:
                print("✅ Respuesta automática enviada exitosamente")
                
                # NO GUARDAR mensajes automáticos en la base de datos
                # Las respuestas automáticas del bot no deben aparecer como mensajes en el chat
                # Solo se envían a WhatsApp, pero no se registran en la conversación del dashboard
                print("✅ Respuesta automática enviada (no registrada en BD)")
                
            else:
                print("❌ Error al enviar respuesta automática")
                
        except Exception as e:
            print(f"❌ Error enviando respuesta automática: {e}")
    
    return response_text

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
                            # Enviar mensaje a WhatsApp
                            result = send_whatsapp_message(phone_number, message_text)
                            
                            if result:
                                # Guardar mensaje en la base de datos
                                new_message = Message(
                                    phone_number=phone_number,
                                    content=message_text,
                                    sender="bot",
                                    message_id=result.get('messages', [{}])[0].get('id')
                                )
                                
                                db.add(new_message)
                                db.commit()
                                db.refresh(new_message)
                                
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
                                        "message": "Error enviando mensaje a WhatsApp",
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
