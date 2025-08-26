#!/bin/bash

echo "🛑 Stopping Property Management System..."

# Остановить и удалить контейнеры
docker-compose down

echo "✅ Property Management System stopped successfully!"

# Показать статус
echo ""
echo "📊 Container status:"
docker-compose ps
