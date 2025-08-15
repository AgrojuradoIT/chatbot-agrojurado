from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from models.whatsapp_models import Message, WhatsappUser
from middleware.auth import get_current_user
from middleware.permissions import require_permission
from services.whatsapp_service import send_whatsapp_message
from datetime import datetime
from typing import List, Dict, Any
import math

router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.get("/chats")
async def get_chats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.view"))
):
    """Obtiene lista de chats (contactos con mensajes) ordenados por mensaje más reciente"""
    try:
        # Subconsulta para obtener el mensaje más reciente de cada contacto
        latest_message_subquery = db.query(
            Message.phone_number,
            func.max(Message.timestamp).label('latest_timestamp')
        ).group_by(Message.phone_number).subquery()
        
        # Consulta principal para obtener los mensajes más recientes con información del contacto
        chats_query = db.query(
            Message.phone_number,
            Message.content,
            Message.timestamp,
            Message.sender,
            WhatsappUser.name
        ).join(
            latest_message_subquery,
            (Message.phone_number == latest_message_subquery.c.phone_number) &
            (Message.timestamp == latest_message_subquery.c.latest_timestamp)
        ).outerjoin(
            WhatsappUser,
            WhatsappUser.phone_number == Message.phone_number
        ).order_by(desc(Message.timestamp))
        
        chats_data = chats_query.all()
        
        # Formatear respuesta
        chats = []
        for chat in chats_data:
            chats.append({
                "id": chat.phone_number,
                "name": chat.name or "Sin nombre",
                "phone": chat.phone_number,
                "lastMessage": chat.content,
                "lastMessageTime": chat.timestamp.isoformat() if chat.timestamp else None,
                "lastMessageSender": chat.sender,
                "unreadCount": 0,  # TODO: Implementar conteo de no leídos
                "isOnline": False  # TODO: Implementar estado online
            })
        
        return {
            "chats": chats,
            "total": len(chats)
        }
        
    except Exception as e:
        print(f"Error al obtener chats: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener chats: {e}")

@router.get("/{phone_number}")
async def get_messages(
    phone_number: str, 
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Mensajes por página"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.view"))
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
                "total": total_messages,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {e}")


@router.get("/{phone_number}/recent")
async def get_recent_messages(
    phone_number: str,
    limit: int = Query(20, ge=1, le=50, description="Mensajes recientes a obtener"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.view"))
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


@router.get("/{phone_number}/older")
async def get_older_messages(
    phone_number: str,
    before_timestamp: str = Query(..., description="Timestamp del mensaje más antiguo actual"),
    limit: int = Query(50, ge=1, le=100, description="Mensajes a cargar"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.view"))
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
            "hasMore": len(messages) == limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting older messages: {e}")


@router.post("/send")
async def send_message(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.send.individual"))
):
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


@router.get("/")
async def get_all_messages(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(50, ge=1, le=100, description="Mensajes por página"),
    phone_number: str = Query(None, description="Filtrar por número de teléfono"),
    sender: str = Query(None, description="Filtrar por remitente (user/bot)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _: dict = Depends(require_permission("chatbot.messages.view"))
):
    """Obtiene todos los mensajes con filtros y paginación"""
    try:
        # Construir query base
        query = db.query(Message)
        
        # Aplicar filtros
        if phone_number:
            query = query.filter(Message.phone_number == phone_number)
        if sender:
            query = query.filter(Message.sender == sender)
        
        # Contar total de mensajes
        total = query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        messages = query.order_by(Message.timestamp.desc()).offset(offset).limit(per_page).all()
        
        # Calcular información de paginación
        total_pages = math.ceil(total / per_page)
        has_next = page < total_pages
        has_prev = page > 1
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "text": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "status": msg.status,
                    "phone_number": msg.phone_number
                }
                for msg in messages
            ],
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {e}")
