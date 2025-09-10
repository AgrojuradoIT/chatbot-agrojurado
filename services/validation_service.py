import re
from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from models.payment_models import PaymentUser, PaymentReceipt

class ValidationService:
    """Servicio para validar datos de usuarios y comprobantes"""
    
    @staticmethod
    def validate_cedula_format(cedula: str) -> Tuple[bool, str]:
        """
        Validates cedula format according to Colombian rules
        
        Args:
            cedula: Cedula number to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Clean spaces and special characters
        cedula_clean = re.sub(r'[^\d]', '', cedula)
        
        # Validate that it only contains numbers
        if not cedula_clean.isdigit():
            return False, "La cédula solo debe contener números"
        
        return True, "Cédula válida"
    

    
    @staticmethod
    def validate_date_format(date_str: str) -> Tuple[bool, str, Optional[datetime]]:
        """
        Validates date format DD/MM/YYYY
        
        Args:
            date_str: Date in string format
            
        Returns:
            Tuple[bool, str, Optional[datetime]]: (is_valid, error_message, date_object)
        """
        # Pattern for DD/MM/YYYY
        date_pattern = r'^(\d{1,2})/(\d{1,2})/(\d{4})$'
        match = re.match(date_pattern, date_str)
        
        if not match:
            return False, "El formato debe ser DD/MM/AAAA (ejemplo: 15/03/1990)", None
        
        day, month, year = map(int, match.groups())
        
        # Validate ranges
        if year < 1900 or year > datetime.now().year:
            return False, f"El año debe estar entre 1900 y {datetime.now().year}", None
        
        if month < 1 or month > 12:
            return False, "El mes debe estar entre 1 y 12", None
        
        if day < 1 or day > 31:
            return False, "El día debe estar entre 1 y 31", None
        
        # Validate specific days per month
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        # Adjust February for leap years
        if month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            days_in_month[1] = 29
        
        if day > days_in_month[month - 1]:
            return False, f"El día {day} no es válido para el mes {month}", None
        
        # Create datetime object
        try:
            date_obj = datetime(year, month, day)
            return True, "Fecha válida", date_obj
        except ValueError:
            return False, "Fecha inválida", None
    
    @staticmethod
    def validate_user_data(db: Session, cedula: str, expedition_date: datetime) -> Tuple[bool, str, Optional[PaymentUser]]:
        """
        Validates that user data exists in the database
        
        Args:
            db: Database session
            cedula: Cedula number
            expedition_date: Expedition date
            
        Returns:
            Tuple[bool, str, Optional[PaymentUser]]: (is_valid, error_message, user)
        """
        # Search user by cedula
        user = db.query(PaymentUser).filter(
            PaymentUser.cedula == cedula,
            PaymentUser.is_active == True
        ).first()
        
        if not user:
            return False, "No se encontró un usuario registrado con esa cédula", None
        
        # Validate expedition date (with ±1 day tolerance)
        from datetime import timedelta
        tolerance = timedelta(days=1)
        
        if abs(user.expedition_date - expedition_date) > tolerance:
            return False, "La fecha de expedición no coincide con nuestros registros", None
        
        return True, "Datos válidos", user
    
    @staticmethod
    def find_user_receipts(db: Session, cedula: str, expedition_date: datetime) -> Tuple[bool, str, list[PaymentReceipt]]:
        """
        Searches for user payment receipts
        
        Args:
            db: Database session
            cedula: Cedula number
            expedition_date: Expedition date (to validate user)
            
        Returns:
            Tuple[bool, str, list[PaymentReceipt]]: (success, message, receipts)
        """
        # First validate that the user exists
        is_valid, message, user = ValidationService.validate_user_data(db, cedula, expedition_date)
        
        if not is_valid:
            return False, message, []
        
        # Search user receipts
        receipts = db.query(PaymentReceipt).filter(
            PaymentReceipt.cedula == cedula,
            PaymentReceipt.is_active == True
        ).all()
        
        if not receipts:
            return False, "No se encontraron comprobantes de pago para esta cédula", []
        
        return True, f"Se encontraron {len(receipts)} comprobante(s) de pago", receipts
    
    @staticmethod
    def is_cedula_registered(db: Session, cedula: str) -> Tuple[bool, str, Optional[PaymentUser]]:
        """
        Checks if a cedula is registered in the database
        
        Args:
            db: Database session
            cedula: Cedula number
            
        Returns:
            Tuple[bool, str, Optional[PaymentUser]]: (is_registered, message, user)
        """
        # Search user by cedula
        user = db.query(PaymentUser).filter(
            PaymentUser.cedula == cedula,
            PaymentUser.is_active == True
        ).first()
        
        if user:
            return True, f"Usuario registrado: {user.name}", user
        else:
            return False, "La cédula no existe en nuestros registros", None
    
    @staticmethod
    def get_latest_receipt(db: Session, cedula: str, expedition_date: datetime) -> Tuple[bool, str, Optional[PaymentReceipt]]:
        """
        Obtiene el comprobante más reciente de un usuario
        
        Args:
            db: Sesión de base de datos
            cedula: Número de cédula
            expedition_date: Fecha de expedición
            
        Returns:
            Tuple[bool, str, Optional[PaymentReceipt]]: (éxito, mensaje, comprobante)
        """
        is_valid, message, receipts = ValidationService.find_user_receipts(db, cedula, expedition_date)
        
        if not is_valid:
            return False, message, None
        
        # Retornar el primero
        latest_receipt = receipts[0]
        return True, "Comprobante encontrado", latest_receipt
