#!/bin/bash

# Скрипт для первоначальной настройки SSL с Let's Encrypt
# Использование: ./init-letsencrypt.sh

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Конфигурация
DOMAIN="slon.prvms.ru"
EMAIL="admin@prvms.ru"  # Укажите ваш email
COMPOSE_FILE="docker-compose.prod.yml"

echo "🔐 Let's Encrypt SSL Setup"
echo "=========================="
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# 1. Создание временной конфигурации nginx без SSL
echo -e "${YELLOW}📝 Creating temporary nginx config...${NC}"
cat > nginx/conf.d/default.conf << 'EOF'
# Temporary HTTP-only config for certbot
server {
    listen 80;
    server_name slon.prvms.ru;

    # Allow certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Temporary allow all traffic
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
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
echo -e "${YELLOW}🔐 Requesting SSL certificate...${NC}"
docker-compose -f $COMPOSE_FILE run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN

# 5. Восстановление полной конфигурации nginx с SSL
echo -e "${YELLOW}📝 Restoring full nginx config with SSL...${NC}"
cat > nginx/conf.d/default.conf << 'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name slon.prvms.ru;

    # Allow certbot challenges
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name slon.prvms.ru;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/slon.prvms.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/slon.prvms.ru/privkey.pem;

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
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 6. Перезагрузка nginx
echo -e "${YELLOW}🔄 Reloading nginx with SSL...${NC}"
docker-compose -f $COMPOSE_FILE restart nginx

# 7. Запуск certbot для автообновления
echo -e "${YELLOW}🤖 Starting certbot renewal service...${NC}"
docker-compose -f $COMPOSE_FILE up -d certbot

# 8. Готово!
echo ""
echo -e "${GREEN}✅ SSL setup completed successfully!${NC}"
echo ""
echo "Your site should now be accessible at:"
echo "  https://$DOMAIN"
echo ""
echo "Certificate will auto-renew every 12 hours via certbot service."
echo ""
