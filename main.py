from fastapi import FastAPI
from database import Base, engine
from config.settings import settings
from config.cors import setup_cors

# Importar todos los routers
from routers import auth, templates, contacts, messages, statistics, websocket, webhook

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================

# Crear tablas de la base de datos
Base.metadata.create_all(bind=engine)

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

# Registrar todos los routers
app.include_router(auth.router)           # /auth/*
app.include_router(templates.router)      # /api/templates/*
app.include_router(contacts.router)       # /api/contacts/*
app.include_router(messages.router)       # /api/messages/*
app.include_router(statistics.router)     # /api/statistics/*
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
