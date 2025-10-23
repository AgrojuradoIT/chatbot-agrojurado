import os
import requests
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from datetime import datetime, timedelta
import json

class AuthService:
    def __init__(self):
        self.client_id = os.getenv("OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("OAUTH_CLIENT_SECRET")
        self.redirect_uri = os.getenv("OAUTH_REDIRECT_URI")
        self.token_url = os.getenv("OAUTH_TOKEN_URL")
        self.user_url = os.getenv("OAUTH_USER_URL")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        
        if not all([self.client_id, self.client_secret, self.redirect_uri, self.token_url, self.user_url]):
            raise ValueError("Faltan variables de entorno OAuth requeridas")
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Intercambia el código de autorización por un access token
        """
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': code,
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            
            response = requests.post(self.token_url, headers=headers, json=data)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data
            else:
                print(f"Error obteniendo token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en exchange_code_for_token: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del usuario usando el access token
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            
            response = requests.get(self.user_url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data
            else:
                print(f"Error obteniendo usuario: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en get_user_info: {e}")
            return None
    
    async def get_user_roles_permissions(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los roles y permisos del usuario desde Laravel
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            
            # Construir URL del endpoint de roles y permisos
            roles_url = self.user_url.replace('/api/user', '/api/me/roles-permisos')
            response = requests.get(roles_url, headers=headers)
            
            if response.status_code == 200:
                roles_data = response.json()
                return roles_data
            else:
                print(f"Error obteniendo roles y permisos: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en get_user_roles_permissions: {e}")
            return None
    
    async def create_jwt_token(self, user_data: Dict[str, Any], access_token: str) -> str:
        """
        Crea un JWT token interno para la aplicación incluyendo roles y permisos
        """
        try:
            # Obtener roles y permisos del usuario
            roles_data = await self.get_user_roles_permissions(access_token)
            
            payload = {
                'user_id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'sector': user_data.get('sector'),
                'roles': roles_data.get('roles', []) if roles_data else [],
                'permissions': roles_data.get('permisos', []) if roles_data else [],
                'access_token': access_token,
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow(),
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            return token
            
        except Exception as e:
            print(f"Error creando JWT: {e}")
            return None
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica y decodifica un JWT token
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except JWTError as e:
            print(f"Error verificando JWT: {e}")
            return None
    
    async def validate_access_token(self, access_token: str) -> bool:
        """
        Valida si un access token sigue siendo válido con Laravel Passport
        """
        try:
            user_info = await self.get_user_info(access_token)
            return user_info is not None
        except Exception as e:
            print(f"Error validando access token: {e}")
            return False
    
    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoca un access token en Laravel Passport
        """
        try:
            # Laravel Passport no tiene endpoint estándar de revoke, 
            # pero podemos usar el logout del AuthController
            logout_url = self.user_url.replace('/api/user', '/api/logout')
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            
            response = requests.post(logout_url, headers=headers)
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Error revocando token: {e}")
            return False

# Instancia global del servicio
auth_service = AuthService()
