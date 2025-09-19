from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.whatsapp_models import WhatsappUser
from models.contact_models import ContactCreateRequest, ContactUpdateRequest, ContactResponse, ContactListResponse
from middleware.auth import get_current_user
from middleware.permissions import require_permission, require_any_permission
from utils.websocket_manager import manager
from typing import List
import math

router = APIRouter(prefix="/api/contacts", tags=["contacts"])

@router.get("/")
async def get_contacts(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Contactos por página"),
    search: str = Query("", description="Buscar por nombre o teléfono"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.contacts.view"))
):
    """Obtiene la lista de contactos con paginación y búsqueda"""
    try:
        # Construir query base
        query = db.query(WhatsappUser)
        
        # Aplicar filtro de búsqueda si se proporciona
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (WhatsappUser.name.ilike(search_filter)) |
                (WhatsappUser.phone_number.ilike(search_filter))
            )
        
        # Contar total de registros
        total = query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        contacts = query.offset(offset).limit(per_page).all()
        
        # Convertir a modelo de respuesta
        contact_responses = []
        for contact in contacts:
            contact_responses.append(ContactResponse(
                phone_number=contact.phone_number,
                name=contact.name,
                contact_type=contact.contact_type,
                last_interaction=contact.last_interaction.isoformat() if contact.last_interaction else None,
                is_active=contact.is_active
            ))
        
        # Calcular si hay más páginas
        total_pages = math.ceil(total / per_page)
        has_next = page < total_pages
        
        return ContactListResponse(
            contacts=contact_responses,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next
        )
        
    except Exception as e:
        print(f"Error al obtener contactos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener contactos")

@router.post("/bulk")
async def create_contacts_bulk(
    contacts: List[ContactCreateRequest],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.contacts.manage"))
):
    """Crea múltiples contactos de forma masiva (importación)"""
    try:
        results = {
            "created": 0,
            "skipped": 0,
            "errors": [],
            "duplicates": []
        }
        
        for contact in contacts:
            try:
                # Verificar si el contacto ya existe
                existing_contact = db.query(WhatsappUser).filter(
                    WhatsappUser.phone_number == contact.phone_number
                ).first()
                
                if existing_contact:
                    results["skipped"] += 1
                    results["duplicates"].append(f"{contact.phone_number} - {contact.name}")
                    continue
                
                # Crear nuevo contacto
                new_contact = WhatsappUser(
                    phone_number=contact.phone_number,
                    name=contact.name,
                    contact_type=contact.contact_type if hasattr(contact, 'contact_type') else None,
                    is_active=contact.is_active if hasattr(contact, 'is_active') else True
                )
                
                db.add(new_contact)
                results["created"] += 1
                
            except Exception as contact_error:
                results["errors"].append(f"{contact.phone_number}: {str(contact_error)}")
        
        # Confirmar todos los cambios
        db.commit()
        
        # Notificar creación masiva por WebSocket si se crearon contactos
        if results["created"] > 0:
            bulk_notification = {
                "type": "contact_updated",
                "data": {
                    "action": "bulk_created",
                    "count": results["created"]
                }
            }
            await manager.send_message_to_all(bulk_notification)
        
        return {
            "message": f"Importación completada: {results['created']} creados, {results['skipped']} omitidos",
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error en importación masiva: {e}")
        raise HTTPException(status_code=500, detail="Error en importación masiva de contactos")

@router.post("/")
async def create_contact(
    contact: ContactCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.contacts.manage"))
):
    """Crea un nuevo contacto"""
    try:
        # Verificar si el contacto ya existe
        existing_contact = db.query(WhatsappUser).filter(
            WhatsappUser.phone_number == contact.phone_number
        ).first()
        
        if existing_contact:
            raise HTTPException(status_code=400, detail="El contacto ya existe")
        
        # Crear nuevo contacto
        new_contact = WhatsappUser(
            phone_number=contact.phone_number,
            name=contact.name,
            contact_type=contact.contact_type,
            is_active=contact.is_active
        )
        
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        
        # Notificar creación de contacto por WebSocket
        contact_notification = {
            "type": "contact_updated",
            "data": {
                "contact_phone": new_contact.phone_number,
                "action": "created",
                "contact": {
                    "phone_number": new_contact.phone_number,
                    "name": new_contact.name,
                    "is_active": new_contact.is_active
                }
            }
        }
        await manager.send_message_to_all(contact_notification)
        
        return {
            "message": "Contacto creado exitosamente",
            "contact": {
                "phone_number": new_contact.phone_number,
                "name": new_contact.name,
                "is_active": new_contact.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al crear contacto: {e}")
        raise HTTPException(status_code=500, detail="Error al crear contacto")

@router.put("/{phone_number}")
async def update_contact(
    phone_number: str,
    contact_update: ContactUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.contacts.manage"))
):
    """Actualiza un contacto existente"""
    try:
        contact = db.query(WhatsappUser).filter(
            WhatsappUser.phone_number == phone_number
        ).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        # Actualizar campos si se proporcionan
        if contact_update.name is not None:
            contact.name = contact_update.name
        if contact_update.contact_type is not None:
            contact.contact_type = contact_update.contact_type
        if contact_update.is_active is not None:
            contact.is_active = contact_update.is_active
        
        db.commit()
        db.refresh(contact)
        
        # Notificar actualización de contacto por WebSocket
        contact_notification = {
            "type": "contact_updated",
            "data": {
                "contact_phone": contact.phone_number,
                "action": "updated",
                "contact": {
                    "phone_number": contact.phone_number,
                    "name": contact.name,
                    "is_active": contact.is_active
                }
            }
        }
        await manager.send_message_to_all(contact_notification)
        
        return {
            "message": "Contacto actualizado exitosamente",
            "contact": {
                "phone_number": contact.phone_number,
                "name": contact.name,
                "is_active": contact.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al actualizar contacto: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar contacto")

@router.delete("/{phone_number}")
async def delete_contact(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.contacts.manage"))
):
    """Elimina un contacto"""
    try:
        contact = db.query(WhatsappUser).filter(
            WhatsappUser.phone_number == phone_number
        ).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        # Guardar datos del contacto antes de eliminarlo
        contact_data = {
            "phone_number": contact.phone_number,
            "name": contact.name,
            "is_active": contact.is_active
        }
        
        db.delete(contact)
        db.commit()
        
        # Notificar eliminación de contacto por WebSocket
        contact_notification = {
            "type": "contact_updated",
            "data": {
                "contact_phone": contact_data["phone_number"],
                "action": "deleted",
                "contact": contact_data
            }
        }
        await manager.send_message_to_all(contact_notification)
        
        return {"message": "Contacto eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al eliminar contacto: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar contacto")

@router.get("/{phone_number}")
async def get_contact(
    phone_number: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.contacts.view"))
):
    """Obtiene un contacto específico"""
    try:
        contact = db.query(WhatsappUser).filter(
            WhatsappUser.phone_number == phone_number
        ).first()
        
        if not contact:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        return ContactResponse(
            phone_number=contact.phone_number,
            name=contact.name,
            contact_type=contact.contact_type,
            last_interaction=contact.last_interaction.isoformat() if contact.last_interaction else None,
            is_active=contact.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al obtener contacto: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener contacto")
