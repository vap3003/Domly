#!/bin/bash

echo "🚀 Starting Property Management System..."

# Проверить наличие .env файла
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before running the system"
fi

# Проверить наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Остановить существующие контейнеры
echo "🛑 Stopping existing containers..."
docker-compose down

# Собрать и запустить сервисы
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Ждать запуска сервисов
echo "⏳ Waiting for services to start..."
sleep 30

# Проверить здоровье сервисов
echo "🏥 Checking services health..."
docker-compose ps

# Показать статус
echo ""
echo "✅ Property Management System started successfully!"
echo ""
echo "📊 Available services:"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo ""
echo "🌐 When services are ready:"
echo "   • API Gateway: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • View all logs: docker-compose logs -f"
echo "   • View specific service: docker-compose logs -f <service-name>"
echo ""
echo "🛑 To stop the system: ./scripts/stop.sh"
