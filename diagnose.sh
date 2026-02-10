#!/bin/bash

# Скрипт диагностики проблем с доступом к сайту

echo "🔍 Диагностика проблем с kupislona.prvms.ru"
echo "============================================"
echo ""

# 1. Проверка статуса контейнеров
echo "1️⃣ Статус Docker контейнеров:"
docker-compose -f docker-compose.prod.yml ps
echo ""

# 2. Проверка портов
echo "2️⃣ Проверка занятости портов 80 и 443:"
sudo netstat -tulpn | grep -E ':80 |:443 ' || echo "Порты не прослушиваются!"
echo ""

# 3. Проверка логов nginx
echo "3️⃣ Последние логи nginx (errors):"
docker-compose -f docker-compose.prod.yml logs --tail=20 nginx | grep -i error || echo "Ошибок не найдено"
echo ""

echo "4️⃣ Последние логи nginx (access):"
docker-compose -f docker-compose.prod.yml logs --tail=10 nginx | grep -E "GET|POST"
echo ""

# 5. Проверка логов web
echo "5️⃣ Последние логи web контейнера:"
docker-compose -f docker-compose.prod.yml logs --tail=20 web
echo ""

# 6. Проверка сертификата
echo "6️⃣ Проверка SSL сертификата:"
docker-compose -f docker-compose.prod.yml run --rm certbot certificates 2>&1 | grep -A 5 "kupislona.prvms.ru" || echo "Сертификат не найден!"
echo ""

# 7. Проверка конфига nginx
echo "7️⃣ Проверка конфигурации nginx:"
docker-compose -f docker-compose.prod.yml exec nginx nginx -t 2>&1
echo ""

# 8. Проверка DNS
echo "8️⃣ Проверка DNS резолвинга:"
nslookup kupislona.prvms.ru || dig kupislona.prvms.ru
echo ""

# 9. Проверка доступности изнутри контейнера
echo "9️⃣ Проверка доступности Django из nginx:"
docker-compose -f docker-compose.prod.yml exec nginx wget -O- http://web:8000 2>&1 | head -5 || echo "Django не отвечает!"
echo ""

# 10. Firewall
echo "🔟 Проверка firewall (ufw/iptables):"
sudo ufw status || sudo iptables -L -n | grep -E "80|443"
echo ""

echo "============================================"
echo "✅ Диагностика завершена"
echo ""
echo "📋 Частые проблемы и решения:"
echo ""
echo "Если nginx не запущен:"
echo "  → docker-compose -f docker-compose.prod.yml up -d nginx"
echo ""
echo "Если порты заняты другим процессом:"
echo "  → sudo systemctl stop nginx  # Если установлен системный nginx"
echo "  → sudo systemctl stop apache2  # Если установлен apache"
echo ""
echo "Если DNS не резолвится:"
echo "  → Проверьте A-запись в DNS провайдере"
echo "  → Подождите распространения DNS (до 24 часов)"
echo ""
echo "Если сертификат не получен:"
echo "  → Проверьте что домен доступен по HTTP (port 80)"
echo "  → ./init-letsencrypt.sh  # Запустите заново"
echo ""
echo "Если firewall блокирует:"
echo "  → sudo ufw allow 80/tcp"
echo "  → sudo ufw allow 443/tcp"
echo ""
