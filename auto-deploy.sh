#!/bin/bash

# Скрипт автоматического деплоя для Kupi Slona
# Использование на сервере: ./auto-deploy.sh

set -e

echo "🚀 Kupi Slona Auto-Deploy"
echo "========================="
echo ""

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Конфигурация
COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_DIR="/root/kupi_slona"

cd $PROJECT_DIR

# 1. Получение изменений
echo -e "${YELLOW}📥 Pulling latest changes...${NC}"
git pull origin main || {
    echo -e "${RED}❌ Git pull failed!${NC}"
    exit 1
}

# 2. Проверка .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# 3. Остановка старых контейнеров
echo -e "${YELLOW}🛑 Stopping old containers...${NC}"
docker-compose -f $COMPOSE_FILE down || true

# 4. Пересборка контейнеров
echo -e "${YELLOW}🔨 Building containers...${NC}"
docker-compose -f $COMPOSE_FILE build --no-cache web || {
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
}

# 5. Запуск сервисов
echo -e "${YELLOW}🔄 Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# 6. Ожидание запуска
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# 7. Миграции
echo -e "${YELLOW}🗄️  Running migrations...${NC}"
WEB_CONTAINER=$(docker-compose -f $COMPOSE_FILE ps -q web)
docker exec $WEB_CONTAINER python manage.py migrate --noinput || {
    echo -e "${RED}❌ Migrations failed!${NC}"
    exit 1
}

# 8. Сборка статики
echo -e "${YELLOW}📦 Collecting static files...${NC}"
docker exec $WEB_CONTAINER python manage.py collectstatic --noinput || {
    echo -e "${RED}❌ Collectstatic failed!${NC}"
    exit 1
}

# 9. Проверка статуса
echo ""
echo -e "${YELLOW}📊 Services status:${NC}"
docker-compose -f $COMPOSE_FILE ps

# 10. Готово!
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "📋 Quick commands:"
echo "  Logs:    docker-compose -f $COMPOSE_FILE logs -f web"
echo "  Restart: docker-compose -f $COMPOSE_FILE restart web"
echo "  Shell:   docker-compose -f $COMPOSE_FILE exec web bash"
echo ""
