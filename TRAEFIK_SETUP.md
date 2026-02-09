# 🚀 Настройка Kupi Slona с Traefik

## Что такое Traefik?

**Traefik** - современный reverse proxy с автоматическим обнаружением сервисов через Docker labels.

### Преимущества Traefik:
- ✅ **Автоматическое обнаружение** - добавили контейнер → он сразу доступен
- ✅ **Infrastructure as Code** - вся конфигурация в docker-compose.yml
- ✅ **Автоматический SSL** - Let's Encrypt из коробки
- ✅ **Dashboard** - мониторинг роутов в реальном времени
- ✅ **Масштабируемость** - легко добавлять новые сервисы

---

## 📋 Пошаговая настройка

### Шаг 1: DNS настройка

Создайте A records для субдоменов:

```
Тип: A
Имя: slon
Значение: IP_ВАШЕГО_СЕРВЕРА

Тип: A
Имя: traefik
Значение: IP_ВАШЕГО_СЕРВЕРА
```

**Результат:**
- `slon.prvms.ru` → Kupi Slona приложение
- `traefik.prvms.ru` → Traefik Dashboard

Проверка:
```bash
nslookup slon.prvms.ru
nslookup traefik.prvms.ru
```

### Шаг 2: Подготовка .env

```bash
# Скопируйте шаблон
cp .env.slon.prvms.ru .env

# Отредактируйте
nano .env
```

Добавьте в `.env`:
```bash
# Email для Let's Encrypt (обязательно!)
ACME_EMAIL=admin@prvms.ru

# Django settings
DEBUG=False
SECRET_KEY=ваш-секретный-ключ
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru

# Database
DB_PASSWORD=сильный-пароль
```

### Шаг 3: Сгенерируйте пароль для Traefik Dashboard

```bash
# Установите htpasswd (если нет)
sudo apt-get install apache2-utils  # Ubuntu/Debian
brew install httpd                   # macOS

# Сгенерируйте пароль
echo $(htpasswd -nb admin ваш_пароль) | sed -e s/\\$/\\$\\$/g

# Скопируйте результат
# Например: admin:$$apr1$$xyz...
```

Замените в `docker-compose.traefik.yml` строку 68:
```yaml
- "traefik.http.middlewares.dashboard-auth.basicauth.users=admin:$$apr1$$ВАШ_HASH"
```

### Шаг 4: Запуск

```bash
# Соберите образы
docker-compose -f docker-compose.traefik.yml build

# Запустите всё
docker-compose -f docker-compose.traefik.yml up -d

# Проверьте статус
docker-compose -f docker-compose.traefik.yml ps

# Все контейнеры должны быть "Up"
```

### Шаг 5: Миграции и статика

```bash
# Применить миграции
docker-compose -f docker-compose.traefik.yml exec web python manage.py migrate

# Собрать статику
docker-compose -f docker-compose.traefik.yml exec web python manage.py collectstatic --noinput

# Создать суперюзера
docker-compose -f docker-compose.traefik.yml exec web python manage.py createsuperuser
```

### Шаг 6: Проверка

#### 6.1 Traefik Dashboard

Откройте: **https://traefik.prvms.ru**

- Username: `admin`
- Password: `ваш_пароль`

Вы должны увидеть:
- HTTP Routers: kupi-slona, kupi-slona-static
- Services: kupi-slona, kupi-slona-static
- Certificates: slon.prvms.ru, traefik.prvms.ru

#### 6.2 Kupi Slona

Откройте: **https://slon.prvms.ru**

✅ Должно работать:
- SSL сертификат валиден 🔒
- Главная страница загружается
- Static файлы работают
- Редирект с HTTP на HTTPS

### Шаг 7: Логи

```bash
# Все сервисы
docker-compose -f docker-compose.traefik.yml logs -f

# Только Traefik
docker-compose -f docker-compose.traefik.yml logs -f traefik

# Только web
docker-compose -f docker-compose.traefik.yml logs -f web

# Последние 100 строк
docker-compose -f docker-compose.traefik.yml logs --tail=100
```

---

## 🎯 Добавление нового приложения (пример)

### Допустим, вы хотите добавить WordPress на blog.prvms.ru

#### 1. Создайте docker-compose.wordpress-traefik.yml

```yaml
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
      - wordpress_backend
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik-public"

      # HTTP роутер
      - "traefik.http.routers.wordpress-http.rule=Host(`blog.prvms.ru`)"
      - "traefik.http.routers.wordpress-http.entrypoints=web"

      # HTTPS роутер
      - "traefik.http.routers.wordpress.rule=Host(`blog.prvms.ru`)"
      - "traefik.http.routers.wordpress.entrypoints=websecure"
      - "traefik.http.routers.wordpress.tls.certresolver=letsencrypt"
      - "traefik.http.services.wordpress.loadbalancer.server.port=80"
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
  traefik-public:
    external: true
```

#### 2. Запустите

```bash
# Убедитесь что сеть traefik-public существует
docker network ls | grep traefik-public

# Запустите WordPress
docker-compose -f docker-compose.wordpress-traefik.yml up -d
```

#### 3. Готово!

Traefik **автоматически**:
- ✅ Обнаружит новый контейнер
- ✅ Настроит маршрутизацию
- ✅ Получит SSL сертификат
- ✅ Добавит в Dashboard

Откройте: **https://blog.prvms.ru** - WordPress уже работает!

**Никаких ручных настроек!** 🎉

---

## 🔧 Расширенные настройки

### Rate Limiting

Добавьте в labels web сервиса:

```yaml
labels:
  # ... существующие labels

  # Rate limit: 100 запросов в секунду
  - "traefik.http.middlewares.rate-limit.ratelimit.average=100"
  - "traefik.http.middlewares.rate-limit.ratelimit.burst=50"
  - "traefik.http.routers.kupi-slona.middlewares=kupi-slona-headers,kupi-slona-compress,rate-limit"
```

### IP Whitelist

Ограничить доступ к admin панели:

```yaml
labels:
  # ... существующие labels

  # Admin только с определённых IP
  - "traefik.http.middlewares.admin-whitelist.ipwhitelist.sourcerange=1.2.3.4/32,5.6.7.8/32"

  # Роутер для /admin
  - "traefik.http.routers.kupi-slona-admin.rule=Host(`slon.prvms.ru`) && PathPrefix(`/admin`)"
  - "traefik.http.routers.kupi-slona-admin.middlewares=admin-whitelist"
  - "traefik.http.routers.kupi-slona-admin.priority=200"
```

### Custom Domain для Static

Если хотите отдавать статику с CDN домена:

```yaml
labels:
  # Static на cdn.prvms.ru
  - "traefik.http.routers.kupi-slona-cdn.rule=Host(`cdn.prvms.ru`)"
  - "traefik.http.routers.kupi-slona-cdn.entrypoints=websecure"
  - "traefik.http.routers.kupi-slona-cdn.tls.certresolver=letsencrypt"
```

### CORS Headers

```yaml
labels:
  # CORS для API
  - "traefik.http.middlewares.cors.headers.accesscontrolallowmethods=GET,POST,PUT,DELETE,OPTIONS"
  - "traefik.http.middlewares.cors.headers.accesscontrolalloworiginlist=https://slon.prvms.ru"
  - "traefik.http.middlewares.cors.headers.accesscontrolmaxage=100"
  - "traefik.http.middlewares.cors.headers.addvaryheader=true"
```

---

## 📊 Мониторинг

### Traefik Metrics

Добавьте в command секцию traefik:

```yaml
command:
  # ... существующие команды

  # Prometheus metrics
  - "--metrics.prometheus=true"
  - "--metrics.prometheus.addEntryPointsLabels=true"
  - "--metrics.prometheus.addServicesLabels=true"
```

Метрики будут доступны на http://traefik:8080/metrics

### Grafana Dashboard

Используйте официальный Traefik Dashboard для Grafana:
- Dashboard ID: 4475
- https://grafana.com/grafana/dashboards/4475

---

## 🔒 Безопасность

### 1. Защита Docker Socket

**ВАЖНО!** `/var/run/docker.sock` даёт полный контроль над Docker.

Используйте Docker Socket Proxy:

```yaml
services:
  docker-socket-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: docker-socket-proxy
    environment:
      - CONTAINERS=1
      - NETWORKS=1
      - SERVICES=1
      - TASKS=1
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - docker-socket
    restart: unless-stopped

  traefik:
    # ...
    volumes:
      # - /var/run/docker.sock:/var/run/docker.sock:ro  # Удалить эту строку
    environment:
      - DOCKER_HOST=tcp://docker-socket-proxy:2375
    networks:
      - docker-socket
      - traefik-public
```

### 2. Firewall

```bash
# Разрешить только нужные порты
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 3. Fail2Ban для Traefik

```bash
# Установка
sudo apt-get install fail2ban

# Создайте /etc/fail2ban/filter.d/traefik-auth.conf
[Definition]
failregex = ^<HOST> \- \S+ \[\] \"(GET|POST|HEAD).*\" 401
ignoreregex =

# Создайте /etc/fail2ban/jail.local
[traefik-auth]
enabled = true
port = http,https
filter = traefik-auth
logpath = /var/log/traefik/access.log
maxretry = 3
bantime = 3600
```

---

## 🐛 Troubleshooting

### Проблема: SSL сертификат не выдаётся

**Причины:**
1. DNS ещё не обновился
2. Порты 80/443 закрыты
3. Let's Encrypt rate limit

**Решение:**
```bash
# Проверьте DNS
dig slon.prvms.ru

# Проверьте порты
sudo netstat -tlnp | grep ':80\|:443'

# Проверьте логи Traefik
docker-compose -f docker-compose.traefik.yml logs traefik | grep -i acme

# Удалите acme.json и попробуйте снова
docker-compose -f docker-compose.traefik.yml down
docker volume rm kupi_slona_traefik_letsencrypt
docker-compose -f docker-compose.traefik.yml up -d
```

### Проблема: 404 Not Found

**Решение:**
```bash
# Проверьте labels контейнера
docker inspect kupi_slona_web | grep -A 20 Labels

# Проверьте что контейнер в правильной сети
docker network inspect traefik-public

# Проверьте Dashboard
https://traefik.prvms.ru
```

### Проблема: Static файлы не загружаются

**Решение:**
```bash
# Проверьте nginx контейнер
docker-compose -f docker-compose.traefik.yml logs nginx

# Проверьте volume
docker volume inspect kupi_slona_static_volume

# Пересоберите статику
docker-compose -f docker-compose.traefik.yml exec web python manage.py collectstatic --noinput
```

---

## ✅ Checklist

- [ ] DNS настроен (slon.prvms.ru, traefik.prvms.ru)
- [ ] `.env` создан и настроен
- [ ] `ACME_EMAIL` указан в `.env`
- [ ] Пароль для Dashboard сгенерирован
- [ ] `DEBUG=False` в `.env`
- [ ] Firewall настроен (порты 80, 443)
- [ ] Traefik запущен
- [ ] Приложение запущено
- [ ] Миграции применены
- [ ] Статика собрана
- [ ] Суперюзер создан
- [ ] SSL сертификаты получены
- [ ] Dashboard доступен (https://traefik.prvms.ru)
- [ ] Сайт работает (https://slon.prvms.ru)

---

## 📖 Полезные команды

```bash
# Запуск
docker-compose -f docker-compose.traefik.yml up -d

# Остановка
docker-compose -f docker-compose.traefik.yml down

# Рестарт
docker-compose -f docker-compose.traefik.yml restart

# Пересборка
docker-compose -f docker-compose.traefik.yml build
docker-compose -f docker-compose.traefik.yml up -d

# Логи
docker-compose -f docker-compose.traefik.yml logs -f

# Статус
docker-compose -f docker-compose.traefik.yml ps

# Бэкап БД
docker-compose -f docker-compose.traefik.yml exec db pg_dump -U postgres elephant_shop > backup.sql

# Проверка конфигурации
docker-compose -f docker-compose.traefik.yml config
```

---

## 🎉 Готово!

Ваш Kupi Slona работает через **Traefik** на https://slon.prvms.ru!

**Dashboard**: https://traefik.prvms.ru (admin / ваш_пароль)

### Что дальше?

1. **Добавьте мониторинг** (Prometheus + Grafana)
2. **Настройте бэкапы**
3. **Добавьте другие приложения** (просто добавьте labels!)
4. **Настройте Fail2Ban**
5. **Включите Docker Socket Proxy**
