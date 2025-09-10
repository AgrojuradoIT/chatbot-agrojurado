"""
Módulo de usuarios de WhatsApp Business API
Contiene funciones para gestión de usuarios en la base de datos
"""

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.whatsapp_models import WhatsappUser

def create_or_update_whatsapp_user(db: Session, phone_number: str, name: str = None):
    """
    Crea o actualiza un usuario de WhatsApp en la base de datos.
    Respeta los nombres manuales establecidos.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono del usuario
        name: Nombre del usuario (opcional)
    
    Returns:
        WhatsappUser: Usuario creado o actualizado
    """
    user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
    if user:
        user.last_interaction = func.now()
        # Solo actualizar el nombre si el usuario no tiene un nombre personalizado
        # o si el nombre actual es igual al número de teléfono (nombre por defecto)
        if name and (user.name == phone_number or user.name == user.phone_number):
            user.name = name
        # Si el usuario ya tiene un nombre personalizado, mantenerlo
    else:
        user = WhatsappUser(
            phone_number=phone_number,
            name=name if name else phone_number, # Usar el número como nombre si no se proporciona uno
            last_interaction=func.now()
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_all_whatsapp_users(db: Session):
    """
    Obtiene todos los usuarios de WhatsApp de la base de datos.
    
    Args:
        db: Sesión de base de datos
    
    Returns:
        List[WhatsappUser]: Lista de todos los usuarios
    """
    return db.query(WhatsappUser).all()

def get_whatsapp_user_by_phone(db: Session, phone_number: str):
    """
    Obtiene un usuario de WhatsApp por número de teléfono.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono del usuario
    
    Returns:
        WhatsappUser: Usuario encontrado o None
    """
    return db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()

def update_user_last_interaction(db: Session, phone_number: str):
    """
    Actualiza la última interacción de un usuario.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono del usuario
    
    Returns:
        bool: True si se actualizó exitosamente
    """
    try:
        user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
        if user:
            user.last_interaction = func.now()
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"❌ Error al actualizar última interacción: {e}")
        db.rollback()
        return False

def delete_whatsapp_user(db: Session, phone_number: str):
    """
    Elimina un usuario de WhatsApp de la base de datos.
    
    Args:
        db: Sesión de base de datos
        phone_number: Número de teléfono del usuario
    
    Returns:
        bool: True si se eliminó exitosamente
    """
    try:
        user = db.query(WhatsappUser).filter(WhatsappUser.phone_number == phone_number).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    except Exception as e:
        print(f"❌ Error al eliminar usuario: {e}")
        db.rollback()
        return False
