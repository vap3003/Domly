#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных Property Service
Создание таблиц и заполнение тестовыми данными
"""

import asyncio
import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.database.base import init_db, get_db, AsyncSessionLocal
from shared.core.logging import configure_logging, get_logger
from shared.core.config import PropertyServiceConfig

# Импортируем модели
from app.models import (
    Property, PropertyType, PropertyStatus, PropertyCondition, HeatingType,
    PropertyPhoto, PhotoType,
    PropertyFeature, PropertyFeatureAssignment, PropertyAmenity, FeatureCategory,
    PropertyOwner, OwnerType,
    PropertyView, PropertyFavorite, PropertyInquiry
)

# Настройка логирования
config = PropertyServiceConfig()
configure_logging(config)
logger = get_logger(__name__)


async def create_sample_owners():
    """Создание примеров владельцев недвижимости"""
    logger.info("Creating sample property owners...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Физическое лицо
            owner1 = PropertyOwner(
                owner_type=OwnerType.INDIVIDUAL.value,
                first_name="Иван",
                last_name="Петров",
                middle_name="Сергеевич",
                birth_date=date(1985, 3, 15),
                email="ivan.petrov@example.com",
                phone="+79161234567",
                address={
                    "street": "ул. Тверская, д. 10, кв. 5",
                    "city": "Москва",
                    "postal_code": "125009",
                    "country": "Россия"
                },
                passport_data={
                    "series": "4509",
                    "number": "123456",
                    "issued_by": "ОВД Тверского района г. Москвы",
                    "issued_date": "2005-04-20"
                },
                is_verified=True,
                rating=5
            )
            
            # Юридическое лицо
            owner2 = PropertyOwner(
                owner_type=OwnerType.COMPANY.value,
                company_name="ООО \"Недвижимость Плюс\"",
                company_legal_name="Общество с ограниченной ответственностью \"Недвижимость Плюс\"",
                tax_id="7701234567",
                registration_number="1027700123456",
                email="info@realty-plus.ru",
                phone="+74951234567",
                address={
                    "street": "Ленинский проспект, д. 25, оф. 301",
                    "city": "Москва", 
                    "postal_code": "119071",
                    "country": "Россия"
                },
                is_verified=True,
                rating=4
            )
            
            session.add_all([owner1, owner2])
            await session.commit()
            
            logger.info("Sample owners created successfully")
            return [owner1.id, owner2.id]
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating sample owners: {e}")
            raise


async def create_sample_features():
    """Создание справочника характеристик"""
    logger.info("Creating sample property features...")
    
    features_data = [
        # Удобства
        {"name": "Парковка", "category": FeatureCategory.AMENITY.value, "icon": "parking", "name_en": "Parking", "is_popular": True},
        {"name": "Лифт", "category": FeatureCategory.AMENITY.value, "icon": "elevator", "name_en": "Elevator", "is_popular": True},
        {"name": "Балкон", "category": FeatureCategory.AMENITY.value, "icon": "balcony", "name_en": "Balcony", "is_popular": True},
        {"name": "Кондиционер", "category": FeatureCategory.APPLIANCE.value, "icon": "ac", "name_en": "Air Conditioning"},
        {"name": "Стиральная машина", "category": FeatureCategory.APPLIANCE.value, "icon": "washing-machine", "name_en": "Washing Machine"},
        {"name": "Посудомоечная машина", "category": FeatureCategory.APPLIANCE.value, "icon": "dishwasher", "name_en": "Dishwasher"},
        {"name": "Холодильник", "category": FeatureCategory.APPLIANCE.value, "icon": "fridge", "name_en": "Refrigerator"},
        
        # Безопасность
        {"name": "Охрана", "category": FeatureCategory.SECURITY.value, "icon": "security", "name_en": "Security", "is_popular": True},
        {"name": "Видеонаблюдение", "category": FeatureCategory.SECURITY.value, "icon": "camera", "name_en": "CCTV"},
        {"name": "Домофон", "category": FeatureCategory.SECURITY.value, "icon": "intercom", "name_en": "Intercom"},
        
        # Коммуникации
        {"name": "Интернет", "category": FeatureCategory.UTILITY.value, "icon": "wifi", "name_en": "Internet", "is_popular": True},
        {"name": "Кабельное ТВ", "category": FeatureCategory.UTILITY.value, "icon": "tv", "name_en": "Cable TV"},
        {"name": "Центральное отопление", "category": FeatureCategory.UTILITY.value, "icon": "heating", "name_en": "Central Heating"},
        
        # Инфраструктура
        {"name": "Спортзал", "category": FeatureCategory.INFRASTRUCTURE.value, "icon": "gym", "name_en": "Gym"},
        {"name": "Бассейн", "category": FeatureCategory.INFRASTRUCTURE.value, "icon": "pool", "name_en": "Swimming Pool"},
        {"name": "Детская площадка", "category": FeatureCategory.INFRASTRUCTURE.value, "icon": "playground", "name_en": "Playground"},
        {"name": "Консьерж", "category": FeatureCategory.INFRASTRUCTURE.value, "icon": "concierge", "name_en": "Concierge"},
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            features = []
            for feature_data in features_data:
                feature = PropertyFeature(**feature_data)
                features.append(feature)
            
            session.add_all(features)
            await session.commit()
            
            logger.info(f"Created {len(features)} property features")
            return [f.id for f in features]
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating sample features: {e}")
            raise


async def create_sample_properties(owner_ids, feature_ids):
    """Создание примеров недвижимости"""
    logger.info("Creating sample properties...")
    
    properties_data = [
        {
            "owner_id": owner_ids[0],
            "title": "Просторная 3-комнатная квартира в центре Москвы",
            "description": "Отличная квартира в историческом центре города. Высокие потолки, большие окна, евроремонт. Рядом метро, парки, рестораны.",
            "property_type": PropertyType.APARTMENT,
            "status": PropertyStatus.AVAILABLE,
            "condition": PropertyCondition.EXCELLENT,
            "address": {
                "street": "ул. Тверская, д. 15, кв. 42",
                "city": "Москва",
                "district": "Тверской",
                "postal_code": "125009",
                "country": "Россия"
            },
            "coordinates": {"lat": 55.7558, "lng": 37.6176},
            "total_area": Decimal("85.5"),
            "living_area": Decimal("65.2"),
            "kitchen_area": Decimal("12.8"),
            "rooms_count": 3,
            "bedrooms_count": 2,
            "bathrooms_count": 1,
            "floor": 4,
            "total_floors": 9,
            "year_built": 1955,
            "ceiling_height": Decimal("3.2"),
            "heating_type": HeatingType.CENTRAL,
            "has_elevator": True,
            "has_parking": False,
            "has_balcony": True,
            "has_furniture": True,
            "monthly_rent": Decimal("120000"),
            "security_deposit": Decimal("120000"),
            "utility_cost": Decimal("8000"),
            "currency": "RUB",
            "is_featured": True,
            "amenities": ["parking", "elevator", "balcony", "internet", "cable_tv"]
        },
        {
            "owner_id": owner_ids[1],
            "title": "Современная студия в новостройке",
            "description": "Стильная студия в современном ЖК. Панорамные окна, качественная отделка, консьерж-сервис.",
            "property_type": PropertyType.STUDIO,
            "status": PropertyStatus.AVAILABLE,
            "condition": PropertyCondition.EXCELLENT,
            "address": {
                "street": "Кутузовский проспект, д. 35, кв. 1205",
                "city": "Москва",
                "district": "Дорогомилово",
                "postal_code": "121165",
                "country": "Россия"
            },
            "coordinates": {"lat": 55.7423, "lng": 37.5311},
            "total_area": Decimal("35.8"),
            "living_area": Decimal("25.4"),
            "kitchen_area": Decimal("8.2"),
            "rooms_count": 1,
            "bedrooms_count": 0,
            "bathrooms_count": 1,
            "floor": 12,
            "total_floors": 25,
            "year_built": 2020,
            "ceiling_height": Decimal("2.8"),
            "heating_type": HeatingType.INDIVIDUAL,
            "has_elevator": True,
            "has_parking": True,
            "has_balcony": True,
            "has_furniture": False,
            "monthly_rent": Decimal("75000"),
            "security_deposit": Decimal("75000"),
            "utility_cost": Decimal("5000"),
            "currency": "RUB",
            "amenities": ["parking", "elevator", "balcony", "gym", "concierge", "security"]
        },
        {
            "owner_id": owner_ids[0],
            "title": "Уютный дом в Подмосковье",
            "description": "Двухэтажный дом с участком. Тихое место, свежий воздух, идеально для семьи с детьми.",
            "property_type": PropertyType.HOUSE,
            "status": PropertyStatus.AVAILABLE,
            "condition": PropertyCondition.GOOD,
            "address": {
                "street": "ул. Садовая, д. 25",
                "city": "Одинцово",
                "district": "Центральный",
                "postal_code": "143000",
                "country": "Россия"
            },
            "coordinates": {"lat": 55.6758, "lng": 37.2656},
            "total_area": Decimal("150.0"),
            "living_area": Decimal("120.0"),
            "kitchen_area": Decimal("18.0"),
            "rooms_count": 4,
            "bedrooms_count": 3,
            "bathrooms_count": 2,
            "floor": 2,
            "total_floors": 2,
            "year_built": 2010,
            "ceiling_height": Decimal("2.7"),
            "heating_type": HeatingType.GAS,
            "has_elevator": False,
            "has_parking": True,
            "has_balcony": False,
            "has_furniture": False,
            "monthly_rent": Decimal("90000"),
            "security_deposit": Decimal("90000"),
            "utility_cost": Decimal("12000"),
            "currency": "RUB",
            "amenities": ["parking", "garden", "internet"]
        }
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            properties = []
            for prop_data in properties_data:
                property_obj = Property(**prop_data)
                properties.append(property_obj)
            
            session.add_all(properties)
            await session.commit()
            
            # Добавляем характеристики к недвижимости
            for i, property_obj in enumerate(properties):
                # Добавляем несколько случайных характеристик
                feature_assignments = []
                selected_features = feature_ids[:3 + i]  # Разное количество для каждой недвижимости
                
                for j, feature_id in enumerate(selected_features):
                    assignment = PropertyFeatureAssignment(
                        property_id=property_obj.id,
                        feature_id=feature_id,
                        display_order=j,
                        is_highlighted=(j < 2)  # Первые две выделяем
                    )
                    feature_assignments.append(assignment)
                
                session.add_all(feature_assignments)
            
            await session.commit()
            
            logger.info(f"Created {len(properties)} sample properties with features")
            return [p.id for p in properties]
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating sample properties: {e}")
            raise


async def create_sample_photos(property_ids):
    """Создание примеров фотографий"""
    logger.info("Creating sample property photos...")
    
    photos_data = [
        # Фото для первой недвижимости
        {
            "property_id": property_ids[0],
            "url": "https://example.com/photos/property1_main.jpg",
            "thumbnail_url": "https://example.com/photos/thumbs/property1_main.jpg",
            "caption": "Главная фотография гостиной",
            "photo_type": PhotoType.LIVING_ROOM.value,
            "is_main": True,
            "order_index": 1,
            "width": 1920,
            "height": 1080
        },
        {
            "property_id": property_ids[0],
            "url": "https://example.com/photos/property1_kitchen.jpg",
            "thumbnail_url": "https://example.com/photos/thumbs/property1_kitchen.jpg",
            "caption": "Современная кухня",
            "photo_type": PhotoType.KITCHEN.value,
            "order_index": 2,
            "width": 1920,
            "height": 1080
        },
        # Фото для второй недвижимости
        {
            "property_id": property_ids[1],
            "url": "https://example.com/photos/property2_main.jpg",
            "thumbnail_url": "https://example.com/photos/thumbs/property2_main.jpg",
            "caption": "Современная студия",
            "photo_type": PhotoType.INTERIOR.value,
            "is_main": True,
            "order_index": 1,
            "width": 1920,
            "height": 1080
        }
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            photos = []
            for photo_data in photos_data:
                photo = PropertyPhoto(**photo_data)
                photos.append(photo)
            
            session.add_all(photos)
            await session.commit()
            
            logger.info(f"Created {len(photos)} sample photos")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating sample photos: {e}")
            raise


async def main():
    """Главная функция инициализации"""
    logger.info("Starting Property Service database initialization...")
    
    try:
        # Инициализация базы данных
        await init_db()
        logger.info("Database tables created successfully")
        
        # Создание тестовых данных
        owner_ids = await create_sample_owners()
        feature_ids = await create_sample_features()
        property_ids = await create_sample_properties(owner_ids, feature_ids)
        await create_sample_photos(property_ids)
        
        logger.info("✅ Property Service database initialized successfully!")
        logger.info(f"Created {len(owner_ids)} owners, {len(feature_ids)} features, {len(property_ids)} properties")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Установка переменных окружения для работы с БД
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://admin:password@localhost:5432/property_management")
    os.environ.setdefault("SECRET_KEY", "development-secret-key-32-characters-long")
    
    asyncio.run(main())
