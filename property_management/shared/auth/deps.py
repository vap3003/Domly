"""
Зависимости для аутентификации в FastAPI
Dependencies для проверки токенов и получения текущего пользователя
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import structlog

from .security import security_manager

logger = structlog.get_logger(__name__)

# Схема безопасности для извлечения Bearer токена
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency для получения текущего пользователя из JWT токена
    
    Args:
        credentials: HTTP авторизационные данные
    
    Returns:
        dict: Данные пользователя из токена
    
    Raises:
        HTTPException: При ошибке аутентификации
    """
    try:
        token = credentials.credentials
        payload = security_manager.verify_access_token(token)
        
        # Извлекаем данные пользователя из токена
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        user_data = {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", []),
            "is_active": payload.get("is_active", True)
        }
        
        logger.debug("User authenticated", user_id=user_id, role=user_data["role"])
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency для получения активного пользователя
    
    Args:
        current_user: Данные текущего пользователя
    
    Returns:
        dict: Данные активного пользователя
    
    Raises:
        HTTPException: Если пользователь неактивен
    """
    if not current_user.get("is_active", True):
        logger.warning("Inactive user attempted access", user_id=current_user.get("user_id"))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Dependency для получения пользователя (опционально)
    Не выбрасывает исключение, если токен отсутствует
    
    Args:
        credentials: HTTP авторизационные данные (опционально)
    
    Returns:
        dict или None: Данные пользователя или None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = security_manager.verify_access_token(token)
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", []),
            "is_active": payload.get("is_active", True)
        }
        
    except Exception as e:
        logger.debug("Optional authentication failed", error=str(e))
        return None


def require_role(required_role: str):
    """
    Декоратор dependency для проверки роли пользователя
    
    Args:
        required_role: Требуемая роль
    
    Returns:
        function: Dependency функция
    """
    async def role_dependency(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role")
        
        if user_role != required_role:
            logger.warning(
                "Access denied: insufficient role",
                user_id=current_user.get("user_id"),
                required_role=required_role,
                user_role=user_role
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        
        return current_user
    
    return role_dependency


def require_permission(required_permission: str):
    """
    Декоратор dependency для проверки разрешения пользователя
    
    Args:
        required_permission: Требуемое разрешение
    
    Returns:
        function: Dependency функция
    """
    async def permission_dependency(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        
        if required_permission not in user_permissions:
            logger.warning(
                "Access denied: insufficient permissions",
                user_id=current_user.get("user_id"),
                required_permission=required_permission,
                user_permissions=user_permissions
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {required_permission}"
            )
        
        return current_user
    
    return permission_dependency


def require_owner_or_admin(resource_owner_id_field: str = "owner_id"):
    """
    Dependency для проверки, что пользователь является владельцем ресурса или администратором
    
    Args:
        resource_owner_id_field: Название поля с ID владельца ресурса
    
    Returns:
        function: Dependency функция
    """
    async def owner_or_admin_dependency(
        resource_data: Dict[str, Any],
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        resource_owner_id = resource_data.get(resource_owner_id_field)
        
        # Администратор имеет доступ ко всем ресурсам
        if user_role == "admin":
            return current_user
        
        # Проверка владельца ресурса
        if user_id != resource_owner_id:
            logger.warning(
                "Access denied: not owner",
                user_id=user_id,
                resource_owner_id=resource_owner_id
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only access your own resources."
            )
        
        return current_user
    
    return owner_or_admin_dependency


# Предопределенные dependency для общих ролей
require_admin = require_role("admin")
require_manager = require_role("manager")
require_user = require_role("user")
