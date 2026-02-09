#!/bin/bash

# Скрипт для быстрого деплоя Kupi Slona с Nginx Proxy Manager
# Использование: ./deploy.sh

set -e

echo "🐘 Kupi Slona Production Deployment"
echo "===================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo "Скопируйте .env.production.example в .env и заполните значения:"
    echo "  cp .env.production.example .env"
    echo "  nano .env"
    exit 1
fi

# Проверка наличия Docker сети
if ! docker network ls | grep -q nginx-proxy; then
    echo -e "${YELLOW}⚠️  Сеть nginx-proxy не найдена. Создаю...${NC}"
    docker network create nginx-proxy
    echo -e "${GREEN}✓ Сеть nginx-proxy создана${NC}"
else
    echo -e "${GREEN}✓ Сеть nginx-proxy существует${NC}"
fi

# Проверка DEBUG=False
if grep -q "DEBUG=True" .env; then
    echo -e "${RED}❌ ВНИМАНИЕ: DEBUG=True в .env файле!${NC}"
    echo "Для production установите DEBUG=False"
    read -p "Продолжить всё равно? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}📦 Сборка Docker образов...${NC}"
docker-compose -f docker-compose.prod.yml build

echo ""
echo -e "${YELLOW}🚀 Запуск контейнеров...${NC}"
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${YELLOW}⏳ Ожидание запуска сервисов...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}🗄️  Применение миграций...${NC}"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

echo ""
echo -e "${YELLOW}📁 Сборка статических файлов...${NC}"
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo ""
echo -e "${GREEN}✅ Деплой завершён!${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Создайте суперюзера:"
echo "   docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "2. Настройте Nginx Proxy Manager:"
echo "   - Domain: ваш_домен.com"
echo "   - Forward to: kupi_slona_nginx:80"
echo "   - SSL: Let's Encrypt"
echo ""
echo "3. Проверьте логи:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "📖 Полная инструкция: NGINX_PROXY_MANAGER_SETUP.md"
