from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TemplateRequest(BaseModel):
    """Modelo para crear una nueva plantilla"""
    name: str
    content: str
    category: str = "UTILITY"
    footer: Optional[str] = None

class TemplateResponse(BaseModel):
    """Modelo para la respuesta de plantilla"""
    id: str
    name: str
    status: str
    category: str
    language: str
    components: List[Dict[str, Any]]

class SendTemplateRequest(BaseModel):
    """Modelo para enviar plantilla a contactos"""
    template_name: str
    phone_numbers: List[str]
    parameters: Optional[Dict[str, Any]] = None
    header_parameters: Optional[Dict[str, Any]] = None
    media_id: Optional[str] = None

class TemplateMediaRequest(BaseModel):
    """Modelo para plantillas con medios"""
    name: str
    content: str
    category: str = "UTILITY"
    footer: Optional[str] = None
    media_type: str  # "image", "video", "document"
    media_id: Optional[str] = None
    media_url: Optional[str] = None
