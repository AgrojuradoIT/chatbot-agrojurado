from pydantic import BaseModel
from typing import List, Optional

class OAuthCallbackRequest(BaseModel):
    """Modelo para el request del callback OAuth"""
    code: str

class AuthResponse(BaseModel):
    """Modelo para la respuesta de autenticación"""
    access_token: str
    user: dict

class UserResponse(BaseModel):
    """Modelo para la respuesta de información del usuario"""
    id: int
    name: str
    email: str
    sector: Optional[str] = None
    roles: List[str]
    permissions: List[str]
