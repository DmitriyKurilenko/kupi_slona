# 🔐 Production Credentials - ВАЖНО!

**⚠️ ЭТОТ ФАЙЛ НЕ ДОЛЖЕН БЫТЬ В GIT!**
**⚠️ ПОСЛЕ ПРИМЕНЕНИЯ УДАЛИТЕ ЭТОТ ФАЙЛ!**

## Инструкции по обновлению credentials на production

### 1. Подключитесь к production серверу

```bash
ssh root@slon.prvms.ru
cd /root/kupi_slona
```

### 2. Создайте backup текущего .env файла

```bash
cp .env.slon.prvms.ru .env.slon.prvms.ru.backup.$(date +%Y%m%d_%H%M%S)
```

### 3. Обновите .env.slon.prvms.ru с новыми credentials

Используйте эти **СГЕНЕРИРОВАННЫЕ** значения:

```env
# Django Settings
SECRET_KEY=ss3g6Iqj1kp3CXeRxm5rIrTeb/pmdY5g1rJlfEoi4MpbGUgoDctsKTnHJIT6/7/JuwniTqTT3JBzbrxQ
DEBUG=False
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru

# Database (НОВЫЙ ПАРОЛЬ)
DB_NAME=kupi_slona
DB_USER=postgres
DB_PASSWORD=hozzR4tcX55try56jqUk14ig3psRDDdW6ONjiSEIsyE
DB_HOST=db
DB_PORT=5432

# Redis (НОВЫЙ ПАРОЛЬ)
REDIS_PASSWORD=ecsQubL7MVkX2dE0YGtTtZImzPOxsDcL

# Celery
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/0

# OAuth (СОХРАНИТЕ ТЕКУЩИЕ ЗНАЧЕНИЯ)
GOOGLE_CLIENT_ID=<ваш_текущий_client_id>
GOOGLE_CLIENT_SECRET=<ваш_текущий_client_secret>
APPLE_CLIENT_ID=<ваш_apple_client_id>
APPLE_TEAM_ID=<ваш_apple_team_id>
APPLE_KEY_ID=<ваш_apple_key_id>
APPLE_PRIVATE_KEY=<ваш_apple_private_key>

# SSL/TLS
DOMAIN=slon.prvms.ru
SSL_EMAIL=<ваш_email>
```

### 4. Обновите Redis конфигурацию

Убедитесь, что `docker-compose.prod.yml` содержит Redis с паролем (уже обновлено в коде).

### 5. Пересоздайте контейнеры с новыми credentials

```bash
# Создайте backup БД ПЕРЕД остановкой
docker exec kupi_slona-db-1 pg_dump -U postgres kupi_slona | gzip > ~/backup_before_password_change_$(date +%Y%m%d_%H%M%S).sql.gz

# Остановите все сервисы
docker-compose -f docker-compose.prod.yml down

# Удалите volumes (ВНИМАНИЕ: потеряете данные БД!)
# Сначала восстановите БД после перезапуска из backup
docker volume rm kupi_slona_postgres_data

# Запустите с новыми credentials
docker-compose -f docker-compose.prod.yml up -d

# Дождитесь запуска БД (30 секунд)
sleep 30

# Восстановите БД из backup
gunzip -c ~/backup_before_password_change_*.sql.gz | docker exec -i kupi_slona-db-1 psql -U postgres -d kupi_slona

# Проверьте статус
docker-compose -f docker-compose.prod.yml ps
```

### 6. Проверьте работоспособность

```bash
# Проверьте health endpoint
curl http://localhost:8000/health/

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f web
```

### 7. УДАЛИТЕ ЭТОТ ФАЙЛ

```bash
# На вашей локальной машине
rm /Users/hvosdt/Documents/dev/kupi_slona/PRODUCTION_CREDENTIALS.md

# Убедитесь, что он не попал в git
git status
```

---

## Альтернативный подход: Обновить пароли БЕЗ удаления данных

Если у вас уже есть production данные, которые нельзя потерять:

### Для PostgreSQL:

```bash
# Подключитесь к работающему контейнеру БД
docker exec -it kupi_slona-db-1 psql -U postgres

# Внутри psql:
ALTER USER postgres WITH PASSWORD 'hozzR4tcX55try56jqUk14ig3psRDDdW6ONjiSEIsyE';
\q

# Обновите .env.slon.prvms.ru
# Перезапустите web и celery (БЕЗ БД)
docker-compose -f docker-compose.prod.yml restart web celery_worker
```

### Для Redis:

Redis требует перезапуск с новой конфигурацией (данные в Redis не критичны - это только кэш и очередь задач).

---

## OAuth Credentials

**ВАЖНО:** Если ваши OAuth credentials были скомпрометированы, выполните:

### Google OAuth:

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Найдите ваш OAuth 2.0 Client ID
3. Click "Delete" на старом Client Secret
4. Create new Client Secret
5. Обновите `GOOGLE_CLIENT_SECRET` в `.env.slon.prvms.ru`

### Apple Sign In:

1. Перейдите в [Apple Developer Portal](https://developer.apple.com/account/resources/authkeys/list)
2. Revoke старый Key
3. Create new Key
4. Download и обновите `APPLE_PRIVATE_KEY` в `.env.slon.prvms.ru`

---

## Checklist

- [ ] Создан backup БД
- [ ] Обновлен .env.slon.prvms.ru на сервере
- [ ] Пароли БД и Redis изменены
- [ ] Контейнеры перезапущены
- [ ] Health check проходит успешно
- [ ] OAuth credentials ротированы (если были скомпрометированы)
- [ ] Этот файл удален и не попал в git
