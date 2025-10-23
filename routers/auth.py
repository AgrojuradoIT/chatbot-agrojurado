from fastapi import APIRouter, HTTPException, Depends
from models.auth_models import OAuthCallbackRequest, AuthResponse, UserResponse
from services.auth_service import auth_service
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/callback", response_model=AuthResponse)
async def oauth_callback(request: OAuthCallbackRequest):
    """
    Maneja el callback OAuth y intercambia el código por un access token
    """
    try:
        # Intercambiar código por access token
        token_data = await auth_service.exchange_code_for_token(request.code)
        
        if not token_data:
            raise HTTPException(status_code=400, detail="Error intercambiando código por token")
        
        access_token = token_data.get('access_token')
        
        # Obtener información del usuario
        user_info = await auth_service.get_user_info(access_token)
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Error obteniendo información del usuario")
        
        # Validar que la información del usuario tenga los campos requeridos
        required_fields = ['id', 'name', 'email', 'sector']
        for field in required_fields:
            if not user_info.get(field):
                raise HTTPException(status_code=400, detail=f"Información del usuario incompleta: falta {field}")
        
        # Crear JWT interno
        jwt_token = await auth_service.create_jwt_token(user_info, access_token)
        
        if not jwt_token:
            raise HTTPException(status_code=500, detail="Error creando token interno")
        
        return AuthResponse(
            access_token=jwt_token,
            user={
                "id": user_info.get('id'),
                "name": user_info.get('name'),
                "email": user_info.get('email'),
                "sector": user_info.get('sector')
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en oauth_callback: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Obtiene información del usuario autenticado
    """
    return UserResponse(
        id=current_user.get('user_id'),
        name=current_user.get('name'),
        email=current_user.get('email'),
        sector=current_user.get('sector'),
        roles=current_user.get('roles', []),
        permissions=current_user.get('permissions', [])
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Cierra la sesión del usuario
    """
    try:
        access_token = current_user.get('access_token')
        
        # Revocar token en Laravel Passport
        await auth_service.revoke_token(access_token)
        
        return {"message": "Sesión cerrada exitosamente"}
        
    except Exception as e:
        print(f"Error en logout: {e}")
        # Aunque falle la revocación, consideramos el logout exitoso
        return {"message": "Sesión cerrada exitosamente"}
