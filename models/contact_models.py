from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from models.whatsapp_models import VALID_CONTACT_TYPES

class ContactCreateRequest(BaseModel):
    """Modelo para crear un nuevo contacto"""
    phone_number: str
    name: str
    contact_type: Optional[str] = None
    is_active: bool = True
    
    @validator('contact_type')
    def validate_contact_type(cls, v):
        if v is not None and v not in VALID_CONTACT_TYPES:
            raise ValueError(f'Tipo de contacto inválido. Opciones válidas: {", ".join(VALID_CONTACT_TYPES)}')
        return v

class ContactUpdateRequest(BaseModel):
    """Modelo para actualizar un contacto"""
    name: Optional[str] = None
    contact_type: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('contact_type')
    def validate_contact_type(cls, v):
        if v is not None and v not in VALID_CONTACT_TYPES:
            raise ValueError(f'Tipo de contacto inválido. Opciones válidas: {", ".join(VALID_CONTACT_TYPES)}')
        return v

class ContactResponse(BaseModel):
    """Modelo para la respuesta de contacto"""
    phone_number: str
    name: str
    contact_type: Optional[str] = None
    last_interaction: Optional[str] = None
    is_active: bool

class ContactListResponse(BaseModel):
    """Modelo para la lista de contactos con paginación"""
    contacts: list[ContactResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
