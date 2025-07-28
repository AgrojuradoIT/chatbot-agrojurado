from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Request, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, get_db
from models.whatsapp_models import WhatsappUser
from pydantic import BaseModel
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from services.whatsapp_service import send_whatsapp_message
from services.gemini_service import generate_gemini_response
from models.whatsapp_models import WebhookRequest

app = FastAPI()

# --- Tareas Programadas (APScheduler) ---

def check_inactive_users():
    db = SessionLocal()
    try:
        now = db.query(func.now()).scalar()
        inactive_time_warn = now - timedelta(minutes=10)
        inactive_time_close = now - timedelta(minutes=11)

        # Usuarios para la segunda notificación (cierre)
        users_to_close = db.query(WhatsappUser).filter(
            WhatsappUser.is_active == True,
            WhatsappUser.inactivity_warning_sent == True,
            WhatsappUser.last_interaction < inactive_time_close
        ).all()

        for user in users_to_close:
            send_whatsapp_message(
                to=user.phone_number, 
                message="Gracias por comunicarte con nosotros. Esperamos que tus dudas hayan sido resueltas. ¡Vuelve pronto!"
            )
            user.is_active = False
            user.inactivity_warning_sent = False # Reset for future interactions
            db.commit()

        # Usuarios para la primera notificación ("¿Estás ahí?")
        users_to_warn = db.query(WhatsappUser).filter(
            WhatsappUser.is_active == True,
            WhatsappUser.inactivity_warning_sent == False,
            WhatsappUser.last_interaction < inactive_time_warn
        ).all()

        for user in users_to_warn:
            send_whatsapp_message(to=user.phone_number, message="¿Estás ahí?")
            user.inactivity_warning_sent = True
            db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(check_inactive_users, 'interval', minutes=1)
    scheduler.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown()

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

# --- Modelos de Datos (Pydantic) ---
class Message(BaseModel):
    message: str

# --- Endpoints de la API ---

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.post("/chat")
def chat(message: Message):
    response = generate_gemini_response(message.message)
    if "Error" in response:
        raise HTTPException(status_code=503, detail=response)
    return {"response": response}

# --- Endpoints para Webhook de WhatsApp ---

@app.get("/webhook")
def verify_webhook(request: Request):
    """
    Verifica el webhook de WhatsApp. 
    Meta enviará una solicitud GET a esta URL con los parámetros:
    hub.mode, hub.challenge, hub.verify_token
    """
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        print("Webhook verificado exitosamente!")
        return Response(content=challenge, media_type="text/plain", status_code=200)
    else:
        print("Error de verificación de Webhook.")
        raise HTTPException(status_code=403, detail="Error de verificación")

from services.whatsapp_service import send_whatsapp_message

@app.post("/webhook")
async def webhook_notification(data: WebhookRequest, db: Session = Depends(get_db)):
    """
    Recibe y procesa las notificaciones de mensajes de WhatsApp.
    """
    print("\n--- Notificación de WhatsApp recibida ---")
    print(data.model_dump_json(indent=2))
    print("-----------------------------------------")

    try:
        # Extraer información del mensaje
        if data.entry and data.entry[0].changes:
            change = data.entry[0].changes[0]
            if change.value and change.value.messages:
                message = change.value.messages[0]
                if message.get("type") == "text":
                    user_phone_number = message["from"]
                    user_name = change.value.contacts[0]['profile']['name'] if change.value.contacts else 'Usuario'
                    user_message = message["text"]["body"]

                    # --- Lógica de Base de Datos ---
                    db_user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == user_phone_number).first()
                    if not db_user:
                        db_user = WhatsappUser(phone_number=user_phone_number, name=user_name)
                        db.add(db_user)
                    
                    db_user.last_interaction = db.query(func.now()).scalar()
                    db_user.is_active = True # Se reactiva si vuelve a escribir
                    db_user.inactivity_warning_sent = False # Resetea el aviso al recibir mensaje
                    db.commit()
                    db.refresh(db_user)
                else:
                    # Ignorar otros tipos de mensajes (stikcers, imagenes, etc)
                    return Response(status_code=200)

                print(f"Mensaje de {user_phone_number}: {user_message}")

                # Lógica del menú y validación
                user_input = user_message.lower().strip()

                # Mapeo de opciones de texto a números
                option_map = {
                    '1': '1',
                    'contacto': '1',
                    '2': '2',
                    'pago': '2',
                    'comprobante': '2',
                    '3': '3',
                    'animo': '3',
                    'ánimo': '3',
                    '4': '4',
                    'datos': '4',
                    '5': '5',
                    'cancelar': '5',
                    'suscripcion': '5',
                    'suscripción': '5',
                }

                chosen_option = None
                for keyword, option_number in option_map.items():
                    if keyword in user_input:
                        chosen_option = option_number
                        break

                if user_input in ['menu', 'hola']:
                    menu_text = (
                        "¡Bienvenido a Agropecuaria Juradó S.A.S! 👋\n\n"
                        "Para poder ayudarte, por favor elige una de las siguientes opciones:\n\n"
                        "1. Números de contacto 📲\n"
                        "2. Mi comprobante de pago 🧾\n"
                        "3. Mi estado de ánimo 😊\n"
                        "4. Tratamiento de datos 📄\n"
                        "5. Cancelar mi suscripción ❌\n\n"
                        "Responde con el número o una palabra clave de la opción que necesitas (ej: 'pago', 'cancelar')."
                    )
                    send_whatsapp_message(to=user_phone_number, message=menu_text)
                elif chosen_option:
                    if chosen_option == '5': # Cancelar suscripción
                        db_user.is_active = False
                        db.commit()
                        response_text = "Tu suscripción ha sido cancelada. No recibirás más mensajes de nuestra parte a menos que nos vuelvas a contactar."
                        send_whatsapp_message(to=user_phone_number, message=response_text)
                        return Response(status_code=200)

                    if chosen_option == '1':
                        response_text = (
                            "*Nuestros números de contacto son:* 📞\n\n"
                            "👩‍💼 *Área de Talento Humano:*\n"
                            "322 5137306\n\n"
                            "🧾 *Área de Contabilidad:*\n"
                            "310 3367098\n\n"
                            "🌐 *Sitio web:*\n"
                            "www.agrojurado.com"
                        )
                    elif chosen_option == '4':
                        response_text = (
                            "📄 *Tratamiento de Datos Personales*\n\n"
                            f"Hola {user_name}, te informamos que Agropecuaria Juradó S.A.S., en cumplimiento de la Ley 1581 de 2012, los datos personales que nos suministras serán tratados conforme a nuestra política de tratamiento de datos y confidencialidad. No se compartirán con terceros sin tu autorización.\n\n"
                            "Para más detalles, puedes consultar nuestra política completa en nuestro sitio web: www.agrojurado.com"
                        )
                    else:
                        # TODO: Implementar la lógica para las demás opciones
                        response_text = f"Has elegido la opción {chosen_option}. Próximamente implementaremos esta función."
                    send_whatsapp_message(to=user_phone_number, message=response_text)
                else:
                    # Si no es una opción de menú válida, ni 'menu' o 'hola', pedir que elija una opción.
                    error_message = "Por favor, elige una opción válida del menú."
                    send_whatsapp_message(to=user_phone_number, message=error_message)

    except Exception as e:
        print(f"Error inesperado en el webhook: {e}")
        import traceback
        traceback.print_exc()

    return Response(status_code=200)