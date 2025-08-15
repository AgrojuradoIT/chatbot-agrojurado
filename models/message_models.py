from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageRequest(BaseModel):
    """Modelo para enviar un mensaje"""
    phone_number: str
    message: str

class MessageResponse(BaseModel):
    """Modelo para la respuesta de mensaje"""
    id: str
    phone_number: str
    message: str
    sender: str  # "user" or "bot"
    timestamp: datetime
    status: Optional[str] = None

class MessagesListResponse(BaseModel):
    """Modelo para la lista de mensajes con paginación"""
    messages: List[MessageResponse]
    pagination: Dict[str, Any]

class WebSocketMessage(BaseModel):
    """Modelo para mensajes de WebSocket"""
    type: str  # "message", "status", "error"
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None

class StatisticsResponse(BaseModel):
    """Modelo para estadísticas"""
    statistics: List[Dict[str, Any]]
    period: str
    total_contacts: int
    total_messages: int
    total_sent: int
    total_received: int
