"""
Модуль безопасности и аутентификации
JWT токены, хеширование паролей, проверка доступа
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import os
import structlog

logger = structlog.get_logger(__name__)

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль
    
    Returns:
        bool: True если пароль верный, False иначе
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Password verification error", error=str(e))
        return False


def get_password_hash(password: str) -> str:
    """
    Хеширование пароля
    
    Args:
        password: Пароль в открытом виде
    
    Returns:
        str: Хешированный пароль
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error("Password hashing error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password"
        )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT access токена
    
    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена
    
    Returns:
        str: JWT токен
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error("Token creation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating access token"
        )


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Создание JWT refresh токена
    
    Args:
        data: Данные для включения в токен
    
    Returns:
        str: JWT refresh токен
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error("Refresh token creation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating refresh token"
        )


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Проверка и декодирование JWT токена
    
    Args:
        token: JWT токен
        token_type: Тип токена (access или refresh)
    
    Returns:
        dict: Данные из токена
    
    Raises:
        HTTPException: При ошибке валидации токена
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Проверка типа токена
        if payload.get("type") != token_type:
            logger.warning("Invalid token type", expected=token_type, actual=payload.get("type"))
            raise credentials_exception
        
        # Проверка времени истечения
        exp = payload.get("exp")
        if exp is None:
            raise credentials_exception
        
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        logger.warning("JWT validation error", error=str(e))
        raise credentials_exception
    except Exception as e:
        logger.error("Token verification error", error=str(e))
        raise credentials_exception


def create_token_pair(user_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Создание пары токенов (access + refresh)
    
    Args:
        user_data: Данные пользователя
    
    Returns:
        dict: Словарь с access_token и refresh_token
    """
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


class SecurityManager:
    """
    Менеджер безопасности для централизованного управления аутентификацией
    """
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return get_password_hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return verify_password(plain_password, hashed_password)
    
    def create_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """Создание пары токенов"""
        return create_token_pair(user_data)
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Проверка access токена"""
        return verify_token(token, "access")
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Проверка refresh токена"""
        return verify_token(token, "refresh")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Обновление access токена по refresh токену
        
        Args:
            refresh_token: Refresh токен
        
        Returns:
            str: Новый access токен
        """
        try:
            payload = self.verify_refresh_token(refresh_token)
            
            # Создаем новый access токен с теми же данными пользователя
            user_data = {k: v for k, v in payload.items() 
                        if k not in ['exp', 'iat', 'type']}
            
            return create_access_token(user_data)
            
        except Exception as e:
            logger.error("Token refresh error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh token"
            )


# Глобальный экземпляр менеджера безопасности
security_manager = SecurityManager()
