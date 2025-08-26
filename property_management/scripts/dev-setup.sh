#!/bin/bash

echo "🔧 Setting up development environment..."

# Создать виртуальные окружения для каждого сервиса
services=("property-service" "tenant-service" "monitoring-service" "api-gateway")

for service in "${services[@]}"; do
    echo "📦 Setting up $service..."
    
    cd "services/$service"
    
    # Создать виртуальное окружение
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created for $service"
    fi
    
    # Активировать и установить зависимости
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    
    echo "✅ Dependencies installed for $service"
    
    cd ../..
done

echo ""
echo "🎉 Development environment setup completed!"
echo ""
echo "🚀 To run a service locally:"
echo "   cd services/<service-name>"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
echo ""
echo "🐳 To run with Docker:"
echo "   ./scripts/start.sh"
