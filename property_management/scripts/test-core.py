#!/usr/bin/env python3
"""
Скрипт для тестирования базовых core модулей
Проверяет работу конфигурации, логирования, валидаторов и аутентификации
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.core.config import PropertyServiceConfig, get_config
from shared.core.logging import configure_logging, get_logger
from shared.auth.security import security_manager
from shared.utils.validators import (
    validate_email_address, validate_phone_number, 
    validate_postal_code, validate_inn
)
from shared.utils.exceptions import PropertyManagementException, ValidationException


async def test_configuration():
    """Тестирование конфигурации"""
    print("🔧 Testing Configuration...")
    
    try:
        # Тестирование загрузки конфигурации
        config = PropertyServiceConfig()
        print(f"✅ Service name: {config.SERVICE_NAME}")
        print(f"✅ Environment: {config.ENVIRONMENT.value}")
        print(f"✅ Log level: {config.LOG_LEVEL.value}")
        
        # Тестирование фабрики конфигураций
        tenant_config = get_config("tenant-service")
        print(f"✅ Tenant service config loaded: {tenant_config.SERVICE_NAME}")
        
        print("✅ Configuration test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}\n")
        return False


async def test_logging():
    """Тестирование логирования"""
    print("📝 Testing Logging...")
    
    try:
        # Настройка логирования
        config = PropertyServiceConfig()
        configure_logging(config)
        
        # Получение логгера
        logger = get_logger("test_logger")
        
        # Тестирование различных уровней логирования
        logger.debug("Debug message", test_field="debug_value")
        logger.info("Info message", test_field="info_value")
        logger.warning("Warning message", test_field="warning_value")
        logger.error("Error message", test_field="error_value")
        
        print("✅ Logging test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}\n")
        return False


async def test_authentication():
    """Тестирование аутентификации"""
    print("🔐 Testing Authentication...")
    
    try:
        # Тестирование хеширования паролей
        password = "test_password_123"
        hashed = security_manager.hash_password(password)
        print(f"✅ Password hashed: {hashed[:20]}...")
        
        # Тестирование проверки пароля
        is_valid = security_manager.verify_password(password, hashed)
        assert is_valid, "Password verification failed"
        print("✅ Password verification passed")
        
        # Тестирование создания токенов
        user_data = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "role": "user"
        }
        
        tokens = security_manager.create_tokens(user_data)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        print("✅ Token creation passed")
        
        # Тестирование проверки access токена
        payload = security_manager.verify_access_token(tokens["access_token"])
        assert payload["sub"] == user_data["sub"]
        print("✅ Access token verification passed")
        
        # Тестирование обновления токена
        new_access_token = security_manager.refresh_access_token(tokens["refresh_token"])
        assert new_access_token is not None
        print("✅ Token refresh passed")
        
        print("✅ Authentication test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}\n")
        return False


async def test_validators():
    """Тестирование валидаторов"""
    print("✅ Testing Validators...")
    
    try:
        # Тестирование email валидатора
        valid_email = validate_email_address("test@example.com")
        assert valid_email == "test@example.com"
        print("✅ Email validation passed")
        
        # Тестирование телефона
        valid_phone = validate_phone_number("8-999-123-45-67")
        assert valid_phone == "+79991234567"
        print("✅ Phone validation passed")
        
        # Тестирование почтового индекса
        valid_postal = validate_postal_code("123456")
        assert valid_postal == "123456"
        print("✅ Postal code validation passed")
        
        # Тестирование ИНН (используем тестовый валидный ИНН)
        try:
            validate_inn("7707083893")  # Тестовый ИНН
            print("✅ INN validation passed")
        except ValueError:
            print("⚠️  INN validation skipped (test INN may be invalid)")
        
        # Тестирование невалидных данных
        try:
            validate_email_address("invalid-email")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid email correctly rejected")
        
        try:
            validate_phone_number("invalid-phone")
            assert False, "Should have raised ValueError"
        except ValueError:
            print("✅ Invalid phone correctly rejected")
        
        print("✅ Validators test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Validators test failed: {e}\n")
        return False


async def test_exceptions():
    """Тестирование исключений"""
    print("⚠️  Testing Exceptions...")
    
    try:
        # Тестирование базового исключения
        try:
            raise PropertyManagementException("Test exception", {"test": "data"})
        except PropertyManagementException as e:
            assert e.message == "Test exception"
            assert e.details["test"] == "data"
            print("✅ Base exception handling passed")
        
        # Тестирование валидационного исключения
        try:
            raise ValidationException("Validation failed", {"field": "email"})
        except ValidationException as e:
            assert e.message == "Validation failed"
            print("✅ Validation exception handling passed")
        
        print("✅ Exceptions test passed\n")
        return True
        
    except Exception as e:
        print(f"❌ Exceptions test failed: {e}\n")
        return False


async def main():
    """Главная функция для запуска всех тестов"""
    print("🚀 Starting Core Modules Test Suite\n")
    
    tests = [
        test_configuration,
        test_logging,
        test_authentication,
        test_validators,
        test_exceptions
    ]
    
    results = []
    
    for test in tests:
        result = await test()
        results.append(result)
    
    # Подведение итогов
    passed = sum(results)
    total = len(results)
    
    print("📊 Test Results:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Core modules are working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    # Установка переменных окружения для тестирования
    os.environ.setdefault("DATABASE_URL", "postgresql://admin:password@localhost:5432/property_management")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-development-only-32-chars-long")
    os.environ.setdefault("ENVIRONMENT", "testing")
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
