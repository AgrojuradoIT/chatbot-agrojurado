from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError, DisconnectionError
import time
import logging
from config.settings import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Usar la configuración centralizada
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Configurar engine con pool de conexiones y reconexión automática
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Número de conexiones en el pool
    max_overflow=20,  # Conexiones adicionales permitidas
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    pool_recycle=3600,  # Reciclar conexiones cada hora
    echo=False,  # Cambiar a True para debug de SQL
    connect_args={
        "autocommit": False,
        "charset": "utf8mb4",
        "use_unicode": True,
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30,
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except (OperationalError, DisconnectionError) as e:
        logger.error(f"Error de conexión a la base de datos: {e}")
        return False

def wait_for_database(max_retries=30, delay=2):
    """Espera a que la base de datos esté disponible"""
    logger.info("Esperando conexión a la base de datos...")
    
    for attempt in range(max_retries):
        if test_connection():
            logger.info("✅ Conexión a la base de datos establecida")
            return True
        
        logger.warning(f"Intento {attempt + 1}/{max_retries}: Base de datos no disponible, reintentando en {delay}s...")
        time.sleep(delay)
    
    logger.error("❌ No se pudo conectar a la base de datos después de todos los intentos")
    return False

def get_db():
    """Obtiene una sesión de base de datos con manejo de errores"""
    db = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            # Probar la conexión ejecutando una consulta simple
            db.execute(text("SELECT 1"))
            yield db
            break
        except (OperationalError, DisconnectionError) as e:
            logger.error(f"Error de conexión en intento {attempt + 1}: {e}")
            if db:
                db.close()
            
            if attempt < max_retries - 1:
                logger.info(f"Reintentando conexión en 2 segundos...")
                time.sleep(2)
            else:
                logger.error("No se pudo establecer conexión después de todos los intentos")
                raise e
        except Exception as e:
            logger.error(f"Error inesperado en get_db: {e}")
            if db:
                db.close()
            raise e
        finally:
            if db and attempt == max_retries - 1:
                db.close()

def get_db_sync():
    """Obtiene una sesión de base de datos de forma síncrona (para uso en webhooks)"""
    db = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            db = SessionLocal()
            # Probar la conexión ejecutando una consulta simple
            db.execute(text("SELECT 1"))
            return db
        except (OperationalError, DisconnectionError) as e:
            logger.error(f"Error de conexión en intento {attempt + 1}: {e}")
            if db:
                db.close()
            
            if attempt < max_retries - 1:
                logger.info(f"Reintentando conexión en 2 segundos...")
                time.sleep(2)
            else:
                logger.error("No se pudo establecer conexión después de todos los intentos")
                raise e
        except Exception as e:
            logger.error(f"Error inesperado en get_db_sync: {e}")
            if db:
                db.close()
            raise e
    
    return db