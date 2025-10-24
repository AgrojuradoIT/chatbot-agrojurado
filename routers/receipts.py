"""
Router for payment receipts management
Handles CRUD operations and FTP file management
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import tempfile
from datetime import datetime
from database import get_db
from services.ftp_service import *
from services.ftp_service import _format_file_size, _validate_ftp_credentials
from services.validation_service import ValidationService
from middleware.auth import get_current_user
from middleware.permissions import require_permission, require_any_permission
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.websocket_manager import manager
    

router = APIRouter(prefix="/api/receipts", tags=["receipts"])

@router.get("/list")
async def list_receipts(
    current_user: dict = Depends(require_any_permission(["chatbot.receipts.view", "chatbot.receipts.manage"])),
    db: Session = Depends(get_db)
):
    """
    Lista todos los comprobantes disponibles en ambas carpetas con metadatos reales
    """
    try:
        receipts = []
        ftp_available = True
        
        # Listar archivos en la carpeta 'recientes' con metadatos reales
        try:
            archivos_recientes = list_files_in_directory("recientes", with_metadata=True)
            for archivo_info in archivos_recientes:
                archivo = archivo_info["filename"]
                # Extraer cédula del nombre del archivo
                cedula = extract_cedula_from_filename(archivo)
                
                receipt = {
                    "id": f"recientes_{archivo}",
                    "nombre": archivo,
                    "cedula": cedula,
                    "fecha": archivo_info["date_iso"],  # Fecha real del archivo
                    "carpeta": "recientes",
                    "tamaño": archivo_info["size_formatted"],  # Tamaño real del archivo
                    "ruta": f"recientes/{archivo}"
                }
                receipts.append(receipt)
        except Exception as e:
            print(f"Error listando archivos recientes: {e}")
            if "Network is unreachable" in str(e) or "Connection refused" in str(e):
                ftp_available = False
        
        # Listar archivos en la carpeta 'anteriores' con metadatos reales
        try:
            archivos_anteriores = list_files_in_directory("anteriores", with_metadata=True)
            for archivo_info in archivos_anteriores:
                archivo = archivo_info["filename"]
                # Extraer cédula del nombre del archivo
                cedula = extract_cedula_from_filename(archivo)
                
                receipt = {
                    "id": f"anteriores_{archivo}",
                    "nombre": archivo,
                    "cedula": cedula,
                    "fecha": archivo_info["date_iso"],  # Fecha real del archivo
                    "carpeta": "anteriores",
                    "tamaño": archivo_info["size_formatted"],  # Tamaño real del archivo
                    "ruta": f"anteriores/{archivo}"
                }
                receipts.append(receipt)
        except Exception as e:
            print(f"Error listando archivos anteriores: {e}")
            if "Network is unreachable" in str(e) or "Connection refused" in str(e):
                ftp_available = False
        
        # Sort by date (most recent first)
        receipts.sort(key=lambda x: x["fecha"], reverse=True)
        
        return {
            "success": True,
            "receipts": receipts,
            "total": len(receipts),
            "ftp_available": ftp_available,
            "message": "Servicio FTP no disponible. Mostrando datos en caché." if not ftp_available else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar comprobantes: {str(e)}")


@router.get("/ftp-status")
async def check_ftp_status(
    current_user: dict = Depends(require_any_permission(["chatbot.receipts.view", "chatbot.receipts.manage"]))
):
    """
    Verifica el estado de la conexión FTP y diagnóstica problemas de conectividad
    """
    import socket
    import time
    
    status = {
        "ftp_configured": False,
        "hostname_resolves": False,
        "port_reachable": False,
        "ftp_login_works": False,
        "error_details": [],
        "resolved_ip": None,
        "ftp_host": FTP_HOST
    }
    
    try:
        # Verificar configuración
        if not _validate_ftp_credentials():
            status["error_details"].append("Credenciales FTP no configuradas")
            return status
        status["ftp_configured"] = True
        
        # Verificar resolución DNS
        try:
            resolved_ip = socket.gethostbyname(FTP_HOST)
            status["hostname_resolves"] = True
            status["resolved_ip"] = resolved_ip
        except socket.gaierror as e:
            status["error_details"].append(f"No se puede resolver hostname {FTP_HOST}: {e}")
            return status
        
        # Verificar conectividad de puerto
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((FTP_HOST, 21))
            sock.close()
            
            if result == 0:
                status["port_reachable"] = True
            else:
                status["error_details"].append(f"Puerto 21 no alcanzable en {FTP_HOST} (IP: {resolved_ip})")
                return status
        except Exception as e:
            status["error_details"].append(f"Error probando conectividad: {e}")
            return status
        
        # Verificar login FTP
        try:
            with ftp_connection() as ftp:
                status["ftp_login_works"] = True
        except Exception as e:
            status["error_details"].append(f"Error en login FTP: {e}")
    
    except Exception as e:
        status["error_details"].append(f"Error general: {e}")
    
    return status


@router.post("/upload-multiple")
async def upload_multiple_receipts(
    current_user: dict = Depends(require_permission("chatbot.receipts.manage")),
    files: List[UploadFile] = File(...),
    folder: str = Form(default="recientes"),
    db: Session = Depends(get_db)
):
    """
    Uploads multiple receipts to the specified folder in parallel
    Cédula is extracted from filename automatically
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Validate folder
        if folder not in ["recientes", "anteriores"]:
            raise HTTPException(status_code=400, detail="Invalid folder. Use 'recientes' or 'anteriores'")
        
        # Create a shared thread pool for FTP operations
        # En producción: limitar a 3-5 conexiones concurrentes para estabilidad
        max_workers = min(len(files), 3)  # Limit to 3 concurrent FTP connections for production stability
        print(f"🔍 DEBUG: Usando {max_workers} workers para subidas FTP paralelas (optimizado para producción)")
        
        async def process_single_file(file: UploadFile, executor: ThreadPoolExecutor):
            """Process a single file upload"""
            try:
                # Validate that it's a PDF file
                if not file.filename.lower().endswith('.pdf'):
                    return {
                        "success": False,
                        "filename": file.filename,
                        "error": "Only PDF files are allowed"
                    }
                
                # Extract cedula from filename
                cedula = extract_cedula_from_filename(file.filename)
                print(f"🔍 DEBUG: Archivo: {file.filename}, Cédula extraída: {cedula}")
                
                if cedula == "N/A":
                    return {
                        "success": False,
                        "filename": file.filename,
                        "error": "Could not extract cedula from filename"
                    }
                
                # Generate unique filename preserving original name + timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_without_ext = file.filename.replace('.pdf', '').replace('.PDF', '')
                filename = f"{name_without_ext}_{timestamp}.pdf"
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    # Upload file to FTP using shared thread pool for true parallelism
                    def upload_to_ftp():
                        return upload_file_to_ftp(temp_file_path, folder, filename)
                    
                    # Use shared ThreadPoolExecutor for FTP operations
                    loop = asyncio.get_event_loop()
                    success = await loop.run_in_executor(executor, upload_to_ftp)
                    
                    print(f"🔍 DEBUG: Subiendo archivo {filename} a carpeta {folder}")
                    print(f"🔍 DEBUG: Resultado subida: {success}")
                    
                    # Si falla, intentar una vez más después de un breve delay
                    if not success:
                        print(f"🔄 DEBUG: Reintentando subida de {filename}...")
                        await asyncio.sleep(0.5)  # Esperar 500ms antes del reintento
                        success = await loop.run_in_executor(executor, upload_to_ftp)
                        print(f"🔍 DEBUG: Resultado reintento: {success}")
                    
                    if success:
                        print(f"🔍 DEBUG: Archivo {filename} subido exitosamente")
                        
                        # Emitir evento WebSocket en tiempo real
                        try:
                            # Obtener tamaño del archivo
                            file_size = len(content)
                            file_size_formatted = _format_file_size(file_size)
                            
                            await manager.send_message_to_all({
                                "type": "receipt_uploaded",
                                "data": {
                                    "filename": filename,
                                    "original_filename": file.filename,
                                    "cedula": cedula,
                                    "folder": folder,
                                    "timestamp": datetime.now().isoformat(),
                                    "size": file_size,
                                    "size_formatted": file_size_formatted
                                }
                            })
                        except Exception as ws_error:
                            print(f"⚠️ DEBUG: Error enviando WebSocket: {ws_error}")
                        
                        return {
                            "success": True,
                            "filename": filename,
                            "original_filename": file.filename,
                            "cedula": cedula,
                            "folder": folder
                        }
                    else:
                        print(f"🔍 DEBUG: Error subiendo archivo {filename} después de reintento")
                        return {
                            "success": False,
                            "filename": file.filename,
                            "error": f"Error uploading file to FTP server after retry - check server logs for details"
                        }
                        
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        
            except Exception as e:
                return {
                    "success": False,
                    "filename": file.filename,
                    "error": f"Error processing file: {str(e)}"
                }
        
        # Process files in batches to show real progress
        batch_size = max_workers  # Process in batches equal to max workers
        results = []
        
        print(f"🔍 DEBUG: Procesando {len(files)} archivos en lotes de {batch_size}")
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(files) + batch_size - 1) // batch_size
            
            print(f"🔍 DEBUG: Procesando lote {batch_num}/{total_batches} ({len(batch)} archivos)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                batch_results = await asyncio.gather(*[process_single_file(file, executor) for file in batch])
                results.extend(batch_results)
            
            # Delay between batches: más largo en producción para estabilidad
            if i + batch_size < len(files):
                await asyncio.sleep(0.3)  # 300ms delay para producción
        
        # Separate successful and failed uploads
        uploaded_files = []
        failed_files = []
        
        for result in results:
            if result["success"]:
                uploaded_files.append({
                    "filename": result["filename"],
                    "original_filename": result["original_filename"],
                    "cedula": result["cedula"],
                    "folder": result["folder"]
                })
            else:
                failed_files.append({
                    "filename": result["filename"],
                    "error": result["error"]
                })
        
        # Limpiar caché del directorio donde se subieron los archivos
        if uploaded_files:
            clear_metadata_cache(folder)
        
        print(f"🔍 DEBUG: Subida completada - Exitosos: {len(uploaded_files)}, Fallidos: {len(failed_files)}")
        
        return {
            "success": len(failed_files) == 0,
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "total_uploaded": len(uploaded_files),
            "total_failed": len(failed_files)
        }
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading receipts: {str(e)}")


@router.delete("/delete-batch")
async def delete_receipts_batch(
    request: Request,
    current_user: dict = Depends(require_permission("chatbot.receipts.manage")),
    db: Session = Depends(get_db)
):
    """
    Optimized batch deletion of receipts with parallel processing
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        # Extract data from request body
        data = await request.json()
        ids = data.get("ids", [])
        optimize = data.get("optimize", False)
        
        if not ids:
            raise HTTPException(status_code=400, detail="No receipts specified for deletion")
        
        print(f"🔍 DEBUG: Eliminando {len(ids)} archivos en modo optimizado")
        
        # Create a shared thread pool for FTP operations
        max_workers = min(len(ids), 5)  # Limit to 5 concurrent FTP connections
        
        async def process_single_delete(receipt_id: str, executor: ThreadPoolExecutor):
            """Process a single file deletion"""
            try:
                # Extract folder and filename from ID
                if "_" in receipt_id:
                    folder, filename = receipt_id.split("_", 1)
                    
                    if folder in ["recientes", "anteriores"]:
                        # Use shared ThreadPoolExecutor for FTP operations
                        loop = asyncio.get_event_loop()
                        
                        def delete_from_ftp():
                            return delete_file_from_ftp(folder, filename)
                        
                        success = await loop.run_in_executor(executor, delete_from_ftp)
                        
                        if success:
                            print(f"✅ DEBUG: Archivo {filename} eliminado exitosamente de {folder}")
                            
                            # Emitir evento WebSocket en tiempo real
                            try:
                                await manager.send_message_to_all({
                                    "type": "receipt_deleted",
                                    "data": {
                                        "receipt_id": receipt_id,
                                        "filename": filename,
                                        "folder": folder,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                })
                            except Exception as ws_error:
                                print(f"⚠️ DEBUG: Error enviando WebSocket: {ws_error}")
                            
                            return {
                                "success": True,
                                "receipt_id": receipt_id,
                                "filename": filename,
                                "folder": folder
                            }
                        else:
                            print(f"❌ DEBUG: Error eliminando archivo {filename}")
                            return {
                                "success": False,
                                "receipt_id": receipt_id,
                                "error": f"Error deleting {receipt_id} from {folder}"
                            }
                    else:
                        return {
                            "success": False,
                            "receipt_id": receipt_id,
                            "error": f"Invalid folder for {receipt_id}"
                        }
                else:
                    return {
                        "success": False,
                        "receipt_id": receipt_id,
                        "error": f"Invalid receipt ID: {receipt_id}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "receipt_id": receipt_id,
                    "error": f"Error processing {receipt_id}: {str(e)}"
                }
        
        # Process files in parallel batches
        batch_size = max_workers
        results = []
        
        print(f"🔍 DEBUG: Procesando {len(ids)} archivos en lotes de {batch_size}")
        
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(ids) + batch_size - 1) // batch_size
            
            print(f"🔍 DEBUG: Procesando lote {batch_num}/{total_batches} ({len(batch)} archivos)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                batch_results = await asyncio.gather(*[process_single_delete(receipt_id, executor) for receipt_id in batch])
                results.extend(batch_results)
            
            # Small delay between batches for stability
            if i + batch_size < len(ids):
                await asyncio.sleep(0.2)  # 200ms delay between batches
        
        # Separate successful and failed deletions
        deleted = []
        errors = []
        
        for result in results:
            if result["success"]:
                deleted.append(result["receipt_id"])
            else:
                errors.append(result["error"])
        
        # Limpiar caché de los directorios afectados
        if deleted:
            affected_dirs = set()
            for receipt_id in deleted:
                if "_" in receipt_id:
                    folder = receipt_id.split("_", 1)[0]
                    if folder in ["recientes", "anteriores"]:
                        affected_dirs.add(folder)
            
            for folder in affected_dirs:
                clear_metadata_cache(folder)
        
        print(f"🔍 DEBUG: Eliminación completada - Exitosos: {len(deleted)}, Fallidos: {len(errors)}")
        
        return {
            "success": len(errors) == 0,
            "deleted": deleted,
            "errors": errors,
            "total_deleted": len(deleted),
            "total_errors": len(errors),
            "optimized": optimize
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting receipts: {str(e)}")

@router.post("/move")
async def move_receipts(
    request: Request,
    current_user: dict = Depends(require_permission("chatbot.receipts.manage")),
    db: Session = Depends(get_db)
):
    """
    Moves one or more receipts to another folder in parallel
    """
    try:
        # Extract data from request body
        data = await request.json()
        ids = data.get("ids", [])
        target_folder = data.get("target_folder", "")
        
        if not ids:
            raise HTTPException(status_code=400, detail="No receipts specified for moving")
        
        if target_folder not in ["recientes", "anteriores"]:
            raise HTTPException(status_code=400, detail="Invalid target folder. Use 'recientes' or 'anteriores'")
        
        # Create a shared thread pool for FTP operations
        # Limit to 4 concurrent FTP connections for production stability
        max_workers = min(len(ids), 4)
        print(f"🔍 DEBUG: Moviendo {len(ids)} archivos usando {max_workers} workers paralelos")
        
        async def process_single_move(receipt_id: str, executor: ThreadPoolExecutor):
            """Process a single file move"""
            try:
                # Extract source folder and filename from ID
                if "_" in receipt_id:
                    source_folder, filename = receipt_id.split("_", 1)
                    
                    if source_folder in ["recientes", "anteriores"]:
                        if source_folder != target_folder:
                            # Use shared ThreadPoolExecutor for FTP operations
                            loop = asyncio.get_event_loop()
                            
                            def move_to_ftp():
                                return move_file_in_ftp(source_folder, target_folder, filename)
                            
                            success = await loop.run_in_executor(executor, move_to_ftp)
                            
                            if success:
                                print(f"✅ DEBUG: Archivo {filename} movido exitosamente de {source_folder} a {target_folder}")
                                
                                # Emitir evento WebSocket en tiempo real
                                try:
                                    await manager.send_message_to_all({
                                        "type": "receipt_moved",
                                        "data": {
                                            "receipt_id": receipt_id,
                                            "filename": filename,
                                            "source_folder": source_folder,
                                            "target_folder": target_folder,
                                            "timestamp": datetime.now().isoformat()
                                        }
                                    })
                                except Exception as ws_error:
                                    print(f"⚠️ DEBUG: Error enviando WebSocket: {ws_error}")
                                
                                return {
                                    "success": True,
                                    "receipt_id": receipt_id,
                                    "filename": filename,
                                    "source_folder": source_folder,
                                    "target_folder": target_folder
                                }
                            else:
                                print(f"❌ DEBUG: Error moviendo archivo {filename}")
                                return {
                                    "success": False,
                                    "receipt_id": receipt_id,
                                    "error": f"Error moving {receipt_id} to {target_folder}"
                                }
                        else:
                            return {
                                "success": False,
                                "receipt_id": receipt_id,
                                "error": f"Receipt {receipt_id} is already in the target folder"
                            }
                    else:
                        return {
                            "success": False,
                            "receipt_id": receipt_id,
                            "error": f"Invalid source folder for {receipt_id}"
                        }
                else:
                    return {
                        "success": False,
                        "receipt_id": receipt_id,
                        "error": f"Invalid receipt ID: {receipt_id}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "receipt_id": receipt_id,
                    "error": f"Error processing {receipt_id}: {str(e)}"
                }
        
        # Process files in batches to show real progress
        batch_size = max_workers  # Process in batches equal to max workers
        results = []
        
        print(f"🔍 DEBUG: Procesando {len(ids)} archivos en lotes de {batch_size}")
        
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(ids) + batch_size - 1) // batch_size
            
            print(f"🔍 DEBUG: Procesando lote {batch_num}/{total_batches} ({len(batch)} archivos)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                batch_results = await asyncio.gather(*[process_single_move(receipt_id, executor) for receipt_id in batch])
                results.extend(batch_results)
            
            # Delay between batches for stability
            if i + batch_size < len(ids):
                await asyncio.sleep(0.2)  # 200ms delay between batches
        
        # Separate successful and failed moves
        moved = []
        errors = []
        
        for result in results:
            if result["success"]:
                moved.append(result["receipt_id"])
            else:
                errors.append(result["error"])
        
        # Limpiar caché de los directorios afectados
        if moved:
            affected_dirs = set()
            for receipt_id in moved:
                if "_" in receipt_id:
                    source_folder = receipt_id.split("_", 1)[0]
                    if source_folder in ["recientes", "anteriores"]:
                        affected_dirs.add(source_folder)
                        affected_dirs.add(target_folder)
            
            for folder in affected_dirs:
                clear_metadata_cache(folder)
        
        print(f"🔍 DEBUG: Movimiento completado - Exitosos: {len(moved)}, Fallidos: {len(errors)}")
        
        return {
            "success": len(errors) == 0,
            "moved": moved,
            "errors": errors,
            "total_moved": len(moved),
            "total_errors": len(errors),
            "target_folder": target_folder
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error moving receipts: {str(e)}")

@router.get("/download/{receipt_id}")
async def download_receipt(
    receipt_id: str,
    current_user: dict = Depends(require_any_permission(["chatbot.receipts.view", "chatbot.receipts.manage"])),
    db: Session = Depends(get_db)
):
    """
    Downloads a specific receipt
    """
    try:
        # Extract folder and filename from ID
        if "_" in receipt_id:
            folder, filename = receipt_id.split("_", 1)
            
            if folder not in ["recientes", "anteriores"]:
                raise HTTPException(status_code=400, detail="Invalid folder")
            
            # Create temporary file for download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file_path = temp_file.name
            
            try:
                # Download file from FTP
                success = download_file_from_ftp(folder, filename, temp_file_path)
                
                if not success:
                    raise HTTPException(status_code=404, detail="File not found")
                
                # Read file content
                with open(temp_file_path, 'rb') as f:
                    content = f.read()
                
                # Clean up temporary file
                os.unlink(temp_file_path)
                
                # Return file as response
                from fastapi.responses import Response
                return Response(
                    content=content,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}"
                    }
                )
                
            except Exception as e:
                # Clean up temporary file in case of error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise e
        else:
            raise HTTPException(status_code=400, detail="Invalid receipt ID")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading receipt: {str(e)}")


@router.post("/clear-cache")
async def clear_receipts_cache(
    current_user: dict = Depends(require_permission("chatbot.receipts.manage")),
    subdir: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Limpia el caché de metadatos de archivos para forzar la actualización de datos
    """
    try:
        clear_metadata_cache(subdir)
        
        return {
            "success": True,
            "message": f"Cache cleared for {'all directories' if subdir is None else subdir}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


# Helper functions
def extract_cedula_from_filename(filename: str) -> str:
    """
    Extracts cedula from filename, avoiding timestamps and other non-cedula numbers
    """
    import re
    from datetime import datetime
    
    # Remove extension
    name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
    
    # Find all numbers in the filename
    numbers = re.findall(r'\d+', name_without_ext)
    
    if not numbers:
        return "N/A"
    
    # Filter out timestamps and other non-cedula patterns
    valid_cedulas = []
    
    for number in numbers:
        # Skip if it looks like a timestamp (YYYYMMDD format)
        if len(number) == 8 and number.isdigit():
            try:
                # Check if it's a valid date (YYYYMMDD)
                year = int(number[:4])
                month = int(number[4:6])
                day = int(number[6:8])
                if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                    continue  # Skip this number as it's likely a timestamp
            except (ValueError, IndexError):
                pass
        
        # Skip if it looks like a time (HHMMSS format)
        if len(number) == 6 and number.isdigit():
            try:
                hour = int(number[:2])
                minute = int(number[2:4])
                second = int(number[4:6])
                if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                    continue  # Skip this number as it's likely a time
            except (ValueError, IndexError):
                pass
        
        # Skip very short numbers (likely not cedulas)
        if len(number) < 6:
            continue
            
        # Skip very long numbers (likely not cedulas)
        if len(number) > 12:
            continue
        
        # This number could be a cedula
        valid_cedulas.append(number)
    
    if not valid_cedulas:
        return "N/A"
    
    # Return the cedula that looks most like a real cedula
    # Priority: 7-10 digits, with preference for 8-10 digits
    for cedula in sorted(valid_cedulas, key=len, reverse=True):
        if 8 <= len(cedula) <= 10:
            return cedula
    
    # If no 8-10 digit cedula found, return the longest valid one
    return max(valid_cedulas, key=len)

# Las funciones _obtener_fecha_archivo y _obtener_tamaño_archivo han sido reemplazadas
# por get_files_with_metadata que obtiene los datos reales del servidor FTP
