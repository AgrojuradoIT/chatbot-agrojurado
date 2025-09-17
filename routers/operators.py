from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.payment_models import PaymentUser, PaymentUserCreate, PaymentUserUpdate, PaymentUserResponse
from middleware.auth import get_current_user
from middleware.permissions import require_permission, require_any_permission
from utils.websocket_manager import manager
from typing import List
import math
from datetime import datetime

router = APIRouter(prefix="/api/operators", tags=["operators"])

@router.get("/")
async def get_operators(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Operarios por página"),
    search: str = Query("", description="Buscar por nombre o cédula"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.operators.view"))
):
    """Obtiene la lista de operarios con paginación y búsqueda"""
    try:
        # Construir query base
        query = db.query(PaymentUser)
        
        # Aplicar filtro de búsqueda si se proporciona
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (PaymentUser.name.ilike(search_filter)) |
                (PaymentUser.cedula.ilike(search_filter))
            )
        
        # Contar total de registros
        total = query.count()
        
        # Aplicar paginación
        offset = (page - 1) * per_page
        operators = query.offset(offset).limit(per_page).all()
        
        # Convertir a modelo de respuesta
        operator_responses = []
        for operator in operators:
            operator_responses.append(PaymentUserResponse(
                id=operator.id,
                cedula=operator.cedula,
                name=operator.name,
                expedition_date=operator.expedition_date,
                is_active=operator.is_active,
                created_at=operator.created_at
            ))
        
        # Calcular si hay más páginas
        total_pages = math.ceil(total / per_page)
        has_next = page < total_pages
        
        return {
            "operators": operator_responses,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": has_next
        }
        
    except Exception as e:
        print(f"Error al obtener operarios: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener operarios")

@router.post("/bulk")
async def create_operators_bulk(
    operators: List[PaymentUserCreate],
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.operators.manage"))
):
    """Crea múltiples operarios de forma masiva (importación)"""
    try:
        results = {
            "created": 0,
            "skipped": 0,
            "errors": [],
            "duplicates": []
        }
        
        for operator in operators:
            try:
                # Verificar si el operario ya existe
                existing_operator = db.query(PaymentUser).filter(
                    PaymentUser.cedula == operator.cedula
                ).first()
                
                if existing_operator:
                    results["skipped"] += 1
                    results["duplicates"].append(f"{operator.cedula} - {operator.name}")
                    continue
                
                # Crear nuevo operario
                new_operator = PaymentUser(
                    cedula=operator.cedula,
                    name=operator.name,
                    expedition_date=operator.expedition_date,
                    is_active=True
                )
                
                db.add(new_operator)
                results["created"] += 1
                
            except Exception as operator_error:
                results["errors"].append(f"{operator.cedula}: {str(operator_error)}")
        
        # Confirmar todos los cambios
        db.commit()
        
        # Notificar creación masiva por WebSocket si se crearon operarios
        if results["created"] > 0:
            bulk_notification = {
                "type": "operator_updated",
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
        raise HTTPException(status_code=500, detail="Error en importación masiva de operarios")

@router.post("/", response_model=PaymentUserResponse)
async def create_operator(
    operator: PaymentUserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.operators.manage"))
):
    """Crea un nuevo operario"""
    try:
        # Verificar si el operario ya existe
        existing_operator = db.query(PaymentUser).filter(
            PaymentUser.cedula == operator.cedula
        ).first()
        
        if existing_operator:
            raise HTTPException(status_code=400, detail="El operario ya existe")
        
        # Crear nuevo operario
        new_operator = PaymentUser(
            cedula=operator.cedula,
            name=operator.name,
            expedition_date=operator.expedition_date,
            is_active=True
        )
        
        db.add(new_operator)
        db.commit()
        db.refresh(new_operator)
        
        # Notificar creación de operario por WebSocket
        operator_notification = {
            "type": "operator_updated",
            "data": {
                "operator_cedula": new_operator.cedula,
                "action": "created",
                "operator": {
                    "id": new_operator.id,
                    "cedula": new_operator.cedula,
                    "name": new_operator.name,
                    "expedition_date": new_operator.expedition_date.isoformat(),
                    "is_active": new_operator.is_active
                }
            }
        }
        await manager.send_message_to_all(operator_notification)
        
        return new_operator
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al crear operario: {e}")
        raise HTTPException(status_code=500, detail="Error al crear operario")

@router.put("/{cedula}", response_model=PaymentUserResponse)
async def update_operator(
    cedula: str,
    operator_update: PaymentUserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.operators.manage"))
):
    """Actualiza un operario existente"""
    try:
        operator = db.query(PaymentUser).filter(
            PaymentUser.cedula == cedula
        ).first()
        
        if not operator:
            raise HTTPException(status_code=404, detail="Operario no encontrado")
        
        # Actualizar campos si se proporcionan
        if operator_update.name is not None:
            operator.name = operator_update.name
        if operator_update.expedition_date is not None:
            operator.expedition_date = operator_update.expedition_date
        if operator_update.is_active is not None:
            operator.is_active = operator_update.is_active
        
        db.commit()
        db.refresh(operator)
        
        # Notificar actualización de operario por WebSocket
        operator_notification = {
            "type": "operator_updated",
            "data": {
                "operator_cedula": operator.cedula,
                "action": "updated",
                "operator": {
                    "id": operator.id,
                    "cedula": operator.cedula,
                    "name": operator.name,
                    "expedition_date": operator.expedition_date.isoformat(),
                    "is_active": operator.is_active
                }
            }
        }
        await manager.send_message_to_all(operator_notification)
        
        return operator
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al actualizar operario: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar operario")

@router.delete("/{cedula}")
async def delete_operator(
    cedula: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.operators.manage"))
):
    """Elimina un operario de la base de datos."""
    try:
        operator = db.query(PaymentUser).filter(
            PaymentUser.cedula == cedula
        ).first()
        
        if not operator:
            raise HTTPException(status_code=404, detail="Operario no encontrado")
        
        # Guardar datos del operario antes de eliminarlo para notificar
        operator_data = {
            "id": operator.id,
            "cedula": operator.cedula,
            "name": operator.name,
            "expedition_date": operator.expedition_date.isoformat() if operator.expedition_date else None,
            "is_active": operator.is_active
        }
        
        # Eliminación definitiva
        db.delete(operator)
        db.commit()
        
        # Notificar eliminación de operario por WebSocket
        operator_notification = {
            "type": "operator_updated",
            "data": {
                "operator_cedula": operator_data["cedula"],
                "action": "deleted",
                "operator": operator_data
            }
        }
        await manager.send_message_to_all(operator_notification)
        
        return {"message": "Operario eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al eliminar operario: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar operario")

@router.get("/{cedula}", response_model=PaymentUserResponse)
async def get_operator(
    cedula: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("chatbot.operators.view"))
):
    """Obtiene un operario específico"""
    try:
        operator = db.query(PaymentUser).filter(
            PaymentUser.cedula == cedula
        ).first()
        
        if not operator:
            raise HTTPException(status_code=404, detail="Operario no encontrado")
        
        return PaymentUserResponse(
            id=operator.id,
            cedula=operator.cedula,
            name=operator.name,
            expedition_date=operator.expedition_date,
            is_active=operator.is_active,
            created_at=operator.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al obtener operario: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener operario")