# Настройка Kupi Slona на субдомене slon.prvms.ru

## 📋 Пошаговая инструкция

### Шаг 1: Настройка DNS

**ВАЖНО!** Сначала настройте DNS запись:

1. Перейдите в панель управления DNS вашего домена `prvms.ru`
2. Добавьте **A record**:
   ```
   Тип: A
   Имя: slon
   Значение: IP_АДРЕС_ВАШЕГО_СЕРВЕРА
   TTL: 300 (или Auto)
   ```

3. Проверьте DNS (может занять до 5-10 минут):
   ```bash
   # На вашем компьютере или сервере
   nslookup slon.prvms.ru

   # Должно вернуть IP вашего сервера
   ```

### Шаг 2: Подготовка .env файла

```bash
# Скопируйте шаблон
cp .env.slon.prvms.ru .env

# Отредактируйте файл
nano .env
```

**Обязательно измените:**
1. `SECRET_KEY` - сгенерируйте новый:
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. `DB_PASSWORD` - установите сильный пароль для PostgreSQL

**Проверьте что установлено:**
```bash
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru
DEBUG=False
```

### Шаг 3: Создание Docker сети

```bash
# Создайте сеть для Nginx Proxy Manager (если ещё не создана)
docker network create nginx-proxy

# Проверьте что сеть создана
docker network ls | grep nginx-proxy
```

### Шаг 4: Деплой приложения

```bash
# Запустите автоматический деплой
./deploy.sh

# Или вручную:
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Шаг 5: Создание суперюзера

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Введите:
# Username: admin
# Email: admin@prvms.ru
# Password: (ваш пароль)
```

### Шаг 6: Проверка контейнеров

```bash
# Проверьте что все контейнеры запущены
docker-compose -f docker-compose.prod.yml ps

# Должны быть running:
# - kupi_slona_db
# - kupi_slona_redis
# - kupi_slona_web
# - kupi_slona_nginx
# - kupi_slona_celery

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f web
```

### Шаг 7: Настройка в Nginx Proxy Manager

#### 7.1 Откройте Nginx Proxy Manager

Обычно доступен на: `http://IP_СЕРВЕРА:81`

- **Email по умолчанию**: `admin@example.com`
- **Password по умолчанию**: `changeme`

(После первого входа смените пароль!)

#### 7.2 Добавьте Proxy Host

**Hosts → Proxy Hosts → Add Proxy Host**

**Tab: Details**
```
Domain Names:        slon.prvms.ru
Scheme:              http
Forward Hostname/IP: kupi_slona_nginx
Forward Port:        80

☑ Block Common Exploits
☑ Websockets Support
```

**Tab: SSL**
```
☑ Request a new SSL Certificate
☑ Force SSL
☑ HTTP/2 Support
☑ HSTS Enabled

Email Address: ваш_email@example.com

☑ I Agree to the Let's Encrypt Terms of Service
```

**Tab: Advanced** (опционально)
```nginx
# Увеличить лимит загрузки файлов
client_max_body_size 20M;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

#### 7.3 Сохраните

Нажмите **Save**. Nginx Proxy Manager автоматически:
1. Настроит reverse proxy
2. Получит SSL сертификат от Let's Encrypt
3. Настроит редирект с HTTP на HTTPS

### Шаг 8: Проверка работоспособности

#### 8.1 Откройте в браузере

Перейдите на: **https://slon.prvms.ru**

✅ **Должно работать:**
- Главная страница загружается
- SSL сертификат валидный (зелёный замок 🔒)
- Стили и картинки загружаются
- Регистрация/вход работают

#### 8.2 Тест основных функций

```bash
# Тест 1: Главная страница
curl -I https://slon.prvms.ru
# Должно вернуть: HTTP/2 200

# Тест 2: Static файлы
curl -I https://slon.prvms.ru/static/favicon.svg
# Должно вернуть: HTTP/2 200

# Тест 3: API
curl https://slon.prvms.ru/api/docs
# Должно вернуть JSON с API документацией
```

#### 8.3 Проверьте в браузере

- [ ] **Главная страница**: https://slon.prvms.ru
- [ ] **Регистрация**: https://slon.prvms.ru/accounts/signup/
- [ ] **Вход**: https://slon.prvms.ru/accounts/login/
- [ ] **Покупка слона** (базовый тариф)
- [ ] **Покупка слона** (с выбором оттенка)
- [ ] **Личный кабинет**: https://slon.prvms.ru/dashboard/
- [ ] **Admin панель**: https://slon.prvms.ru/admin/
- [ ] **API документация**: https://slon.prvms.ru/api/docs

### Шаг 9: Настройка OAuth (опционально)

Если используете Google/Apple OAuth:

#### Google OAuth

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте OAuth 2.0 Client ID
3. Authorized redirect URIs:
   ```
   https://slon.prvms.ru/accounts/google/login/callback/
   ```
4. Добавьте в `.env`:
   ```bash
   GOOGLE_CLIENT_ID=ваш_client_id
   GOOGLE_SECRET=ваш_secret
   ```

#### Apple OAuth

1. Перейдите в [Apple Developer](https://developer.apple.com/)
2. Настройте Sign in with Apple
3. Return URLs:
   ```
   https://slon.prvms.ru/accounts/apple/login/callback/
   ```
4. Добавьте в `.env`:
   ```bash
   APPLE_CLIENT_ID=ваш_service_id
   APPLE_SECRET=ваш_secret
   ```

После изменения `.env`:
```bash
docker-compose -f docker-compose.prod.yml restart web
```

---

## 🔧 Troubleshooting

### Проблема: DNS не резолвится

```bash
# Проверьте DNS
dig slon.prvms.ru
nslookup slon.prvms.ru

# Очистите DNS кэш (на сервере)
sudo systemd-resolve --flush-caches  # Ubuntu/Debian
sudo dscacheutil -flushcache          # macOS
```

**Решение**: Подождите 5-10 минут для распространения DNS

### Проблема: 502 Bad Gateway

```bash
# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs nginx

# Проверьте что контейнеры в правильной сети
docker network inspect nginx-proxy
```

**Решение**: Убедитесь что `kupi_slona_nginx` в сети `nginx-proxy`

### Проблема: SSL сертификат не выдаётся

**Причины:**
1. DNS ещё не обновился (подождите)
2. Порты 80/443 закрыты firewall
3. Let's Encrypt rate limit (5 попыток/час)

```bash
# Проверьте firewall
sudo ufw status

# Откройте порты если нужно
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Проблема: Static файлы не загружаются

```bash
# Пересоберите статику
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Проверьте права
docker-compose -f docker-compose.prod.yml exec nginx ls -la /app/staticfiles/

# Рестарт nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Проблема: CSRF verification failed

**В .env должно быть:**
```bash
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru
```

После изменения:
```bash
docker-compose -f docker-compose.prod.yml restart web
```

---

## 📊 Мониторинг

### Логи в реальном времени

```bash
# Все сервисы
docker-compose -f docker-compose.prod.yml logs -f

# Только web
docker-compose -f docker-compose.prod.yml logs -f web

# Только celery
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# Последние 100 строк
docker-compose -f docker-compose.prod.yml logs --tail=100 web
```

### Статус сервисов

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Использование ресурсов
docker stats kupi_slona_web kupi_slona_db kupi_slona_redis

# Проверка здоровья
docker-compose -f docker-compose.prod.yml exec web python manage.py check
```

### Бэкапы

```bash
# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres elephant_shop > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres elephant_shop

# Бэкап media файлов
tar -czf media_backup_$(date +%Y%m%d).tar.gz -C $(docker volume inspect kupi_slona_media_volume -f '{{.Mountpoint}}') .
```

---

## ✅ Checklist развёртывания

- [ ] DNS настроен (A record для slon.prvms.ru)
- [ ] `.env` файл создан и настроен
- [ ] `DEBUG=False` в `.env`
- [ ] `SECRET_KEY` сгенерирован
- [ ] `DB_PASSWORD` установлен
- [ ] Docker сеть `nginx-proxy` создана
- [ ] Приложение задеплоено (`./deploy.sh`)
- [ ] Миграции применены
- [ ] Статика собрана
- [ ] Суперюзер создан
- [ ] Nginx Proxy Manager настроен
- [ ] SSL сертификат получен
- [ ] Firewall настроен (порты 80, 443)
- [ ] Сайт доступен по https://slon.prvms.ru
- [ ] Регистрация работает
- [ ] Покупка слона работает
- [ ] OAuth настроен (если используется)
- [ ] Бэкапы настроены

---

## 🎉 Готово!

Ваш Kupi Slona работает на **https://slon.prvms.ru** с SSL сертификатом!

### Следующие шаги:

1. **Настройте мониторинг** (Sentry, Prometheus, Grafana)
2. **Настройте автоматические бэкапы** (cron job)
3. **Настройте email уведомления**
4. **Добавьте Google Analytics** (если нужно)

### Полезные ссылки:

- **Сайт**: https://slon.prvms.ru
- **Admin**: https://slon.prvms.ru/admin/
- **API Docs**: https://slon.prvms.ru/api/docs
- **Nginx Proxy Manager**: http://IP_СЕРВЕРА:81
