from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ContactCreateRequest(BaseModel):
    """Modelo para crear un nuevo contacto"""
    phone_number: str
    name: str
    is_active: bool = True

class ContactUpdateRequest(BaseModel):
    """Modelo para actualizar un contacto"""
    name: Optional[str] = None
    is_active: Optional[bool] = None

class ContactResponse(BaseModel):
    """Modelo para la respuesta de contacto"""
    phone_number: str
    name: str
    last_interaction: Optional[str] = None
    is_active: bool

class ContactListResponse(BaseModel):
    """Modelo para la lista de contactos con paginación"""
    contacts: list[ContactResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
