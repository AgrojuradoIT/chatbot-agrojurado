from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Boolean, func
from database import Base
from typing import List, Optional, Any, Dict

class ChangeValue(BaseModel):
    messaging_product: str
    metadata: dict
    contacts: Optional[List[dict]] = None
    errors: Optional[List[dict]] = None
    messages: Optional[List[dict]] = None
    statuses: Optional[List[dict]] = None

class Change(BaseModel):
    value: ChangeValue
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WebhookRequest(BaseModel):
    object: str
    entry: List[Entry]

class WhatsappUser(Base):
    __tablename__ = "whatsapp_users"

    phone_number = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    last_interaction = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    inactivity_warning_sent = Column(Boolean, default=False)
    conversation_state = Column(String(50), nullable=True)  # Estado de la conversación
    conversation_data = Column(String(1000), nullable=True)  # Datos temporales de la conversación (JSON)

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(100), primary_key=True, index=True)
    phone_number = Column(String(50), index=True)
    sender = Column(String(10))  # 'user' or 'bot'
    content = Column(String(1000))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(20), default='sent')  # 'sending', 'sent', 'delivered', 'error'

class TemplateRequest(BaseModel):
    name: str
    content: str
    category: str
    language: str = "es"
    footer: str = None

class TemplateWithMediaRequest(BaseModel):
    name: str
    content: str
    category: str
    language: str = "es"
    footer: str = None
    media_type: str = "IMAGE"  # IMAGE, VIDEO, DOCUMENT
    media_id: str = None
    image_url: str = None

class TemplateResponse(BaseModel):
    id: str
    name: str
    status: str
    category: str
    language: str
    created_at: str
    rejected_reason: Optional[str] = None

class SendTemplateRequest(BaseModel):
    template_name: str
    phone_numbers: List[str]
    parameters: Optional[Dict[str, Any]] = None

class SendTemplateWithMediaRequest(BaseModel):
    template_name: str
    phone_numbers: List[str]
    media_id: str
    parameters: Optional[Dict[str, Any]] = None
    header_parameters: Optional[Dict[str, Any]] = None

class ContactCreateRequest(BaseModel):
    phone_number: str
    name: str
    is_active: bool = True

class ContactUpdateRequest(BaseModel):
    name: str
    is_active: bool = True

class ContactResponse(BaseModel):
    phone_number: str
    name: str
    last_interaction: str
    is_active: bool

class Template(Base):
    __tablename__ = "templates"

    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    content = Column(String(1000), nullable=False)
    category = Column(String(50)) # 'UTILITY' | 'MARKETING' | 'TRANSACTIONAL' | 'OTP'
    status = Column(String(50)) # 'APPROVED' | 'PENDING' | 'REJECTED' | 'DRAFT'
    rejected_reason = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    footer = Column(String(500), nullable=True)
    is_archived = Column(Boolean, default=False)
    # Nuevos campos para plantillas con medios
    header_text = Column(String(500), nullable=True)
    media_type = Column(String(20), nullable=True)  # IMAGE, VIDEO, DOCUMENT
    media_id = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)