"""
Пример использования базовых core модулей
Демонстрация работы с конфигурацией, логированием, БД и аутентификацией
"""

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import structlog

# Импорт наших модулей
from shared.core.config import PropertyServiceConfig
from shared.core.logging import configure_logging, get_logger
from shared.database.base import get_db, init_db, close_db, DatabaseManager
from shared.auth.deps import get_current_user, get_current_active_user, require_admin
from shared.auth.security import security_manager
from shared.utils.exceptions import PropertyManagementException, to_http_exception
from shared.utils.validators import validate_email_address, validate_phone_number


# Создание конфигурации
config = PropertyServiceConfig()

# Настройка логирования
configure_logging(config)
logger = get_logger(__name__)


# Lifespan для управления жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Property Service", version=config.SERVICE_VERSION)
    
    try:
        # Инициализация базы данных
        await init_db()
        logger.info("Database initialized")
        
        # Проверка подключения к БД
        db_manager = DatabaseManager()
        if await db_manager.health_check():
            logger.info("Database health check passed")
        else:
            logger.error("Database health check failed")
            
    except Exception as e:
        logger.error("Failed to initialize service", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Property Service")
    await close_db()
    logger.info("Service shutdown complete")


# Создание приложения
app = FastAPI(
    title=config.SERVICE_NAME,
    version=config.SERVICE_VERSION,
    description="Property Management Service with core modules",
    lifespan=lifespan
)


# Пример endpoint с аутентификацией
@app.post("/auth/login")
async def login(email: str, password: str):
    """Аутентификация пользователя"""
    try:
        # Валидация email
        email = validate_email_address(email)
        
        # В реальном приложении здесь была бы проверка в БД
        # Для примера используем фиктивные данные
        if email == "admin@example.com" and password == "password":
            user_data = {
                "sub": "550e8400-e29b-41d4-a716-446655440000",
                "email": email,
                "role": "admin",
                "permissions": ["read", "write", "delete"],
                "is_active": True
            }
            
            tokens = security_manager.create_tokens(user_data)
            logger.info("User logged in", email=email)
            
            return {
                "message": "Login successful",
                **tokens
            }
        else:
            logger.warning("Invalid login attempt", email=email)
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except ValueError as e:
        logger.error("Login validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе"""
    logger.info("User info requested", user_id=current_user["user_id"])
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"],
        "permissions": current_user["permissions"]
    }


@app.post("/auth/refresh")
async def refresh_token(refresh_token: str):
    """Обновление access токена"""
    try:
        new_access_token = security_manager.refresh_access_token(refresh_token)
        logger.info("Token refreshed")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(status_code=401, detail="Could not refresh token")


@app.get("/admin/settings")
async def get_admin_settings(admin_user: dict = Depends(require_admin)):
    """Endpoint только для администраторов"""
    logger.info("Admin settings accessed", admin_id=admin_user["user_id"])
    
    return {
        "service_name": config.SERVICE_NAME,
        "environment": config.ENVIRONMENT.value,
        "database_pool_size": config.DATABASE_POOL_SIZE,
        "max_property_photos": config.MAX_PROPERTY_PHOTOS,
        "supported_photo_formats": config.SUPPORTED_PHOTO_FORMATS
    }


@app.get("/database/health")
async def database_health_check():
    """Проверка состояния базы данных"""
    db_manager = DatabaseManager()
    is_healthy = await db_manager.health_check()
    
    status_code = 200 if is_healthy else 503
    
    return {
        "database_healthy": is_healthy,
        "timestamp": "2024-01-01T00:00:00Z"  # В реальности использовать datetime.utcnow()
    }


@app.post("/validate/contact")
async def validate_contact_info(email: str, phone: str):
    """Валидация контактной информации"""
    try:
        validated_email = validate_email_address(email)
        validated_phone = validate_phone_number(phone)
        
        logger.info("Contact info validated", email=validated_email, phone=validated_phone)
        
        return {
            "email": validated_email,
            "phone": validated_phone,
            "valid": True
        }
        
    except ValueError as e:
        logger.warning("Contact validation failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/config")
async def get_service_config():
    """Получение публичной конфигурации сервиса"""
    return {
        "service_name": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION,
        "environment": config.ENVIRONMENT.value,
        "max_property_photos": config.MAX_PROPERTY_PHOTOS,
        "supported_photo_formats": config.SUPPORTED_PHOTO_FORMATS,
        "enable_geocoding": config.ENABLE_GEOCODING
    }


# Обработчик кастомных исключений
@app.exception_handler(PropertyManagementException)
async def property_management_exception_handler(request, exc: PropertyManagementException):
    """Обработчик кастомных исключений системы"""
    logger.error(
        "Property management exception",
        exception_type=type(exc).__name__,
        message=exc.message,
        details=exc.details
    )
    
    http_exc = to_http_exception(exc)
    return {"error": http_exc.detail}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    db_manager = DatabaseManager()
    db_healthy = await db_manager.health_check()
    
    health_status = {
        "service": config.SERVICE_NAME,
        "version": config.SERVICE_VERSION,
        "environment": config.ENVIRONMENT.value,
        "database": "healthy" if db_healthy else "unhealthy",
        "status": "healthy" if db_healthy else "unhealthy"
    }
    
    status_code = 200 if db_healthy else 503
    
    logger.info("Health check performed", status=health_status["status"])
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None  # Отключаем стандартное логирование uvicorn
    )
