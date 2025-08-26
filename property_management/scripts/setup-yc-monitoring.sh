#!/bin/bash

echo "🔧 Настройка Yandex Cloud Monitoring для Property Management System"
echo ""

# Проверка зависимостей
if ! command -v yc &> /dev/null; then
    echo "❌ Yandex Cloud CLI не установлен"
    echo "   Установите CLI: https://cloud.yandex.ru/docs/cli/quickstart"
    exit 1
fi

# Проверка аутентификации
if ! yc config list &> /dev/null; then
    echo "❌ Yandex Cloud CLI не настроен"
    echo "   Выполните: yc init"
    exit 1
fi

echo "✅ Yandex Cloud CLI готов к использованию"
echo ""

# Получение текущих настроек
CURRENT_FOLDER_ID=$(yc config get folder-id)
echo "📂 Текущий каталог: $CURRENT_FOLDER_ID"
echo ""

# Создание сервисного аккаунта
SERVICE_ACCOUNT_NAME="property-management-monitoring"

echo "👤 Создание сервисного аккаунта..."
if yc iam service-account get $SERVICE_ACCOUNT_NAME &> /dev/null; then
    echo "   Сервисный аккаунт уже существует"
    SERVICE_ACCOUNT_ID=$(yc iam service-account get $SERVICE_ACCOUNT_NAME --format=json | jq -r '.id')
else
    SERVICE_ACCOUNT_ID=$(yc iam service-account create \
        --name $SERVICE_ACCOUNT_NAME \
        --description "Service account for Property Management monitoring" \
        --format=json | jq -r '.id')
    echo "   ✅ Сервисный аккаунт создан: $SERVICE_ACCOUNT_ID"
fi

# Назначение роли
echo "🔐 Назначение роли monitoring.editor..."
yc resource-manager folder add-access-binding $CURRENT_FOLDER_ID \
    --role monitoring.editor \
    --service-account-id $SERVICE_ACCOUNT_ID \
    --async > /dev/null

echo "   ✅ Роль назначена"

# Создание ключа
echo "🔑 Создание авторизованного ключа..."
KEY_FILE="./config/yandex-cloud/service-account-key.json"

# Создаем директорию если не существует
mkdir -p ./config/yandex-cloud

yc iam key create \
    --service-account-id $SERVICE_ACCOUNT_ID \
    --output $KEY_FILE \
    --format json

echo "   ✅ Ключ сохранен в $KEY_FILE"

# Обновление .env файла
echo "📝 Обновление переменных окружения..."

# Создаем или обновляем .env файл
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   Создан .env файл из шаблона"
fi

# Обновляем переменные
sed -i.bak "s/YC_MONITORING_ENABLED=false/YC_MONITORING_ENABLED=true/g" .env
sed -i.bak "s/YC_FOLDER_ID=your-yandex-cloud-folder-id/YC_FOLDER_ID=$CURRENT_FOLDER_ID/g" .env

echo "   ✅ Переменные окружения обновлены"

# Проверка конфигурации
echo ""
echo "🔍 Проверка конфигурации..."

if [ -f "$KEY_FILE" ]; then
    echo "   ✅ Файл ключа существует"
else
    echo "   ❌ Файл ключа не найден"
    exit 1
fi

if grep -q "YC_MONITORING_ENABLED=true" .env; then
    echo "   ✅ YC Monitoring включен в .env"
else
    echo "   ❌ YC Monitoring не включен в .env"
fi

if grep -q "YC_FOLDER_ID=$CURRENT_FOLDER_ID" .env; then
    echo "   ✅ Folder ID настроен в .env"
else
    echo "   ❌ Folder ID не настроен в .env"
fi

echo ""
echo "🎉 Настройка Yandex Cloud Monitoring завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Проверьте настройки в .env файле"
echo "   2. Запустите систему с YC Monitoring:"
echo "      docker-compose -f docker-compose.yandex.yml --profile app --profile yandex-monitoring up -d"
echo "   3. Перейдите в консоль Yandex Cloud > Monitoring для просмотра метрик"
echo ""
echo "📊 Полезные ссылки:"
echo "   • Консоль Monitoring: https://console.cloud.yandex.ru/folders/$CURRENT_FOLDER_ID/monitoring"
echo "   • Документация: ./docs/YANDEX_CLOUD_MONITORING.md"
echo ""

# Создание backup старого .env файла
if [ -f .env.bak ]; then
    rm .env.bak
fi
