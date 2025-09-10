from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# =============================================================================
# MODELOS DE BASE DE DATOS (SQLAlchemy)
# =============================================================================

class PaymentUser(Base):
    """Modelo para usuarios con información de pago"""
    __tablename__ = "payment_users"
    
    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    expedition_date = Column(DateTime, nullable=False)  # Fecha de expedición de la cédula
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PaymentReceipt(Base):
    """Modelo para comprobantes de pago"""
    __tablename__ = "payment_receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    cedula = Column(String(20), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)  # Ruta al archivo PDF
    file_name = Column(String(200), nullable=False)  # Nombre del archivo
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relación con el usuario
    user = relationship("PaymentUser", foreign_keys=[cedula], primaryjoin="PaymentReceipt.cedula == PaymentUser.cedula")

# =============================================================================
# MODELOS PYDANTIC (Para API)
# =============================================================================

class PaymentUserCreate(BaseModel):
    """Modelo para crear un usuario de pago"""
    cedula: str
    name: str
    expedition_date: datetime

class PaymentUserUpdate(BaseModel):
    """Modelo para actualizar un usuario de pago"""
    name: Optional[str] = None
    expedition_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class PaymentUserResponse(BaseModel):
    """Modelo para respuesta de usuario de pago"""
    id: int
    cedula: str
    name: str
    expedition_date: datetime
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentReceiptCreate(BaseModel):
    """Modelo para crear un comprobante de pago"""
    cedula: str
    file_path: str
    file_name: str

class PaymentReceiptUpdate(BaseModel):
    """Modelo para actualizar un comprobante de pago"""
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    is_active: Optional[bool] = None

class PaymentReceiptResponse(BaseModel):
    """Modelo para respuesta de comprobante de pago"""
    id: int
    cedula: str
    file_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ReceiptSearchRequest(BaseModel):
    """Modelo para búsqueda de comprobantes"""
    cedula: str
    expedition_date: datetime

class ReceiptSearchResponse(BaseModel):
    """Modelo para respuesta de búsqueda de comprobantes"""
    success: bool
    message: str
    receipts: Optional[list[PaymentReceiptResponse]] = None
    file_path: Optional[str] = None
