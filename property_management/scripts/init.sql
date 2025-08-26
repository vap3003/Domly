-- Инициализация базы данных для Property Management System
-- Создание расширений PostgreSQL

-- UUID расширение для генерации UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Создание схем для разделения данных по сервисам
CREATE SCHEMA IF NOT EXISTS property_service;
CREATE SCHEMA IF NOT EXISTS tenant_service;
CREATE SCHEMA IF NOT EXISTS monitoring_service;

-- Создание таблиц для системных настроек
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Вставка базовых настроек системы
INSERT INTO system_settings (key, value, description) VALUES 
    ('system_name', 'Property Management System', 'Название системы'),
    ('version', '1.0.0', 'Версия системы'),
    ('timezone', 'Europe/Moscow', 'Временная зона системы'),
    ('currency_default', 'RUB', 'Валюта по умолчанию'),
    ('language_default', 'ru', 'Язык по умолчанию')
ON CONFLICT (key) DO NOTHING;

-- Создание индексов для производительности
CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);

-- Создание функции для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применение триггера к таблице system_settings
DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Логирование инициализации
DO $$
BEGIN
    RAISE NOTICE 'Property Management System database initialized successfully';
    RAISE NOTICE 'Schemas created: property_service, tenant_service, monitoring_service';
    RAISE NOTICE 'Extensions enabled: uuid-ossp';
END $$;
