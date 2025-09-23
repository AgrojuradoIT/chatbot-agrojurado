"""
Servicio de gestión del chatbot
Este archivo maneja todas las funcionalidades relacionadas con el chatbot, 
los mensajes y las conversaciones con usuarios
"""

from sqlalchemy.orm import Session
from models.whatsapp_models import WhatsappUser, Message
from services.whatsapp_service import send_whatsapp_message, create_or_update_whatsapp_user
from services.receipt_service import ReceiptService
from services.validation_service import ValidationService
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import json

# Mensajes constantes
WELCOME_MESSAGE = (
    "¡Bienvenid@ a Agropecuaria Juradó S.A.S! 👋\n\n"
    "Para poder ayudarte, por favor elige una de las siguientes opciones: 👇\n\n"
    "*1.* 📲 Lineas de atención\n\n"
    "*2.* 🧾 Mi comprobante de pago\n\n"
    "*3.* 😊 Mi estado de ánimo\n\n"
    "*4.* 📣 Realizar una queja o denuncia\n\n"
    "*5.* 👤 Tratamiento de datos\n\n"
    "*6.* ❌ Cancelar mi suscripción\n\n"
    "_💡 Responde con el número de la opción que necesitas._"
)

# Mensaje común para volver al menú principal
MENU_RETURN_MESSAGE = (
    "_Para volver al menú principal, escribe:_\n"
    "(' *0* ', ' *menu* ', ' *volver* ' o ' *salir* ')."
)

def get_display_name(user_phone_number: str, user_name: str, db: Session) -> str:
    """Obtiene el nombre de display desde la base de datos o usa el nombre de WhatsApp como fallback"""
    user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == user_phone_number).first()
    return user.name if user and user.name else user_name

async def process_message(message: str, user_name: str, user_phone_number: str, db: Session) -> str:
    """Procesa el mensaje del usuario y retorna la respuesta apropiada"""
    
    message = message.lower().strip()
    
    # Crear o actualizar usuario en la base de datos
    create_or_update_whatsapp_user(db, user_phone_number, user_name)
    
    # Obtener el nombre de display
    display_name = get_display_name(user_phone_number, user_name, db)
    
    # Mensajes reutilizables (definidos después de obtener display_name)
    CONTACT_MESSAGE = (
        "*📲 Lineas de atención*\n\n"
        "Nuestras líneas de atención están habilitadas para brindarte soporte y orientación.\n\n"
        "*Horario de atención:*\n\n"
        "*Lunes a Viernes:*\n"
        "06:55 a.m. a 3:30 p.m.\n\n"
        "*Sabados:*\n"
        "06:55 a.m. a 12:30 m.\n\n"
        "👩‍💼 *Área de Talento Humano:*\n"
        "322 513 7306\n\n"
        "🧾 *Área de Contabilidad:*\n"
        "310 336 7098\n\n"
        "🦺 *Área de SST:*\n"
        "311 569 1769\n\n"
        "🌐 *Página web:*\n"
        "www.agrojurado.com\n\n"
        "📧 *Correo electrónico:*\n"
        "info@agrojurado.com\n\n"

        "_Escribe *Menú* o *Volver* para regresar al menú principal._"
    )
    
    DATA_TREATMENT_MESSAGE = (
        "📄 *Tratamiento de Datos Personales*\n\n"
        f"Hola {display_name}, te informamos que Agropecuaria Juradó S.A.S., en cumplimiento de la Ley 1581 de 2012, "
        "los datos personales que nos suministras serán tratados conforme a nuestra política de tratamiento de datos "
        "y confidencialidad. No se compartirán con terceros sin tu autorización.\n\n"
        "_Para más detalles, puedes consultar nuestra política completa en nuestro sitio web: www.agrojurado.com_"
    )
    
    RECEIPT_INIT_MESSAGE = (
        "🧾 *Comprobante de Pago*\n\n"
        "Para buscar tu comprobante de pago por favor, *ingresa tu número de cédula*\n"
        "_(solo números y sin espacio)_.\n\n"
        "Ejemplo: *1001234567*\n\n"
        "💡 _Escribe *cancelar* en cualquier momento para volver al menú principal_"
    )
    
    # Obtener el estado de conversación del usuario
    user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == user_phone_number).first()
    
    print(f"🔍 DEBUG: Usuario encontrado: {user is not None}")
    if user:
        print(f"🔍 DEBUG: Estado de conversación: '{user.conversation_state}'")
        print(f"🔍 DEBUG: Datos de conversación: '{user.conversation_data}'")
    
    # Si el usuario está en proceso de solicitar comprobante
    if hasattr(user, 'conversation_state') and user.conversation_state:
        response_text = await _handle_receipt_conversation(message, user_phone_number, user, db, display_name)
        
        # ENVIAR LA RESPUESTA AUTOMÁTICA A WHATSAPP
        if response_text:
            try:
                print(f"🤖 Enviando respuesta automática a {user_phone_number}: {response_text}")
                success = send_whatsapp_message(to=user_phone_number, message=response_text)
                
                if success:
                    print("✅ Respuesta automática enviada exitosamente")
                    print("✅ Respuesta automática enviada (no registrada en BD)")
                else:
                    print("❌ Error al enviar respuesta automática")
                    
            except Exception as e:
                print(f"❌ Error enviando respuesta automática: {e}")
        
        return response_text
    
    # Mapeo de opciones de texto a números
    option_map = {
        '1': '1', 'contacto': '1',
        '2': '2', 'pago': '2', 'comprobante': '2',
        '3': '3', 'animo': '3', 'ánimo': '3',
        '4': '4', 'queja': '4', 'denuncia': '4',
        '5': '5', 'datos': '5',
        '6': '6', 'suscripcion': '6', 'suscripción': '6',
    }

    # Determinar la opción elegida
    chosen_option = None
    for keyword, option_number in option_map.items():
        if keyword in message:
            chosen_option = option_number
            break

    # Procesar opciones del menú
    if chosen_option:
        if chosen_option == '6':  # Cancelar suscripción
            if user:
                user.is_active = False
                db.commit()
                response_text = "Tu suscripción ha sido cancelada. No recibirás más mensajes de nuestra parte a menos que nos vuelvas a contactar."
            else:
                response_text = "No se pudo encontrar tu suscripción para cancelar."

        elif chosen_option == '1':  # Números de contacto
            response_text = CONTACT_MESSAGE
        
        elif chosen_option == '2':  # Comprobante de pago
            # Iniciar flujo de comprobante de pago
            if user:
                user.conversation_state = "waiting_cedula"
                db.commit()
            
            response_text = RECEIPT_INIT_MESSAGE
        
        elif chosen_option == '4':  # Realizar una queja o denuncia
            response_text = (
                "📢 *Realizar una queja o denuncia*\n\n"
                f"Hola {display_name}, para realizar una petición, queja, reclamo, sugerencia o denuncia, "
                "puedes hacerlo a través del formulario PQRS en nuestra página web:\n\n"
                "🌐 https://www.agrojurado.com/pqrs\n\n"
                "📧 pqrs@agrojurado.com\n\n"
                "📞 322 513 7306\n\n"

                "También puedes radicar tu solicitud de forma anónima desde el mismo formulario si así lo prefieres.\n\n"
                "Todas las solicitudes serán atendidas conforme a nuestros tiempos de respuesta establecidos.\n\n"
                "_Escribe *Menú* o *Volver* para regresar al menú principal._"
            )

        elif chosen_option == '5':  # Tratamiento de datos
            response_text = DATA_TREATMENT_MESSAGE

        elif chosen_option == '3':  # Estado de ánimo
            response_text = (
                "😊 *Estado de ánimo*\n\n"
                f"Hola {display_name}, actualmente esta opción no está disponible.\n\n"
                "_Escribe *Menú* o *Volver* para regresar al menú principal._"
            )
        
        else:
            # Implementación por defecto
            response_text = f"Has elegido la opción {chosen_option}. Próximamente implementaremos esta función."
    
    else:
        # Mostrar menú automáticamente para cualquier mensaje no reconocido
        response_text = WELCOME_MESSAGE

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

async def _handle_receipt_conversation(message: str, user_phone_number: str, user, db, display_name: str) -> str:
    """
    Maneja la conversación para solicitar comprobante de pago
    """
    
    print(f"🔍 DEBUG: Procesando conversación para {user_phone_number}")
    print(f"🔍 DEBUG: Estado de conversación: {user.conversation_state}")
    print(f"🔍 DEBUG: Mensaje recibido: '{message}'")
    
    conversation_state = user.conversation_state
    
    # Verificar si el usuario quiere cancelar o volver al menú
    cancel_keywords = ['cancelar', 'cancel', 'menu', 'menú', 'volver', 'atras', 'atrás', 'salir', '0']
    message_lower = message.lower().strip()
    
    # Solo cancelar si el mensaje completo coincide con una palabra clave
    if message_lower in cancel_keywords:
        # Limpiar estado de conversación
        user.conversation_state = None
        user.conversation_data = None
        db.commit()
        
        return WELCOME_MESSAGE
    
    if conversation_state == "waiting_cedula":
        print(f"🔍 DEBUG: Validando cédula: '{message}'")
        
        # Validar formato de cédula
        is_valid, cedula_message = ValidationService.validate_cedula_format(message)
        
        print(f"🔍 DEBUG: Validación cédula - Válida: {is_valid}, Mensaje: {cedula_message}")
        
        if not is_valid:
            response = f"❌ {cedula_message}\n\nPor favor, ingresa tu cédula nuevamente."
            print(f"🔍 DEBUG: Respuesta de error: {response}")
            return response
        
        # Verificar si la cédula está registrada en la base de datos
        is_registered, registration_message, user_data = ValidationService.is_cedula_registered(db, message)
        
        print(f"🔍 DEBUG: Verificación registro - Registrada: {is_registered}, Mensaje: {registration_message}")
        
        if not is_registered:
            # Mantener el estado para que pueda volver a escribir la cédula
            user.conversation_state = "waiting_cedula"
            user.conversation_data = None
            db.commit()
            
            response = (
                f"❌ La cédula {message} no existe en nuestros registros.\n\n"
                f"Por favor, ingresa tu número de cédula nuevamente:"
            )
            print(f"🔍 DEBUG: Respuesta de cédula no registrada: {response}")
            return response
        
        # Guardar cédula y cambiar estado
        conversation_data = {"cedula": message}
        user.conversation_data = json.dumps(conversation_data)
        user.conversation_state = "waiting_date"
        db.commit()
        
        print(f"🔍 DEBUG: Cédula guardada: {message}, Estado cambiado a: waiting_date")
        
        response = (
            f"¡Hola {user_data.name}! ☺️\n\n"
            f"para continuar, por favor ingresa la\n"
            f"*fecha de expedición de tu cédula*.\n\n"
            f"La fecha debe estar en formato:\n"
            f"*DD/MM/AAAA*\n\n"
            f"Ejemplo: *15/03/1990*"
        )
        print(f"🔍 DEBUG: Respuesta de éxito: {response}")
        return response
    
    elif conversation_state == "waiting_date":
        print(f"🔍 DEBUG: Validando fecha: '{message}'")
        
        # Validar formato de fecha
        is_valid, date_message, date_obj = ValidationService.validate_date_format(message)
        
        print(f"🔍 DEBUG: Validación fecha - Válida: {is_valid}, Mensaje: {date_message}, Objeto: {date_obj}")
        
        if not is_valid:
            response = f"❌ {date_message}\n\nPor favor, ingresa la fecha nuevamente en formato DD/MM/AAAA."
            print(f"🔍 DEBUG: Respuesta de error fecha: {response}")
            return response
        
        # Obtener cédula guardada
        conversation_data = json.loads(user.conversation_data or "{}")
        cedula = conversation_data.get("cedula")
        
        # Validar datos del usuario (cédula + fecha de expedición)
        print(f"🔍 DEBUG: Validando datos usuario - Cédula: {cedula}, Fecha: {date_obj}")
        user_valid, user_message, user_data = ValidationService.validate_user_data(db, cedula, date_obj)
        
        print(f"🔍 DEBUG: Validación datos usuario - Válida: {user_valid}, Mensaje: {user_message}")
        
        if not user_valid:
            response = f"❌ {user_message}\n\nPor favor, verifica la fecha de expedición e intenta nuevamente."
            print(f"🔍 DEBUG: Respuesta de error datos usuario: {response}")
            return response
        
        if not cedula:
            # Error en los datos guardados, reiniciar
            user.conversation_state = None
            user.conversation_data = None
            db.commit()
            return "❌ Error en el proceso. Por favor, inicia nuevamente seleccionando 'Mi comprobante de pago'."
        
        # Buscar y enviar los últimos dos comprobantes
        success, result_message = ReceiptService.search_and_send_receipt(
            db=db,
            cedula=cedula,
            expedition_date_str=message,
            phone_number=user_phone_number
        )
        
        # Verificar si necesitamos mostrar opciones de comprobantes
        if success and "options_sent" in result_message:
            # Guardar los comprobantes encontrados para la selección
            conversation_data = json.loads(user.conversation_data or "{}")
            conversation_data["receipts_found"] = True
            user.conversation_data = json.dumps(conversation_data)
            user.conversation_state = "waiting_receipt_selection"
            db.commit()
            
            # No retornar mensaje adicional, solo las opciones ya fueron enviadas
            return ""
        else:
            # Limpiar estado de conversación
            user.conversation_state = None
            user.conversation_data = None
            db.commit()
            
            if success:
                return (
                    f"✅ {result_message}\n\n"
                    "¡Espero que esto te ayude! Si necesitas algo más, no dudes en contactarnos.\n\n"
                    f"{MENU_RETURN_MESSAGE}"
                )
            else:
                return (
                    f"❌ {result_message}\n\n"
                    "Si crees que hay un error, por favor acercate a las oficinas de Talento Humano.\n\n"
                    f"{MENU_RETURN_MESSAGE}"
                )
    
    elif conversation_state == "waiting_receipt_selection":
        # Procesar selección de comprobante
        if message in ['1', '2']:
            # Obtener los comprobantes disponibles
            conversation_data = json.loads(user.conversation_data or "{}")
            cedula = conversation_data.get("cedula")
            
            if not cedula:
                # Error en los datos guardados, reiniciar
                user.conversation_state = None
                user.conversation_data = None
                db.commit()
                return "❌ Error en el proceso. Por favor, inicia nuevamente seleccionando 'Mi comprobante de pago'."
            
            # OPTIMIZACIÓN: Buscar directamente en la carpeta seleccionada
            folder_name = "recientes" if message == '2' else "anteriores"
            
            # Buscar comprobantes solo en la carpeta específica
            success, message_receipts, receipts = ReceiptService.get_receipts_by_folder(
                db=db,
                cedula=cedula,
                folder=folder_name
            )
            
            if not success:
                user.conversation_state = None
                user.conversation_data = None
                db.commit()
                
                # Mensaje específico según la carpeta
                if message == '2':  # Quincena actual
                    return (
                        "❌ Aún no tienes comprobantes de la quincena actual. 😓\n\n"
                        "Los comprobantes se generan después de cada pago de nómina.\n\n"
                        f"{MENU_RETURN_MESSAGE}"
                    )
                else:  # Quincena anterior
                    return (
                        "❌ No tienes comprobantes de la quincena anterior. 😓\n\n"
                        "Los comprobantes de quincenas anteriores se archivan automáticamente.\n\n"
                        f"{MENU_RETURN_MESSAGE}"
                    )
            
            # Si encontramos comprobantes, enviar el primero
            selected_receipt = receipts[0]
            file_name = selected_receipt['file_name']
            file_path = selected_receipt['file_path']
            
            success, result_message = ReceiptService.send_selected_receipt(selected_receipt, user_phone_number)
            
            # Limpiar estado de conversación
            user.conversation_state = None
            user.conversation_data = None
            db.commit()
            
            if success:
                return (
                    f"✅ {result_message}\n\n"
                    "¡Espero que esto te ayude! Si necesitas algo más, no dudes en contactarnos.\n\n"
                    f"{MENU_RETURN_MESSAGE}"
                )
            else:
                return (
                    f"❌ {result_message}\n\n"
                    "Si crees que hay un error, por favor contacta directamente a:\n"
                    "🧾 *Área de Contabilidad:* 310 3367098\n\n"
                    f"{MENU_RETURN_MESSAGE}"
                )
        else:
            return "❌ Por favor, responde con '1' para la quincena anterior o '2' para la quincena reciente."
    
    else:
        # Estado desconocido, reiniciar
        user.conversation_state = None
        user.conversation_data = None
        db.commit()
        return "❌ Error en el proceso. Por favor, inicia nuevamente seleccionando 'Mi comprobante de pago'."

def send_message_to_user(db: Session, phone_number: str, message: str, current_user: dict = None) -> Tuple[bool, Optional[Message], str]:
    """
    Envía un mensaje a un usuario y lo guarda en la base de datos
    Retorna: (éxito, objeto_mensaje, mensaje_error)
    """
    try:
        # Enviar mensaje a WhatsApp
        result = send_whatsapp_message(to=phone_number, message=message)
        
        if not result:
            return False, None, "Error al enviar mensaje a WhatsApp"
            
        # Guardar mensaje en la base de datos
        new_message = Message(
            phone_number=phone_number,
            content=message,
            sender="bot",
            message_id=result.get('messages', [{}])[0].get('id', None)
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        return True, new_message, "Mensaje enviado correctamente"
        
    except Exception as e:
        return False, None, f"Error al enviar mensaje: {str(e)}"

def handle_webhook_message(message_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Procesa un mensaje entrante desde el webhook de WhatsApp
    Retorna información del mensaje procesado
    """
    message_id = message_data.get("id")
    from_number = message_data.get("from")
    message_type = message_data.get("type")
    
    # Procesar mensajes de texto y respuestas de botones
    message_text = ""
    
    if message_type == "text":
        message_text = message_data.get("text", {}).get("body", "")
    elif message_type == "interactive":
        # Procesar respuesta de botón interactivo
        interactive_data = message_data.get("interactive", {})
        if interactive_data.get("type") == "button_reply":
            button_reply = interactive_data.get("button_reply", {})
            message_text = button_reply.get("id", "")  # El ID del botón presionado
            print(f"🔘 Botón presionado: ID='{message_text}', Título='{button_reply.get('title', '')}'")
    
    if not message_text:
        return {"success": False, "reason": "Tipo de mensaje no soportado o sin texto"}
        
    # Crear el mensaje del usuario en la BD
    timestamp = message_data.get("timestamp")
    
    user_message = Message(
        id=message_id,
        phone_number=from_number,
        content=message_text,
        sender="user"
    )
    
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    return {
        "success": True,
        "message": user_message,
        "message_text": message_text,
        "phone_number": from_number
    }