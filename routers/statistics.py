from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.whatsapp_models import WhatsappUser, Message
from models.message_models import StatisticsResponse
from middleware.auth import get_current_user
from middleware.permissions import require_role
from datetime import datetime, timedelta
from typing import List, Dict, Any

router = APIRouter(prefix="/api/statistics", tags=["statistics"])

@router.get("/", response_model=StatisticsResponse)
async def get_statistics(
    period: str = Query("30d", description="Período de estadísticas: 7d, 30d, 90d, all"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("Super Administrador"))
):
    """
    Obtiene estadísticas de mensajes por contacto.
    Solo accesible para Super Administrador.
    """
    try:
        # Calcular fecha de corte según el período
        cutoff_date = None
        if period != "all":
            days = int(period.replace("d", ""))
            cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Obtener todos los usuarios
        users = db.query(WhatsappUser).all()
        
        statistics = []
        
        for user in users:
            # Construir query base para mensajes
            query = db.query(Message).filter(Message.phone_number == user.phone_number)
            
            # Aplicar filtro de fecha si es necesario
            if cutoff_date:
                query = query.filter(Message.timestamp >= cutoff_date)
            
            messages = query.all()
            
            if messages:
                # Calcular estadísticas
                total_messages = len(messages)
                sent_messages = len([m for m in messages if m.sender == "bot"])
                received_messages = len([m for m in messages if m.sender == "user"])
                
                # Último mensaje
                last_message = max(messages, key=lambda m: m.timestamp)
                last_message_date = last_message.timestamp
                
                # Calcular tiempo promedio de respuesta
                response_times = []
                for i in range(len(messages) - 1):
                    current_msg = messages[i]
                    next_msg = messages[i + 1]
                    time_diff = abs((next_msg.timestamp - current_msg.timestamp).total_seconds() / 60)
                    if time_diff < 1440:  # Solo respuestas dentro de 24 horas
                        response_times.append(time_diff)
                
                average_response_time = None
                if response_times:
                    average_response_time = sum(response_times) / len(response_times)
                
                # Calcular frecuencia de mensajes
                first_message = min(messages, key=lambda m: m.timestamp)
                days_diff = (last_message_date - first_message.timestamp).days
                message_frequency = total_messages / max(days_diff, 1)
                
                statistics.append({
                    "contact": {
                        "phone_number": user.phone_number,
                        "name": user.name,
                        "last_interaction": last_message_date.isoformat(),
                        "is_active": True
                    },
                    "total_messages": total_messages,
                    "sent_messages": sent_messages,
                    "received_messages": received_messages,
                    "last_message_date": last_message_date.isoformat(),
                    "average_response_time": average_response_time,
                    "message_frequency": message_frequency
                })
        
        # Ordenar por total de mensajes descendente
        statistics.sort(key=lambda x: x["total_messages"], reverse=True)
        
        return StatisticsResponse(
            statistics=statistics,
            period=period,
            total_contacts=len(statistics),
            total_messages=sum(s["total_messages"] for s in statistics),
            total_sent=sum(s["sent_messages"] for s in statistics),
            total_received=sum(s["received_messages"] for s in statistics)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
