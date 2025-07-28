from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, Boolean, func
from database import Base
from typing import List, Optional

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