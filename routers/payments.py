from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models.payment_models import (
    PaymentUserCreate, PaymentUserResponse, PaymentUserUpdate,
    PaymentReceiptCreate, PaymentReceiptResponse, PaymentReceiptUpdate,
    ReceiptSearchRequest, ReceiptSearchResponse
)
from services.receipt_service import ReceiptService
from services.validation_service import ValidationService
from typing import List
import os
import shutil
from datetime import datetime
from services.ftp_service import upload_file as ftp_upload, list_files_in_directory as ftp_list, find_files_by_cedula as ftp_find_by_cedula, rename_file as ftp_rename, move_file as ftp_move, delete_file as ftp_delete

router = APIRouter(prefix="/api/payments", tags=["payments"])

# =============================================================================
# ENDPOINTS PARA USUARIOS
# =============================================================================

@router.post("/users", response_model=PaymentUserResponse)
async def create_payment_user(
    user_data: PaymentUserCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo usuario de pago"""
    success, message, user = ReceiptService.create_user(
        db=db,
        cedula=user_data.cedula,
        name=user_data.name,
        expedition_date_str=user_data.expedition_date.strftime("%d/%m/%Y")
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return user

@router.get("/users", response_model=List[PaymentUserResponse])
async def get_payment_users(db: Session = Depends(get_db)):
    """Obtiene todos los usuarios de pago"""
    from models.payment_models import PaymentUser
    users = db.query(PaymentUser).filter(PaymentUser.is_active == True).all()
    return users

@router.get("/users/{cedula}", response_model=PaymentUserResponse)
async def get_payment_user(cedula: str, db: Session = Depends(get_db)):
    """Obtiene un usuario de pago por cédula"""
    from models.payment_models import PaymentUser
    user = db.query(PaymentUser).filter(
        PaymentUser.cedula == cedula,
        PaymentUser.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return user

@router.put("/users/{cedula}", response_model=PaymentUserResponse)
async def update_payment_user(
    cedula: str,
    user_data: PaymentUserUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un usuario de pago"""
    from models.payment_models import PaymentUser
    
    user = db.query(PaymentUser).filter(
        PaymentUser.cedula == cedula,
        PaymentUser.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos proporcionados
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.expedition_date is not None:
        user.expedition_date = user_data.expedition_date
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{cedula}")
async def delete_payment_user(cedula: str, db: Session = Depends(get_db)):
    """Elimina (desactiva) un usuario de pago"""
    from models.payment_models import PaymentUser
    
    user = db.query(PaymentUser).filter(
        PaymentUser.cedula == cedula,
        PaymentUser.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user.is_active = False
    db.commit()
    
    return {"message": "Usuario eliminado exitosamente"}

# =============================================================================
# ENDPOINTS PARA COMPROBANTES
# =============================================================================

@router.post("/receipts", response_model=PaymentReceiptResponse)
async def create_payment_receipt(
    receipt_data: PaymentReceiptCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo comprobante de pago"""
    success, message, receipt = ReceiptService.create_receipt(
        db=db,
        cedula=receipt_data.cedula,
        file_path=receipt_data.file_path,
        file_name=receipt_data.file_name
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return receipt

@router.post("/receipts/upload")
async def upload_receipt_file(
    file: UploadFile = File(...),
    cedula: str = None,
    folder: str = "recientes",  # "recientes" o "anteriores"
    db: Session = Depends(get_db)
):
    """Sube un archivo PDF de comprobante y lo registra en la base de datos"""
    
    # Validar que sea un PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    # Validar carpeta
    if folder not in ["recientes", "anteriores"]:
        raise HTTPException(status_code=400, detail="folder debe ser 'recientes' o 'anteriores'")
    
    # Crear directorio si no existe
    upload_dir = f"static/receipts/{folder}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generar nombre único para el archivo
    # Formato: CONSECUTIVO_CEDULA.pdf
    # Obtener el siguiente consecutivo disponible
    existing_files = [f for f in os.listdir(upload_dir) if f.endswith('.pdf')]
    consecutivos = []
    
    for file in existing_files:
        if file.endswith(f"_{cedula}.pdf"):
            try:
                consecutivo = int(file.split('_')[0])
                consecutivos.append(consecutivo)
            except (ValueError, IndexError):
                continue
    
    next_consecutivo = max(consecutivos) + 1 if consecutivos else 1
    new_filename = f"{next_consecutivo:04d}_{cedula}.pdf"
    file_path = os.path.join(upload_dir, new_filename)
    
    # Guardar archivo localmente
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")
    
    # Validar parámetros requeridos
    if not cedula:
        raise HTTPException(status_code=400, detail="cedula es requerido")
    
    # Si hay configuración FTP, subir al hosting y usar URL pública o ruta remota
    public_url, remote_path = ftp_upload(file_path, folder, new_filename)
    stored_path = public_url if public_url else (remote_path if remote_path else file_path)

    # Crear comprobante en la base de datos
    success, message, receipt = ReceiptService.create_receipt(
        db=db,
        cedula=cedula,
        file_path=stored_path,
        file_name=new_filename
    )
    
    if not success:
        # Eliminar archivo si falló la creación en BD
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=message)

    # Si se subió a FTP, borrar la copia local para no persistir
    if (public_url or remote_path) and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    
    return {
        "message": "Comprobante subido exitosamente",
        "receipt": receipt,
        "file_path": stored_path
    }


# =====================
# Gestión vía FTP
# =====================

@router.get("/receipts/files")
async def list_receipt_files(folder: str):
    if folder not in ["recientes", "anteriores"]:
        raise HTTPException(status_code=400, detail="folder debe ser 'recientes' o 'anteriores'")
    files = ftp_list(folder)
    return {"folder": folder, "files": files}


@router.put("/receipts/{receipt_id}/rename", response_model=PaymentReceiptResponse)
async def rename_receipt(receipt_id: int, new_name: str, db: Session = Depends(get_db)):
    from models.payment_models import PaymentReceipt
    receipt = db.query(PaymentReceipt).filter(PaymentReceipt.id == receipt_id, PaymentReceipt.is_active == True).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")

    # Determinar folder por la ruta
    folder = "recientes" if "/recientes/" in receipt.file_path else "anteriores"
    old_name = receipt.file_name
    if not new_name.lower().endswith('.pdf'):
        new_name += '.pdf'

    ok = ftp_rename(folder, old_name, new_name)
    if not ok:
        raise HTTPException(status_code=500, detail="No fue posible renombrar el archivo en el hosting")

    # Actualizar BD
    receipt.file_name = new_name
    # Reemplazar el nombre al final de file_path
    receipt.file_path = receipt.file_path.rsplit('/', 1)[0] + '/' + new_name
    db.commit()
    db.refresh(receipt)
    return receipt


@router.put("/receipts/{receipt_id}/move", response_model=PaymentReceiptResponse)
async def move_receipt(receipt_id: int, target_folder: str, db: Session = Depends(get_db)):
    if target_folder not in ["recientes", "anteriores"]:
        raise HTTPException(status_code=400, detail="target_folder debe ser 'recientes' o 'anteriores'")

    from models.payment_models import PaymentReceipt
    receipt = db.query(PaymentReceipt).filter(PaymentReceipt.id == receipt_id, PaymentReceipt.is_active == True).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")

    current_folder = "recientes" if "/recientes/" in receipt.file_path else "anteriores"
    if current_folder == target_folder:
        return receipt

    new_remote_path = ftp_move(current_folder, target_folder, receipt.file_name)
    if not new_remote_path:
        raise HTTPException(status_code=500, detail="No fue posible mover el archivo en el hosting")

    # Actualizar BD
    receipt.file_path = new_remote_path if new_remote_path.startswith('/') else receipt.file_path.replace('/'+current_folder+'/', '/'+target_folder+'/')
    db.commit()
    db.refresh(receipt)
    return receipt


@router.delete("/receipts/{receipt_id}")
async def delete_receipt_hosting(receipt_id: int, db: Session = Depends(get_db)):
    from models.payment_models import PaymentReceipt
    receipt = db.query(PaymentReceipt).filter(PaymentReceipt.id == receipt_id, PaymentReceipt.is_active == True).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")

    folder = "recientes" if "/recientes/" in receipt.file_path else "anteriores"
    ok = ftp_delete(folder, receipt.file_name)
    if not ok:
        raise HTTPException(status_code=500, detail="No fue posible eliminar el archivo en el hosting")

    # Marcar inactivo en BD
    receipt.is_active = False
    db.commit()
    return {"message": "Comprobante eliminado exitosamente"}

@router.get("/receipts", response_model=List[PaymentReceiptResponse])
async def get_payment_receipts(
    cedula: str = None,
    db: Session = Depends(get_db)
):
    """Obtiene comprobantes de pago (opcionalmente filtrados por cédula)"""
    from models.payment_models import PaymentReceipt
    
    query = db.query(PaymentReceipt).filter(PaymentReceipt.is_active == True)
    
    if cedula:
        query = query.filter(PaymentReceipt.cedula == cedula)
    
    receipts = query.order_by(PaymentReceipt.payment_date.desc()).all()
    return receipts

@router.get("/receipts/{receipt_id}", response_model=PaymentReceiptResponse)
async def get_payment_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Obtiene un comprobante de pago específico"""
    from models.payment_models import PaymentReceipt
    
    receipt = db.query(PaymentReceipt).filter(
        PaymentReceipt.id == receipt_id,
        PaymentReceipt.is_active == True
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    return receipt

@router.put("/receipts/{receipt_id}", response_model=PaymentReceiptResponse)
async def update_payment_receipt(
    receipt_id: int,
    receipt_data: PaymentReceiptUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un comprobante de pago"""
    from models.payment_models import PaymentReceipt
    
    receipt = db.query(PaymentReceipt).filter(
        PaymentReceipt.id == receipt_id,
        PaymentReceipt.is_active == True
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    # Actualizar campos proporcionados
    if receipt_data.payment_date is not None:
        receipt.payment_date = receipt_data.payment_date
    if receipt_data.file_path is not None:
        receipt.file_path = receipt_data.file_path
    if receipt_data.file_name is not None:
        receipt.file_name = receipt_data.file_name
    if receipt_data.amount is not None:
        receipt.amount = receipt_data.amount
    if receipt_data.description is not None:
        receipt.description = receipt_data.description
    if receipt_data.is_active is not None:
        receipt.is_active = receipt_data.is_active
    
    db.commit()
    db.refresh(receipt)
    return receipt

@router.delete("/receipts/{receipt_id}")
async def delete_payment_receipt(receipt_id: int, db: Session = Depends(get_db)):
    """Elimina (desactiva) un comprobante de pago"""
    from models.payment_models import PaymentReceipt
    
    receipt = db.query(PaymentReceipt).filter(
        PaymentReceipt.id == receipt_id,
        PaymentReceipt.is_active == True
    ).first()
    
    if not receipt:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    
    receipt.is_active = False
    db.commit()
    
    return {"message": "Comprobante eliminado exitosamente"}

# =============================================================================
# ENDPOINTS PARA BÚSQUEDA Y ENVÍO
# =============================================================================

@router.post("/search", response_model=ReceiptSearchResponse)
async def search_receipts(
    search_data: ReceiptSearchRequest,
    db: Session = Depends(get_db)
):
    """Busca comprobantes de un usuario"""
    success, message, receipts = ReceiptService.get_user_receipts(
        db=db,
        cedula=search_data.cedula,
        expedition_date_str=search_data.expedition_date.strftime("%d/%m/%Y")
    )
    
    return ReceiptSearchResponse(
        success=success,
        message=message,
        receipts=receipts if success else None
    )

@router.post("/send/{phone_number}")
async def send_receipt_to_phone(
    phone_number: str,
    search_data: ReceiptSearchRequest,
    db: Session = Depends(get_db)
):
    """Envía un comprobante de pago por WhatsApp"""
    success, message = ReceiptService.search_and_send_receipt(
        db=db,
        cedula=search_data.cedula,
        expedition_date_str=search_data.expedition_date.strftime("%d/%m/%Y"),
        phone_number=phone_number
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}

# =============================================================================
# ENDPOINTS DE VALIDACIÓN
# =============================================================================

@router.post("/validate/cedula")
async def validate_cedula(cedula: str):
    """Valida el formato de una cédula"""
    is_valid, message = ValidationService.validate_cedula_format(cedula)
    return {
        "is_valid": is_valid,
        "message": message,
        "cedula": cedula
    }

@router.post("/validate/date")
async def validate_date(date_str: str):
    """Valida el formato de una fecha DD/MM/AAAA"""
    is_valid, message, date_obj = ValidationService.validate_date_format(date_str)
    return {
        "is_valid": is_valid,
        "message": message,
        "date_str": date_str,
        "date_obj": date_obj.isoformat() if date_obj else None
    }
