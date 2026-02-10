# Production Deployment Guide

Инструкции по развёртыванию Kupi Slona на production сервере.

## Требования

- Docker и Docker Compose установлены на сервере
- Домен направлен на IP сервера (A-запись для `slon.prvms.ru`)
- Порты 80 и 443 открыты в firewall

## Первоначальная настройка

### 1. Клонирование репозитория

```bash
cd ~
git clone <repository-url> kupi_slona
cd kupi_slona
```

### 2. Создание .env файла

```bash
cp .env.example .env
nano .env
```

Обязательные настройки:
```env
DEBUG=False
SECRET_KEY=<сгенерируйте длинный случайный ключ>
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru

DB_PASSWORD=<сильный пароль для БД>

# Для OAuth (если используется)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### 3. Настройка SSL сертификата

Отредактируйте email в `init-letsencrypt.sh`:
```bash
nano init-letsencrypt.sh
# Измените EMAIL="admin@prvms.ru" на ваш email
```

Запустите скрипт получения SSL:
```bash
./init-letsencrypt.sh
```

Скрипт:
1. Создаст временную HTTP-конфигурацию nginx
2. Запустит nginx и Django
3. Получит SSL сертификат через Let's Encrypt
4. Обновит конфигурацию для HTTPS
5. Перезагрузит nginx

### 4. Запуск миграций и сборка статики

```bash
WEB_CONTAINER=$(docker-compose -f docker-compose.prod.yml ps -q web)
docker exec $WEB_CONTAINER python manage.py migrate
docker exec $WEB_CONTAINER python manage.py collectstatic --noinput
```

### 5. Создание суперпользователя

```bash
docker exec -it $WEB_CONTAINER python manage.py createsuperuser
```

## Автоматический деплой через GitHub Actions

### Настройка secrets

В настройках репозитория GitHub добавьте secrets:
- `SERVER_HOST` - IP адрес сервера
- `SERVER_USER` - пользователь SSH (обычно `root`)
- `SSH_PRIVATE_KEY` - приватный SSH ключ

### Деплой

После настройки, каждый push в `main` будет автоматически:
1. Подключаться к серверу по SSH
2. Делать `git pull`
3. Пересобирать Docker образ web
4. Запускать миграции
5. Собирать статику

## Ручной деплой

Для ручного деплоя используйте скрипт:

```bash
./auto-deploy.sh
```

Скрипт делает то же самое, что и GitHub Actions.

## Управление сервисами

### Просмотр логов

```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Только web
docker-compose -f docker-compose.prod.yml logs -f web

# Только nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Только celery
docker-compose -f docker-compose.prod.yml logs -f celery_worker
```

### Перезапуск сервисов

```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml restart

# Только web
docker-compose -f docker-compose.prod.yml restart web
```

### Остановка и запуск

```bash
# Остановить все
docker-compose -f docker-compose.prod.yml down

# Запустить все
docker-compose -f docker-compose.prod.yml up -d
```

### Доступ к shell

```bash
# Django shell
WEB_CONTAINER=$(docker-compose -f docker-compose.prod.yml ps -q web)
docker exec -it $WEB_CONTAINER python manage.py shell

# Bash shell
docker exec -it $WEB_CONTAINER bash
```

## Обновление SSL сертификата

Certbot автоматически обновляет сертификат каждые 12 часов.

Для ручного обновления:
```bash
docker-compose -f docker-compose.prod.yml run --rm certbot renew
docker-compose -f docker-compose.prod.yml restart nginx
```

## Мониторинг

### Проверка статуса сервисов

```bash
docker-compose -f docker-compose.prod.yml ps
```

### Проверка использования ресурсов

```bash
docker stats
```

## Backup

### База данных

```bash
# Создать backup
docker exec kupi_slona_db_1 pg_dump -U postgres elephant_shop > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из backup
cat backup.sql | docker exec -i kupi_slona_db_1 psql -U postgres elephant_shop
```

### Media файлы

```bash
# Создать backup
docker cp kupi_slona_web_1:/app/media ./media_backup

# Восстановить
docker cp ./media_backup kupi_slona_web_1:/app/media
```

## Troubleshooting

### Сайт не открывается

1. Проверьте статус контейнеров:
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   ```

2. Проверьте логи nginx:
   ```bash
   docker-compose -f docker-compose.prod.yml logs nginx
   ```

3. Проверьте логи web:
   ```bash
   docker-compose -f docker-compose.prod.yml logs web
   ```

### 502 Bad Gateway

Обычно означает, что web контейнер не запущен или недоступен:
```bash
docker-compose -f docker-compose.prod.yml restart web
```

### SSL ошибки

Если сертификат не валидный, попробуйте переполучить:
```bash
docker-compose -f docker-compose.prod.yml run --rm certbot renew --force-renewal
docker-compose -f docker-compose.prod.yml restart nginx
```

### Проблемы со статикой

```bash
WEB_CONTAINER=$(docker-compose -f docker-compose.prod.yml ps -q web)
docker exec $WEB_CONTAINER python manage.py collectstatic --noinput --clear
```

## Архитектура

```
Internet (443/80)
    ↓
nginx (SSL termination, static files)
    ↓
web (Django + Gunicorn)
    ↓
db (PostgreSQL)
redis (Celery broker)
    ↓
celery_worker (async tasks)
```

- **nginx**: Обрабатывает HTTPS, статику, media, проксирует к Django
- **web**: Django приложение на Gunicorn
- **db**: PostgreSQL база данных
- **redis**: Брокер для Celery
- **celery_worker**: Асинхронные задачи (генерация изображений)
- **certbot**: Автообновление SSL сертификатов
