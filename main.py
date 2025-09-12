from fastapi import FastAPI
from database import Base, engine, wait_for_database, test_connection
from config.settings import settings
from config.cors import setup_cors
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar todos los routers
from routers import auth, templates, contacts, messages, statistics, websocket, webhook, payments, receipts, operators

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================

# Esperar a que la base de datos esté disponible
if not wait_for_database():
    logger.error("No se pudo conectar a la base de datos. La aplicación no se iniciará.")
    exit(1)

# Crear tablas de la base de datos
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas de la base de datos creadas/verificadas correctamente")
except Exception as e:
    logger.error(f"❌ Error al crear tablas de la base de datos: {e}")
    exit(1)

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

# Configurar CORS
setup_cors(app)

# Mostrar token de verificación
print(f"VERIFY_TOKEN: {settings.WHATSAPP_VERIFY_TOKEN}")

# =============================================================================
# REGISTRO DE ROUTERS
# =============================================================================

# Ruta básica
@app.get("/")
async def root():
    """Ruta raíz de la API"""
    return {"message": "WhatsApp Chatbot API - Agropecuaria Juradó S.A.S"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Verifica el estado de la aplicación y la base de datos"""
    db_status = test_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# Registrar todos los routers
app.include_router(auth.router)           # /auth/*
app.include_router(templates.router)      # /api/templates/*
app.include_router(contacts.router)       # /api/contacts/*
app.include_router(messages.router)       # /api/messages/*
app.include_router(statistics.router)     # /api/statistics/*
app.include_router(payments.router)       # /api/payments/*
app.include_router(receipts.router)   # /api/receipts/*
app.include_router(operators.router)      # /api/operators/*
app.include_router(webhook.router)        # /webhook/*

# Registrar rutas WebSocket
app.include_router(websocket.router)      # /ws y /ws/{phone_number}

# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        reload=True
    )
