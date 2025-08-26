"""
Базовые настройки для работы с базой данных
SQLAlchemy с поддержкой асинхронных операций
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
import structlog

logger = structlog.get_logger(__name__)

# Получение URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Преобразование URL для асинхронного драйвера
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = DATABASE_URL
else:
    raise ValueError("Unsupported database URL format. Use postgresql:// or postgresql+asyncpg://")

logger.info("Database configuration", database_url=ASYNC_DATABASE_URL.split('@')[0] + '@***')

# Создание асинхронного движка
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,
    pool_recycle=3600,  # Переиспользование соединений каждый час
)

# Создание фабрики сессий
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

# Базовый класс для моделей
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency для получения сессии базы данных
    Используется в FastAPI endpoints через Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db():
    """
    Инициализация базы данных
    Создание всех таблиц
    """
    try:
        async with engine.begin() as conn:
            # Импортируем все модели для создания таблиц
            from shared.database.models import *  # noqa
            
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db():
    """
    Закрытие соединений с базой данных
    Используется при завершении приложения
    """
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))


class DatabaseManager:
    """
    Менеджер для работы с базой данных
    Предоставляет удобные методы для операций с БД
    """
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def create_session(self) -> AsyncSession:
        """Создание новой сессии"""
        return self.session_factory()
    
    async def execute_query(self, query, params=None):
        """Выполнение произвольного SQL запроса"""
        async with self.session_factory() as session:
            try:
                result = await session.execute(query, params or {})
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error("Query execution error", query=str(query), error=str(e))
                raise
    
    async def health_check(self) -> bool:
        """Проверка состояния подключения к БД"""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()
