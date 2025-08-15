from fastapi import HTTPException, Depends
from typing import List
from .auth import get_current_user

def require_role(required_role: str):
    """
    Dependencia para verificar si el usuario tiene un rol específico
    """
    def check_role(current_user: dict = Depends(get_current_user)):
        # Super Administrador tiene acceso total
        user_roles = current_user.get('roles', [])
        if 'Super Administrador' in user_roles:
            return current_user
        
        # Verificar si tiene el rol requerido
        if required_role not in user_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Acceso denegado. Se requiere el rol: {required_role}"
            )
        
        return current_user
    return check_role

def require_permission(required_permission: str):
    """
    Dependencia para verificar si el usuario tiene un permiso específico
    """
    def check_permission(current_user: dict = Depends(get_current_user)):
        
        # Super Administrador tiene acceso total
        user_roles = current_user.get('roles', [])
        if 'Super Administrador' in user_roles:

            return current_user
        
        # Verificar si tiene el permiso requerido
        user_permissions = current_user.get('permissions', [])
        if required_permission not in user_permissions:

            raise HTTPException(
                status_code=403, 
                detail=f"Acceso denegado. Se requiere el permiso: {required_permission}"
            )
        

        return current_user
    return check_permission

def require_any_role(required_roles: List[str]):
    """
    Dependencia para verificar si el usuario tiene al menos uno de los roles especificados
    """
    def check_any_role(current_user: dict = Depends(get_current_user)):
        # Super Administrador tiene acceso total
        user_roles = current_user.get('roles', [])
        if 'Super Administrador' in user_roles:
            return current_user
        
        # Verificar si tiene al menos uno de los roles requeridos
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=403, 
                detail=f"Acceso denegado. Se requiere uno de estos roles: {', '.join(required_roles)}"
            )
        
        return current_user
    return check_any_role

def require_any_permission(required_permissions: List[str]):
    """
    Dependencia para verificar si el usuario tiene al menos uno de los permisos especificados
    """
    def check_any_permission(current_user: dict = Depends(get_current_user)):
        # Super Administrador tiene acceso total
        user_roles = current_user.get('roles', [])
        if 'Super Administrador' in user_roles:
            return current_user
        
        # Verificar si tiene al menos uno de los permisos requeridos
        user_permissions = current_user.get('permissions', [])
        if not any(permission in user_permissions for permission in required_permissions):
            raise HTTPException(
                status_code=403, 
                detail=f"Acceso denegado. Se requiere uno de estos permisos: {', '.join(required_permissions)}"
            )
        
        return current_user
    return check_any_permission

# Funciones auxiliares para verificar permisos sin dependencias
def check_permission(current_user: dict, required_permission: str) -> bool:
    """
    Verifica si el usuario actual tiene un permiso específico
    """
    # Super Administrador tiene acceso total
    user_roles = current_user.get('roles', [])
    if 'Super Administrador' in user_roles:
        return True
    
    # Verificar permiso específico
    user_permissions = current_user.get('permissions', [])
    return required_permission in user_permissions

def check_role(current_user: dict, required_role: str) -> bool:
    """
    Verifica si el usuario actual tiene un rol específico
    """
    # Super Administrador tiene acceso total
    user_roles = current_user.get('roles', [])
    if 'Super Administrador' in user_roles:
        return True
    
    # Verificar rol específico
    return required_role in user_roles

def is_super_admin(current_user: dict) -> bool:
    """
    Verifica si el usuario es Super Administrador
    """
    user_roles = current_user.get('roles', [])
    return 'Super Administrador' in user_roles