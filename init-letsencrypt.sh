#!/bin/bash

# Скрипт для первоначальной настройки SSL с Let's Encrypt
# Использование: ./init-letsencrypt.sh

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Загрузка переменных из .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo ""
    echo "Создайте .env файл:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    echo "Установите в .env:"
    echo "  DOMAIN=ваш-домен.ru"
    echo "  SSL_EMAIL=admin@ваш-домен.ru"
    exit 1
fi

# Загрузка .env
export $(grep -v '^#' .env | xargs)

# Проверка обязательных переменных
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Переменная DOMAIN не указана в .env${NC}"
    echo ""
    echo "Откройте .env и установите:"
    echo "  DOMAIN=ваш-домен.ru"
    echo ""
    echo "Текущее содержимое .env:"
    cat .env | grep -E "^DOMAIN=" || echo "  (DOMAIN не найден)"
    exit 1
fi

if [ -z "$SSL_EMAIL" ]; then
    echo -e "${RED}❌ Переменная SSL_EMAIL не указана в .env${NC}"
    echo ""
    echo "Откройте .env и установите:"
    echo "  SSL_EMAIL=admin@ваш-домен.ru"
    echo ""
    echo "Текущее содержимое .env:"
    cat .env | grep -E "^SSL_EMAIL=" || echo "  (SSL_EMAIL не найден)"
    exit 1
fi

COMPOSE_FILE="docker-compose.prod.yml"

echo "🔐 Let's Encrypt SSL Setup"
echo "=========================="
echo ""
echo "Domain: $DOMAIN"
echo "Email: $SSL_EMAIL"
echo ""

# 1. Создание временной конфигурации nginx без SSL
echo -e "${YELLOW}📝 Creating temporary nginx config...${NC}"
cat > nginx/conf.d/default.conf << EOF
# Temporary HTTP-only config for certbot
server {
    listen 80;
    server_name ${DOMAIN};

    # Allow certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Temporary allow all traffic
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }
}
EOF

# 2. Запуск nginx и web (без certbot пока)
echo -e "${YELLOW}🚀 Starting nginx and web...${NC}"
docker-compose -f $COMPOSE_FILE up -d web nginx

# 3. Ожидание запуска
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 5

# 4. Получение сертификата
echo -e "${YELLOW}🔐 Requesting SSL certificate for ${DOMAIN}...${NC}"
echo "This may take 30-60 seconds..."
echo ""

if docker-compose -f $COMPOSE_FILE run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $SSL_EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN 2>&1 | tee /tmp/certbot.log; then
    echo ""
    echo -e "${GREEN}✓ Certificate request completed${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to obtain certificate!${NC}"
    echo "Check the error above. Common issues:"
    echo "  - Domain not pointing to this server"
    echo "  - Port 80 blocked by firewall"
    echo "  - nginx not accessible from internet"
    cat /tmp/certbot.log
    exit 1
fi

# 5. Восстановление полной конфигурации nginx с SSL
echo -e "${YELLOW}📝 Restoring full nginx config with SSL...${NC}"
cat > nginx/conf.d/default.conf << EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name ${DOMAIN};

    # Allow certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Proxy to Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 6. Перезагрузка nginx
echo -e "${YELLOW}🔄 Reloading nginx with SSL...${NC}"
docker-compose -f $COMPOSE_FILE restart nginx

# 7. Запуск certbot для автообновления
echo -e "${YELLOW}🤖 Starting certbot auto-renewal service...${NC}"
docker-compose -f $COMPOSE_FILE up -d certbot >/dev/null 2>&1
echo -e "${GREEN}✓ Certbot renewal service started${NC}"
echo "  (будет автоматически проверять сертификат каждые 12 часов)"

# 8. Проверка сертификата
echo ""
echo -e "${YELLOW}🔍 Verifying certificate installation...${NC}"
CERT_INFO=$(docker-compose -f $COMPOSE_FILE run --rm certbot certificates 2>/dev/null | grep -A 5 "$DOMAIN" | head -6)

if echo "$CERT_INFO" | grep -q "$DOMAIN"; then
    echo -e "${GREEN}✓ Certificate successfully installed!${NC}"
    echo ""
    echo "Certificate details:"
    echo "$CERT_INFO" | grep -E "Certificate Name|Domains|Expiry"
else
    echo -e "${RED}✗ Certificate verification failed!${NC}"
    echo "Certificate not found for domain: $DOMAIN"
    echo ""
    echo "Trying to get certificate list..."
    docker-compose -f $COMPOSE_FILE run --rm certbot certificates 2>&1 | head -20
    exit 1
fi

# 9. Готово!
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ SSL setup completed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "🌐 Your site should now be accessible at:"
echo "   https://$DOMAIN"
echo ""
echo "🔐 Certificate details:"
echo "   Location: /etc/letsencrypt/live/${DOMAIN}/"
echo "   Auto-renewal: Every 12 hours via certbot service"
echo ""
echo "📋 Next steps:"
echo "   1. Visit https://$DOMAIN to verify it works"
echo "   2. Check nginx logs: docker-compose -f $COMPOSE_FILE logs nginx"
echo "   3. Deploy your app: ./auto-deploy.sh"
echo ""
