# 🚀 Nginx Proxy Manager: Несколько приложений на субдоменах

## В чём настоящая сила NPM?

NPM позволяет запускать **много приложений** на **одном сервере** через **разные субдомены**!

### Пример: Один сервер, 5 приложений

```
┌─────────────────────────────────────────────────┐
│         IP: 123.456.789.0 (Один сервер)         │
├─────────────────────────────────────────────────┤
│                                                 │
│  Nginx Proxy Manager (Ports 80, 443, 81)       │
│                                                 │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│  slon        │  → kupi_slona_web:8000          │
│  .prvms.ru   │     Django приложение            │
│              │                                  │
├──────────────┼──────────────────────────────────┤
│              │                                  │
│  blog        │  → wordpress:80                  │
│  .prvms.ru   │     WordPress блог               │
│              │                                  │
├──────────────┼──────────────────────────────────┤
│              │                                  │
│  api         │  → fastapi_app:8001             │
│  .prvms.ru   │     FastAPI сервис               │
│              │                                  │
├──────────────┼──────────────────────────────────┤
│              │                                  │
│  docs        │  → mkdocs:8080                  │
│  .prvms.ru   │     Документация                 │
│              │                                  │
└──────────────┴──────────────────────────────────┘

Все с SSL! Все на одном сервере!
```

---

## 📋 Настройка для slon.prvms.ru (упрощённый вариант)

### Шаг 1: Подготовка

```bash
# DNS настройка (A record)
slon.prvms.ru → IP_СЕРВЕРА

# Создайте .env
cp .env.slon.prvms.ru .env
nano .env

# Создайте Docker сеть (если ещё нет)
docker network create nginx-proxy
```

### Шаг 2: Запуск приложения (упрощённая версия)

```bash
# Используем упрощённую конфигурацию
docker-compose -f docker-compose.npm-simple.yml build
docker-compose -f docker-compose.npm-simple.yml up -d

# Миграции
docker-compose -f docker-compose.npm-simple.yml exec web python manage.py migrate
docker-compose -f docker-compose.npm-simple.yml exec web python manage.py collectstatic --noinput

# Суперюзер
docker-compose -f docker-compose.npm-simple.yml exec web python manage.py createsuperuser
```

### Шаг 3: Настройка NPM

**Откройте NPM**: http://IP_СЕРВЕРА:81

#### Proxy Host для slon.prvms.ru

**Add Proxy Host → Details:**
```
Domain Names:        slon.prvms.ru
Scheme:              http
Forward Hostname/IP: kupi_slona_web
Forward Port:        8000

☑ Cache Assets
☑ Block Common Exploits
☑ Websockets Support
```

**SSL:**
```
☑ Request a new SSL Certificate
☑ Force SSL
☑ HTTP/2 Support
☑ HSTS Enabled
```

**Advanced** (для static/media):
```nginx
# Static files через volume
location /static/ {
    alias /var/lib/docker/volumes/kupi_slona_static_volume/_data/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# Media files через volume
location /media/ {
    alias /var/lib/docker/volumes/kupi_slona_media_volume/_data/;
    expires 7d;
    add_header Cache-Control "public";
}

# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;

# Increase upload size
client_max_body_size 20M;
```

**Сохраните!**

---

## 🎯 Добавление второго приложения (пример с WordPress)

### Шаг 1: Запустите WordPress

```bash
# Создайте docker-compose.wordpress.yml
cat > docker-compose.wordpress.yml << 'EOF'
version: '3.9'

services:
  wordpress:
    image: wordpress:latest
    container_name: blog_wordpress
    environment:
      WORDPRESS_DB_HOST: wordpress_db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress_password
    volumes:
      - wordpress_data:/var/www/html
    networks:
      - nginx-proxy
      - wordpress_backend
    restart: unless-stopped

  wordpress_db:
    image: mysql:8.0
    container_name: wordpress_db
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: wordpress_password
      MYSQL_ROOT_PASSWORD: root_password
    volumes:
      - wordpress_db:/var/lib/mysql
    networks:
      - wordpress_backend
    restart: unless-stopped

volumes:
  wordpress_data:
  wordpress_db:

networks:
  wordpress_backend:
  nginx-proxy:
    external: true
EOF

# Запустите
docker-compose -f docker-compose.wordpress.yml up -d
```

### Шаг 2: Добавьте в NPM

**Add Proxy Host → Details:**
```
Domain Names:        blog.prvms.ru
Scheme:              http
Forward Hostname/IP: blog_wordpress
Forward Port:        80

☑ SSL Certificate
☑ Force SSL
```

**Готово!** Теперь у вас:
- ✅ https://slon.prvms.ru - Django приложение
- ✅ https://blog.prvms.ru - WordPress блог

**На одном сервере!**

---

## 💡 Когда нужен внутренний Nginx?

### Используйте `docker-compose.prod.yml` (с внутренним nginx) если:

✅ **Нужна сложная конфигурация**:
   - Rate limiting
   - Сложные rewrites
   - Custom headers для разных путей
   - WebSocket специфичная настройка

✅ **Много static/media файлов**:
   - Nginx лучше отдаёт статику чем Gunicorn
   - Оптимизация кэширования

✅ **Микросервисы**:
   - Один домен → несколько внутренних сервисов
   - Сложная маршрутизация

### Используйте `docker-compose.npm-simple.yml` (без nginx) если:

✅ **Простое приложение**:
   - Один Django проект
   - Немного статики
   - Стандартная конфигурация

✅ **Несколько разных приложений**:
   - Каждое на своём субдомене
   - NPM управляет маршрутизацией

---

## 📊 Сравнение вариантов

### Вариант 1: С внутренним Nginx (docker-compose.prod.yml)

```
NPM → kupi_slona_nginx → kupi_slona_web
      ↓ (отдаёт static)
```

**Плюсы:**
- ✅ Лучшая производительность для static/media
- ✅ Больше контроля над конфигурацией
- ✅ Rate limiting, advanced caching

**Минусы:**
- ❌ Сложнее настройка
- ❌ Больше контейнеров
- ❌ Больше памяти

### Вариант 2: Без Nginx (docker-compose.npm-simple.yml)

```
NPM → kupi_slona_web (Gunicorn)
```

**Плюсы:**
- ✅ Проще настройка
- ✅ Меньше контейнеров
- ✅ Меньше памяти
- ✅ Легче добавлять новые приложения

**Минусы:**
- ❌ Gunicorn медленнее отдаёт статику
- ❌ Меньше контроля

---

## 🎯 Рекомендации

### Для slon.prvms.ru используйте:

**Если это единственное приложение на сервере:**
→ `docker-compose.prod.yml` (с nginx)

**Если планируете добавить другие приложения:**
→ `docker-compose.npm-simple.yml` (без nginx)

### Для нескольких субдоменов:

```bash
# slon.prvms.ru
docker-compose -f docker-compose.npm-simple.yml up -d

# blog.prvms.ru
docker-compose -f docker-compose.wordpress.yml up -d

# api.prvms.ru
docker-compose -f docker-compose.api.yml up -d
```

**Все управляются через один NPM!**

---

## ✅ Quick Start для простого варианта

```bash
# 1. Настройте .env
cp .env.slon.prvms.ru .env
nano .env

# 2. Создайте сеть
docker network create nginx-proxy

# 3. Запустите (простой вариант)
docker-compose -f docker-compose.npm-simple.yml up -d

# 4. Миграции
docker-compose -f docker-compose.npm-simple.yml exec web python manage.py migrate
docker-compose -f docker-compose.npm-simple.yml exec web python manage.py collectstatic --noinput

# 5. В NPM:
# Domain: slon.prvms.ru
# Forward to: kupi_slona_web:8000
# SSL: ✅
```

**Готово!** 🎉

---

## 💬 Итого: В чём плюс NPM?

### ✨ Главный плюс NPM:

**ОДИН сервер → МНОЖЕСТВО приложений на разных субдоменах!**

- slon.prvms.ru
- blog.prvms.ru
- api.prvms.ru
- admin.prvms.ru
- ...

**Все с SSL, все через один NPM!**

Вместо настройки сложных nginx конфигов вручную - просто кликаете в GUI!

---

## 📖 Ссылки

- **Простая версия**: [docker-compose.npm-simple.yml](docker-compose.npm-simple.yml)
- **С внутренним Nginx**: [docker-compose.prod.yml](docker-compose.prod.yml)
- **Quick Start**: [QUICKSTART_slon.prvms.ru.md](QUICKSTART_slon.prvms.ru.md)
