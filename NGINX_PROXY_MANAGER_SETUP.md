# Настройка Kupi Slona с Nginx Proxy Manager

## 📋 Пошаговая инструкция

### 1. Создайте внешнюю Docker сеть

```bash
docker network create nginx-proxy
```

Эта сеть позволит Nginx Proxy Manager общаться с вашим приложением.

### 2. Обновите .env файл

Добавьте ваш домен в `.env`:

```bash
# Production settings
DEBUG=False
SECRET_KEY=your-super-secret-key-here-change-this

# Домены
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (используйте сильный пароль!)
DB_PASSWORD=strong_password_here

# PostgreSQL settings
DB_HOST=db
DB_NAME=elephant_shop
DB_USER=postgres
DB_PORT=5432

# Redis/Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_URL=redis://redis:6379/1
```

### 3. Соберите и запустите production версию

```bash
# Остановите dev версию если запущена
docker-compose down

# Соберите production версию
docker-compose -f docker-compose.prod.yml build

# Запустите
docker-compose -f docker-compose.prod.yml up -d

# Примените миграции
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Соберите статику
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Создайте суперюзера
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 4. Настройка в Nginx Proxy Manager

#### 4.1 Добавьте Proxy Host

1. Откройте Nginx Proxy Manager (обычно на порту 81)
2. Перейдите в **Hosts → Proxy Hosts**
3. Нажмите **Add Proxy Host**

#### 4.2 Заполните настройки:

**Tab: Details**
- **Domain Names**: `yourdomain.com`, `www.yourdomain.com`
- **Scheme**: `http`
- **Forward Hostname / IP**: `kupi_slona_nginx` (имя контейнера nginx)
- **Forward Port**: `80`
- ✅ **Cache Assets**
- ✅ **Block Common Exploits**
- ✅ **Websockets Support** (опционально)

**Tab: SSL**
- ✅ **SSL Certificate**: Выберите или создайте новый Let's Encrypt сертификат
- ✅ **Force SSL**
- ✅ **HTTP/2 Support**
- ✅ **HSTS Enabled**

**Tab: Advanced** (опционально):
```nginx
# Увеличить размер загрузки файлов
client_max_body_size 20M;

# Security headers (если нужны дополнительные)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

#### 4.3 Сохраните и проверьте

Нажмите **Save** и проверьте доступность на `https://yourdomain.com`

### 5. Проверка работоспособности

```bash
# Проверьте статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# Проверьте сеть
docker network inspect nginx-proxy
```

Вы должны увидеть контейнеры `kupi_slona_nginx` и `kupi_slona_web` в сети.

### 6. Тестирование

✅ Проверьте основные функции:
- [ ] Главная страница загружается
- [ ] Регистрация/вход работают
- [ ] Покупка слона (basic + advanced)
- [ ] Static файлы загружаются (CSS, JS, изображения)
- [ ] Media файлы отдаются корректно
- [ ] Error pages (403, 404, 500) отображаются правильно
- [ ] SSL сертификат валидный (зелёный замок)

### 7. Мониторинг и обслуживание

```bash
# Просмотр логов в реальном времени
docker-compose -f docker-compose.prod.yml logs -f

# Рестарт сервисов
docker-compose -f docker-compose.prod.yml restart

# Обновление после изменений
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres elephant_shop > backup.sql

# Восстановление базы
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres elephant_shop
```

## 🔧 Альтернативная конфигурация (без внутреннего Nginx)

Если хотите, чтобы Nginx Proxy Manager напрямую проксировал на Gunicorn:

1. В `docker-compose.prod.yml` измените web сервис:
   ```yaml
   web:
     # ... остальное без изменений
     expose:
       - "8000"
   ```

2. Закомментируйте/удалите nginx сервис

3. В Nginx Proxy Manager используйте:
   - **Forward Hostname / IP**: `kupi_slona_web`
   - **Forward Port**: `8000`

4. В Nginx Proxy Manager → Advanced добавьте:
   ```nginx
   location /static/ {
       proxy_pass http://kupi_slona_web:8000/static/;
       expires 30d;
   }

   location /media/ {
       proxy_pass http://kupi_slona_web:8000/media/;
       expires 7d;
   }
   ```

⚠️ **Внимание**: Этот вариант менее эффективен для отдачи статики.

## 🐛 Troubleshooting

### Проблема: 502 Bad Gateway

**Решение:**
```bash
# Проверьте что web контейнер запущен
docker-compose -f docker-compose.prod.yml ps web

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs web

# Убедитесь что контейнеры в правильной сети
docker network inspect nginx-proxy
```

### Проблема: Static файлы не загружаются

**Решение:**
```bash
# Пересоберите статику
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Проверьте права доступа
docker-compose -f docker-compose.prod.yml exec nginx ls -la /app/staticfiles/
```

### Проблема: CSRF verification failed

**Решение:**
Убедитесь что в `.env`:
```bash
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com
```

### Проблема: SSL сертификат не работает

**Решение:**
1. Убедитесь что домен указывает на ваш сервер (проверьте DNS)
2. Порты 80 и 443 открыты в firewall
3. В Nginx Proxy Manager переcоздайте SSL сертификат

## 📊 Рекомендуемые настройки для production

### Firewall

```bash
# Разрешить только необходимые порты
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 81/tcp  # Nginx Proxy Manager admin panel
sudo ufw enable
```

### Docker limits

В `docker-compose.prod.yml` добавьте ресурсные лимиты:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Логирование

Настройте ротацию логов в `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## ✅ Checklist перед запуском

- [ ] `.env` файл настроен с production значениями
- [ ] `DEBUG=False` в `.env`
- [ ] Сильный `SECRET_KEY` сгенерирован
- [ ] `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` настроены
- [ ] Docker сеть `nginx-proxy` создана
- [ ] Миграции применены
- [ ] Статика собрана
- [ ] Суперюзер создан
- [ ] SSL сертификат настроен
- [ ] Firewall настроен
- [ ] Бэкапы базы настроены

## 🎉 Готово!

Ваш Kupi Slona проект готов к работе через Nginx Proxy Manager с SSL!
