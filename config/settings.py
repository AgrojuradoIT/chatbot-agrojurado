import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración centralizada de la aplicación"""
    
    # Configuración de la aplicación
    APP_NAME: str = "WhatsApp Chatbot API"
    APP_DESCRIPTION: str = "API para el chatbot de WhatsApp de Agropecuaria Juradó S.A.S"
    APP_VERSION: str = "1.0.0"
    
    # Configuración del servidor
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # WhatsApp Configuration
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    
    # OAuth Configuration
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET: str = os.getenv("OAUTH_CLIENT_SECRET", "")
    OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "")
    OAUTH_AUTH_URL: str = os.getenv("OAUTH_AUTH_URL", "")
    OAUTH_TOKEN_URL: str = os.getenv("OAUTH_TOKEN_URL", "")
    OAUTH_USER_URL: str = os.getenv("OAUTH_USER_URL", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "agrojura_web")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construye la URL de la base de datos desde las variables individuales"""
        if self.DB_PASSWORD:
            return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            return f"mysql+mysqlconnector://{self.DB_USER}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Frontend URL desarrollo
        "http://localhost:8000",  # Backend URL desarrollo # Tu dominio de producción
        "https://www.agrojurado.com",  # Tu dominio con www
        "https://chatbot.agrojurado.com",  # Tu dominio de producción
    ]
    
    def __init__(self):
        """Validar configuraciones críticas al inicializar"""
        if not self.WHATSAPP_VERIFY_TOKEN:
            print("WARNING: WHATSAPP_VERIFY_TOKEN no está configurado")
        if not self.JWT_SECRET_KEY:
            print("WARNING: JWT_SECRET_KEY no está configurado")

# Instancia global de configuración
settings = Settings()
