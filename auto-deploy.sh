#!/bin/bash

# Деплой Kupi Slona
# Использование: ./auto-deploy.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_DIR="/root/kupi_slona"

cd $PROJECT_DIR

# --- 1. Проверки ---

if [ ! -f .env ]; then
    echo -e "${RED}❌ .env не найден!${NC}"
    exit 1
fi

if [ ! -f nginx/conf.d/default.conf ] || ! grep -q "ssl_certificate" nginx/conf.d/default.conf 2>/dev/null; then
    echo -e "${RED}❌ SSL не настроен! Сначала запустите: ./init-letsencrypt.sh${NC}"
    exit 1
fi

# --- 2. Обновление кода ---

echo -e "${YELLOW}📥 Pulling latest changes...${NC}"
git pull origin main || {
    echo -e "${RED}❌ Git pull failed!${NC}"
    exit 1
}

# --- 3. Сборка и запуск ---

echo -e "${YELLOW}🔨 Building...${NC}"
docker-compose -f $COMPOSE_FILE build web

echo -e "${YELLOW}🚀 Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up -d

# --- 4. Ожидание готовности ---

echo -e "${YELLOW}⏳ Waiting for services...${NC}"
sleep 10

# --- 5. Миграции и статика ---

echo -e "${YELLOW}🗄️  Running migrations...${NC}"
docker-compose -f $COMPOSE_FILE exec -T web python manage.py migrate --noinput || {
    echo -e "${RED}❌ Migrations failed!${NC}"
    docker-compose -f $COMPOSE_FILE logs --tail=20 web
    exit 1
}

echo -e "${YELLOW}📦 Collecting static files...${NC}"
docker-compose -f $COMPOSE_FILE exec -T web python manage.py collectstatic --noinput

# --- 6. Health check ---

echo -e "${YELLOW}🏥 Health check...${NC}"
sleep 3
HEALTH=$(curl -sf http://localhost:8000/health/ 2>/dev/null || echo "fail")

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}⚠ Health check: $HEALTH${NC}"
    echo "Проверьте логи: docker-compose -f $COMPOSE_FILE logs web"
fi

# --- 7. Статус ---

echo ""
docker-compose -f $COMPOSE_FILE ps
echo ""
echo -e "${GREEN}✅ Deploy completed!${NC}"
echo ""
