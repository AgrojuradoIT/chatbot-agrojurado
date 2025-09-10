import os
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from models.payment_models import PaymentReceipt, PaymentUser
from services.validation_service import ValidationService
from services.whatsapp_service import send_whatsapp_document, send_whatsapp_message, send_whatsapp_document_url, send_whatsapp_interactive_buttons

class ReceiptService:
    """Servicio para manejar comprobantes de pago"""
    
    @staticmethod
    def search_and_send_receipt(
        db: Session, 
        cedula: str, 
        expedition_date_str: str, 
        phone_number: str
    ) -> Tuple[bool, str]:
        """
        Busca y envía un comprobante de pago según el flujo del diagrama
        
        Args:
            db: Sesión de base de datos
            cedula: Número de cédula
            expedition_date_str: Fecha de expedición en formato DD/MM/AAAA
            phone_number: Número de teléfono para enviar el PDF
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        # Paso 1: Validar formato de cédula
        is_valid_cedula, cedula_message = ValidationService.validate_cedula_format(cedula)
        if not is_valid_cedula:
            return False, cedula_message
        
        # Paso 2: Validar formato de fecha (solo para validación, no para búsqueda)
        is_valid_date, date_message, expedition_date = ValidationService.validate_date_format(expedition_date_str)
        if not is_valid_date:
            return False, date_message
        
        # Paso 3: Buscar los últimos dos comprobantes (solo por cédula)
        print(f"🔍 DEBUG: Iniciando búsqueda de comprobantes para cédula {cedula}")
        success, message, receipts = ReceiptService.get_last_two_receipts(db, cedula)
        print(f"🔍 DEBUG: Resultado búsqueda - Éxito: {success}, Comprobantes: {len(receipts) if receipts else 0}")
        
        if not success:
            return False, message
        
        # Paso 4: Mostrar opciones con botones si hay comprobantes
        if len(receipts) == 0:
            # No hay comprobantes en ninguna carpeta
            return False, "No se encontraron comprobantes de pago para los datos proporcionados"
        else:
            # Hay comprobantes en al menos una carpeta, mostrar botones
            body_text = (
                f"🧾 *Comprobantes de pago*\n\n"
                f"Por favor selecciona que comprobante deseas recibir:"
            )
            
            # Definir los botones
            buttons = [
                {
                    'id': '1',
                    'title': 'Quincena anterior'
                },
                {
                    'id': '2', 
                    'title': 'Quincena actual'
                }
            ]
            
            # Enviar mensaje con botones
            send_whatsapp_interactive_buttons(phone_number, body_text, buttons)
            return True, "options_sent"
    
    @staticmethod
    def get_last_two_receipts(db: Session, cedula: str, expedition_date: str = None) -> Tuple[bool, str, list]:
        """
        Obtiene los comprobantes más recientes de un usuario directamente desde FTP
        (uno de cada carpeta: recientes y anteriores)
        
        Args:
            db: Sesión de base de datos (mantenido por compatibilidad, no se usa)
            cedula: Número de cédula
            expedition_date: Fecha de expedición (opcional, no se usa)
            
        Returns:
            Tuple[bool, str, list]: (éxito, mensaje, lista de diccionarios con info de comprobantes)
        """
        try:
            from services.ftp_service import find_files_by_cedula
            import os
            
            result_receipts = []
            remote_folders = ["recientes", "anteriores"]
            
            for folder in remote_folders:
                try:
                    # Buscar archivos que contengan la cédula (cualquier formato)
                    matching_files = find_files_by_cedula(folder, cedula)
                    
                    if matching_files:
                        # Tomar el primer archivo encontrado de esta carpeta
                        selected_file = matching_files[0]
                        
                        # Construir la ruta remota
                        ftp_base_dir = os.getenv("FTP_BASE_DIR", "")
                        if ftp_base_dir:
                            file_path = f"{ftp_base_dir.rstrip('/')}/{folder}/{selected_file}"
                        else:
                            file_path = f"/{folder}/{selected_file}"
                        
                        # Crear objeto de comprobante
                        receipt_data = {
                            'cedula': cedula,
                            'file_path': file_path,
                            'file_name': selected_file,
                            'folder': folder,
                            'total_found': len(matching_files)
                        }
                        result_receipts.append(receipt_data)
                        
                except (ValueError, ConnectionError, Exception):
                    # Continuar con la siguiente carpeta si hay error
                    continue
            
            if not result_receipts:
                return False, f"No se encontraron comprobantes de pago para la cédula {cedula}", []
            
            return True, f"Se encontraron {len(result_receipts)} comprobante(s)", result_receipts
                
        except Exception as e:
            return False, f"Error al buscar comprobantes: {str(e)}", []
    
    @staticmethod
    def get_receipts_by_folder(db: Session, cedula: str, folder: str) -> Tuple[bool, str, list]:
        """
        OPTIMIZACIÓN: Busca comprobantes solo en una carpeta específica.
        
        Args:
            db: Sesión de base de datos (mantenido por compatibilidad, no se usa)
            cedula: Número de cédula
            folder: Carpeta específica a buscar ('recientes' o 'anteriores')
            
        Returns:
            Tuple[bool, str, list]: (éxito, mensaje, lista de diccionarios con info de comprobantes)
        """
        try:
            from services.ftp_service import find_files_by_cedula
            import os
            
            # Validar que la carpeta sea válida
            if folder not in ["recientes", "anteriores"]:
                return False, f"Carpeta inválida: {folder}", []
            
            # Buscar archivos que contengan la cédula en la carpeta específica
            matching_files = find_files_by_cedula(folder, cedula)
            
            if not matching_files:
                return False, f"No se encontraron comprobantes en la carpeta {folder}", []
            
            # Tomar el primer archivo encontrado
            selected_file = matching_files[0]
            
            # Construir la ruta remota
            ftp_base_dir = os.getenv("FTP_BASE_DIR", "")
            if ftp_base_dir:
                file_path = f"{ftp_base_dir.rstrip('/')}/{folder}/{selected_file}"
            else:
                file_path = f"/{folder}/{selected_file}"
            
            # Crear objeto de comprobante
            receipt_data = {
                'cedula': cedula,
                'file_path': file_path,
                'file_name': selected_file,
                'folder': folder,
                'total_found': len(matching_files)
            }
            
            return True, f"Comprobante encontrado en {folder}", [receipt_data]
                
        except Exception as e:
            return False, f"Error al buscar comprobantes en {folder}: {str(e)}", []
    

    
    @staticmethod
    def send_selected_receipt(
        receipt_data, 
        phone_number: str
    ) -> Tuple[bool, str]:
        """
        Envía un comprobante específico seleccionado por el usuario
        
        Args:
            receipt_data: Datos del comprobante (dict o PaymentReceipt)
            phone_number: Número de teléfono destino
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        # Compatibilidad: si es un objeto PaymentReceipt, usar la función antigua
        if hasattr(receipt_data, 'file_path'):
            return ReceiptService._send_receipt_pdf(receipt_data, phone_number)
        else:
            # Si es un diccionario (datos FTP), usar la nueva función
            return ReceiptService._send_receipt_pdf_from_data(receipt_data, phone_number)
    
    @staticmethod
    def _send_receipt_pdf_from_data(receipt_data: dict, phone_number: str) -> Tuple[bool, str]:
        """
        Envía el PDF del comprobante por WhatsApp desde datos FTP
        
        Args:
            receipt_data: Diccionario con datos del comprobante (file_path, file_name, etc.)
            phone_number: Número de teléfono destino
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            file_path = receipt_data['file_path']
            file_name = receipt_data['file_name']
            
            print(f"🔍 DEBUG: Enviando PDF desde FTP")
            print(f"🔍 DEBUG: Ruta del archivo: {file_path}")
            print(f"🔍 DEBUG: Nombre del archivo: {file_name}")
            
            # Enviar mensaje de confirmación
            confirmation_message = (
                f"✅ *Comprobante de pago encontrado*\n\n"
                f"Te estoy enviando el PDF del comprobante..."
            )
            
            send_whatsapp_message(phone_number, confirmation_message)
            
            # Descargar temporalmente desde FTP y enviar
            from services.ftp_service import download_to_temp
            print(f"🔍 DEBUG: Descargando archivo FTP: {file_path}")
            temp_path = download_to_temp(file_path)
            if not temp_path:
                print(f"❌ DEBUG: Error al descargar archivo FTP")
                return False, "No fue posible descargar el archivo del repositorio remoto"
            
            print(f"🔍 DEBUG: Archivo descargado temporalmente en: {temp_path}")
            try:
                success = send_whatsapp_document(
                    to=phone_number,
                    file_path=temp_path,
                    filename=file_name
                )
                print(f"🔍 DEBUG: Resultado envío WhatsApp: {success}")
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        print(f"🔍 DEBUG: Archivo temporal eliminado")
                except Exception:
                    pass
            
            if success:
                return True, "Comprobante enviado exitosamente"
            else:
                return False, "Error al enviar el archivo PDF"
                
        except Exception as e:
            print(f"❌ DEBUG: Error al procesar el envío: {str(e)}")
            return False, f"Error al procesar el envío: {str(e)}"
    
    @staticmethod
    def _send_receipt_pdf(receipt: PaymentReceipt, phone_number: str) -> Tuple[bool, str]:
        """
        Envía el PDF del comprobante por WhatsApp
        
        Args:
            receipt: Comprobante de pago
            phone_number: Número de teléfono destino
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        # Detectar el tipo de archivo
        is_url = isinstance(receipt.file_path, str) and receipt.file_path.lower().startswith(("http://", "https://"))
        
        # Detectar si es una ruta FTP remota (puede empezar con / o con el FTP_BASE_DIR)
        is_remote_ftp_path = False
        if isinstance(receipt.file_path, str):
            # Ruta absoluta FTP o ruta que contiene carpetas de recibos
            if (receipt.file_path.startswith("/") and any(folder in receipt.file_path for folder in ["/recientes/", "/anteriores/"])) or \
               any(folder in receipt.file_path for folder in ["recientes/", "anteriores/"]):
                is_remote_ftp_path = True
        
        # Solo verificar existencia local si no es URL ni ruta FTP remota
        if not is_url and not is_remote_ftp_path:
            # Verificar que el archivo existe localmente
            if not os.path.exists(receipt.file_path):
                return False, "El archivo del comprobante no se encuentra en el servidor"
        
        print(f"🔍 DEBUG: Tipo de archivo - URL: {is_url}, FTP remoto: {is_remote_ftp_path}")
        print(f"🔍 DEBUG: Ruta del archivo: {receipt.file_path}")
        
        try:
            # Enviar mensaje de confirmación
            confirmation_message = (
                f"✅ *Comprobante de pago encontrado*\n\n"
                f"Te estoy enviando el PDF del comprobante..."
            )
            
            send_whatsapp_message(phone_number, confirmation_message)
            
            # Enviar el PDF
            if is_url:
                print(f"🔍 DEBUG: Enviando como URL pública")
                success = send_whatsapp_document_url(
                    to=phone_number,
                    file_url=receipt.file_path,
                    filename=receipt.file_name
                )
            elif is_remote_ftp_path:
                print(f"🔍 DEBUG: Enviando desde FTP remoto")
                # Descargar temporalmente desde FTP y enviar
                from services.ftp_service import download_to_temp
                print(f"🔍 DEBUG: Descargando archivo FTP: {receipt.file_path}")
                temp_path = download_to_temp(receipt.file_path)
                if not temp_path:
                    print(f"❌ DEBUG: Error al descargar archivo FTP")
                    return False, "No fue posible descargar el archivo del repositorio remoto"
                
                print(f"🔍 DEBUG: Archivo descargado temporalmente en: {temp_path}")
                try:
                    success = send_whatsapp_document(
                        to=phone_number,
                        file_path=temp_path,
                        filename=receipt.file_name
                    )
                    print(f"🔍 DEBUG: Resultado envío WhatsApp: {success}")
                finally:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            print(f"🔍 DEBUG: Archivo temporal eliminado")
                    except Exception:
                        pass
            else:
                print(f"🔍 DEBUG: Enviando archivo local")
                success = send_whatsapp_document(
                    to=phone_number,
                    file_path=receipt.file_path,
                    filename=receipt.file_name
                )
            
            if success:
                return True, "Comprobante enviado exitosamente"
            else:
                return False, "Error al enviar el archivo PDF"
                
        except Exception as e:
            return False, f"Error al procesar el envío: {str(e)}"
    
    @staticmethod
    def get_user_receipts(db: Session, cedula: str, expedition_date_str: str) -> Tuple[bool, str, list[PaymentReceipt]]:
        """
        Obtiene todos los comprobantes de un usuario
        
        Args:
            db: Sesión de base de datos
            cedula: Número de cédula
            expedition_date_str: Fecha de expedición
            
        Returns:
            Tuple[bool, str, list[PaymentReceipt]]: (éxito, mensaje, comprobantes)
        """
        # Validar formato de fecha
        is_valid_date, date_message, expedition_date = ValidationService.validate_date_format(expedition_date_str)
        if not is_valid_date:
            return False, date_message, []
        
        # Buscar comprobantes
        return ValidationService.find_user_receipts(db, cedula, expedition_date)
    
    @staticmethod
    def create_receipt(
        db: Session,
        cedula: str,
        file_path: str,
        file_name: str
    ) -> Tuple[bool, str, Optional[PaymentReceipt]]:
        """
        Crea un nuevo comprobante de pago
        
        Args:
            db: Sesión de base de datos
            cedula: Número de cédula
            file_path: Ruta al archivo PDF
            file_name: Nombre del archivo
            
        Returns:
            Tuple[bool, str, Optional[PaymentReceipt]]: (éxito, mensaje, comprobante)
        """
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return False, "El archivo PDF no existe en la ruta especificada", None
        
        # Verificar que no existe un comprobante con la misma ruta
        existing_receipt = db.query(PaymentReceipt).filter(
            PaymentReceipt.file_path == file_path
        ).first()
        
        if existing_receipt:
            return False, "Ya existe un comprobante con esa ruta de archivo", None
        
        try:
            # Crear el comprobante
            receipt = PaymentReceipt(
                cedula=cedula,
                file_path=file_path,
                file_name=file_name
            )
            
            db.add(receipt)
            db.commit()
            db.refresh(receipt)
            
            return True, "Comprobante creado exitosamente", receipt
            
        except Exception as e:
            db.rollback()
            return False, f"Error al crear el comprobante: {str(e)}", None
    
    @staticmethod
    def create_user(
        db: Session,
        cedula: str,
        name: str,
        expedition_date_str: str
    ) -> Tuple[bool, str, Optional[PaymentUser]]:
        """
        Crea un nuevo usuario de pago
        
        Args:
            db: Sesión de base de datos
            cedula: Número de cédula
            phone_number: Número de teléfono
            name: Nombre del usuario
            expedition_date_str: Fecha de expedición en formato DD/MM/AAAA
            
        Returns:
            Tuple[bool, str, Optional[PaymentUser]]: (éxito, mensaje, usuario)
        """
        # Validar formato de cédula
        is_valid_cedula, cedula_message = ValidationService.validate_cedula_format(cedula)
        if not is_valid_cedula:
            return False, cedula_message, None
        
        # Validar formato de fecha
        is_valid_date, date_message, expedition_date = ValidationService.validate_date_format(expedition_date_str)
        if not is_valid_date:
            return False, date_message, None
        
        # Verificar que no existe un usuario con esa cédula
        existing_user = db.query(PaymentUser).filter(PaymentUser.cedula == cedula).first()
        if existing_user:
            return False, "Ya existe un usuario registrado con esa cédula", None
        
        try:
            # Crear el usuario
            user = PaymentUser(
                cedula=cedula,
                name=name,
                expedition_date=expedition_date
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            return True, "Usuario creado exitosamente", user
            
        except Exception as e:
            db.rollback()
            return False, f"Error al crear el usuario: {str(e)}", None
