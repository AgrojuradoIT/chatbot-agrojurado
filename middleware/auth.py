from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import auth_service

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Middleware para obtener el usuario actual desde el JWT token
    """
    try:
        token = credentials.credentials
        payload = auth_service.verify_jwt_token(token)
        
        if payload is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Verificar si el access token sigue siendo válido
        access_token = payload.get('access_token')
        if not await auth_service.validate_access_token(access_token):
            raise HTTPException(status_code=401, detail="Token expirado")
        
        
        return payload
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="No autorizado")
