#!/bin/bash

# Скрипт для быстрой настройки .env файла

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔧 Настройка .env файла"
echo "======================"
echo ""

# Проверка существования .env
if [ -f .env ]; then
    echo -e "${YELLOW}⚠️  Файл .env уже существует${NC}"
    echo ""
    read -p "Перезаписать? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Отменено"
        exit 0
    fi
fi

# Копирование .env.example
if [ -f .env.example ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Скопирован .env.example → .env${NC}"
elif [ -f .env.production.example ]; then
    cp .env.production.example .env
    echo -e "${GREEN}✓ Скопирован .env.production.example → .env${NC}"
else
    echo -e "${RED}❌ Не найден ни .env.example, ни .env.production.example${NC}"
    exit 1
fi

echo ""
echo "📝 Теперь отредактируйте .env файл:"
echo ""
echo "ОБЯЗАТЕЛЬНО установите:"
echo "  DOMAIN=ваш-домен.ru"
echo "  SSL_EMAIL=admin@ваш-домен.ru"
echo ""
echo "Для production также установите:"
echo "  DEBUG=False"
echo "  SECRET_KEY=<случайная-строка>"
echo "  DB_PASSWORD=<сильный-пароль>"
echo ""

read -p "Открыть .env для редактирования? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ${EDITOR:-nano} .env
    echo ""
    echo -e "${YELLOW}Проверка переменных...${NC}"
    echo ""

    if grep -q "^DOMAIN=" .env && grep -q "^SSL_EMAIL=" .env; then
        echo -e "${GREEN}✓ DOMAIN и SSL_EMAIL установлены${NC}"
        echo ""
        grep -E "^DOMAIN=|^SSL_EMAIL=" .env
        echo ""
        echo -e "${GREEN}✓ Готово! Теперь запустите: ./init-letsencrypt.sh${NC}"
    else
        echo -e "${RED}⚠️  DOMAIN или SSL_EMAIL не найдены в .env${NC}"
        echo "Пожалуйста, установите эти переменные вручную:"
        echo "  nano .env"
    fi
else
    echo ""
    echo "Отредактируйте .env вручную:"
    echo "  nano .env"
    echo ""
    echo "Затем запустите:"
    echo "  ./init-letsencrypt.sh"
fi
