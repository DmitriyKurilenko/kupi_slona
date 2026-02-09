# 🌐 Руководство по добавлению субдоменов

## DNS: Два способа

### ⭐ Способ 1: Wildcard DNS (Рекомендуется)

**Один раз настроили → все субдомены работают!**

#### В панели DNS вашего провайдера:

```
Тип:     A
Имя:     *
Значение: 123.456.789.0 (IP вашего сервера)
TTL:     300
```

**Готово!** Теперь все субдомены автоматически указывают на ваш сервер:
- slon.prvms.ru
- blog.prvms.ru
- api.prvms.ru
- любой.prvms.ru

#### Проверка:

```bash
# Все вернут ваш IP
nslookup slon.prvms.ru
nslookup blog.prvms.ru
nslookup новый-сервис.prvms.ru
```

---

### Способ 2: Отдельные A records

**Для каждого субдомена создаёте запись:**

```
Тип: A, Имя: slon,    Значение: IP_СЕРВЕРА
Тип: A, Имя: blog,    Значение: IP_СЕРВЕРА
Тип: A, Имя: api,     Значение: IP_СЕРВЕРА
Тип: A, Имя: traefik, Значение: IP_СЕРВЕРА
```

---

## 🚀 Пример: 5 приложений на одном сервере

### Архитектура:

```
┌─────────────────────────────────────────────┐
│         IP: 123.456.789.0                   │
│         DNS: *.prvms.ru → 123.456.789.0     │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   Traefik :80/443 │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┬──────────────┐
    │              │              │              │              │
    ▼              ▼              ▼              ▼              ▼
slon.prvms.ru  blog.prvms.ru  db.prvms.ru  status.prvms.ru  docker.prvms.ru
 Django        WordPress       Adminer      Uptime Kuma      Portainer
```

---

## 📋 Добавление нового субдомена

### Шаг 1: DNS уже настроен (wildcard)

✅ Если используете `*.prvms.ru` → ничего делать не нужно!

### Шаг 2: Добавьте сервис в docker-compose

**Пример: Добавляем Grafana на monitoring.prvms.ru**

```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SERVER_ROOT_URL=https://monitoring.prvms.ru
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik-public"

      # monitoring.prvms.ru
      - "traefik.http.routers.grafana.rule=Host(`monitoring.prvms.ru`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"

volumes:
  grafana_data:

networks:
  traefik-public:
    external: true
```

### Шаг 3: Запустите

```bash
docker-compose up -d grafana
```

### Шаг 4: Готово!

Traefik автоматически:
- ✅ Обнаружил новый контейнер
- ✅ Настроил маршрутизацию
- ✅ Получил SSL сертификат от Let's Encrypt
- ✅ Добавил в Dashboard

Откройте: **https://monitoring.prvms.ru** 🎉

---

## 🎯 Готовые примеры субдоменов

### 1. slon.prvms.ru - Django приложение

```yaml
kupi_slona_web:
  labels:
    - "traefik.http.routers.kupi-slona.rule=Host(`slon.prvms.ru`)"
    - "traefik.http.routers.kupi-slona.tls.certresolver=letsencrypt"
```

### 2. blog.prvms.ru - WordPress

```yaml
wordpress:
  labels:
    - "traefik.http.routers.blog.rule=Host(`blog.prvms.ru`)"
    - "traefik.http.routers.blog.tls.certresolver=letsencrypt"
```

### 3. api.prvms.ru - FastAPI микросервис

```yaml
fastapi:
  image: tiangolo/uvicorn-gunicorn-fastapi:python3.11
  labels:
    - "traefik.http.routers.api.rule=Host(`api.prvms.ru`)"
    - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```

### 4. traefik.prvms.ru - Dashboard

```yaml
traefik:
  labels:
    - "traefik.http.routers.traefik-dashboard.rule=Host(`traefik.prvms.ru`)"
    - "traefik.http.routers.traefik-dashboard.service=api@internal"
    - "traefik.http.routers.traefik-dashboard.middlewares=dashboard-auth"
```

### 5. db.prvms.ru - Adminer (database admin)

```yaml
adminer:
  image: adminer:latest
  labels:
    - "traefik.http.routers.adminer.rule=Host(`db.prvms.ru`)"
    - "traefik.http.routers.adminer.tls.certresolver=letsencrypt"
    # Basic Auth для безопасности
    - "traefik.http.routers.adminer.middlewares=adminer-auth"
    - "traefik.http.middlewares.adminer-auth.basicauth.users=admin:$$apr1$$xyz..."
```

---

## 🛠️ Готовый пример: Запустите 5 приложений

```bash
# 1. Настройте Wildcard DNS
# *.prvms.ru → ваш_IP

# 2. Убедитесь что Traefik запущен
docker network create traefik-public
docker-compose -f docker-compose.traefik.yml up -d

# 3. Запустите множество приложений
docker-compose -f docker-compose.multi-apps.yml up -d

# 4. Готово! Откройте:
# https://slon.prvms.ru       - Kupi Slona
# https://blog.prvms.ru       - WordPress
# https://db.prvms.ru         - Adminer
# https://status.prvms.ru     - Uptime Kuma
# https://docker.prvms.ru     - Portainer
# https://traefik.prvms.ru    - Traefik Dashboard
```

**6 приложений, 6 SSL сертификатов, 0 ручных настроек!** 🚀

---

## 🔐 Безопасность субдоменов

### Basic Authentication

Защитите админские субдомены паролем:

```bash
# Генерация пароля
echo $(htpasswd -nb admin yourpassword) | sed -e s/\\$/\\$\\$/g
```

```yaml
labels:
  # Защита паролем
  - "traefik.http.routers.admin.middlewares=admin-auth"
  - "traefik.http.middlewares.admin-auth.basicauth.users=admin:$$apr1$$..."
```

### IP Whitelist

Разрешите доступ только с определённых IP:

```yaml
labels:
  # Только с этих IP
  - "traefik.http.routers.admin.middlewares=admin-whitelist"
  - "traefik.http.middlewares.admin-whitelist.ipwhitelist.sourcerange=1.2.3.4/32,5.6.7.8/32"
```

### Rate Limiting

Ограничьте количество запросов:

```yaml
labels:
  # Максимум 100 запросов в секунду
  - "traefik.http.routers.api.middlewares=api-ratelimit"
  - "traefik.http.middlewares.api-ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.api-ratelimit.ratelimit.burst=50"
```

---

## 📊 Мониторинг субдоменов

### Traefik Dashboard

**https://traefik.prvms.ru**

Вы увидите:
- Все активные роутеры (субдомены)
- SSL сертификаты и их срок
- Статус сервисов
- Количество запросов

### Uptime Kuma

Мониторинг доступности:

```yaml
uptime_kuma:
  image: louislam/uptime-kuma:latest
  labels:
    - "traefik.http.routers.status.rule=Host(`status.prvms.ru`)"
```

Добавьте проверки для всех субдоменов!

---

## 🐛 Troubleshooting

### Проблема: Субдомен не работает

**Проверка 1: DNS**
```bash
nslookup новый-субдомен.prvms.ru
# Должен вернуть IP вашего сервера
```

**Проверка 2: Traefik обнаружил контейнер**
```bash
# Откройте Dashboard
https://traefik.prvms.ru

# Или проверьте логи
docker logs traefik | grep новый-субдомен
```

**Проверка 3: Контейнер в правильной сети**
```bash
docker network inspect traefik-public
# Должен содержать ваш контейнер
```

### Проблема: SSL не выдаётся

**Причины:**
1. DNS ещё не обновился (подождите 5-10 минут)
2. Let's Encrypt rate limit (5 сертификатов/час на домен)
3. Порты 80/443 закрыты

**Решение:**
```bash
# Проверьте порты
sudo netstat -tlnp | grep ':80\|:443'

# Проверьте ACME логи
docker logs traefik | grep -i acme

# Проверьте rate limit
https://crt.sh/?q=prvms.ru
```

---

## ✅ Checklist для нового субдомена

- [ ] DNS настроен (wildcard `*` или отдельный A record)
- [ ] Docker сеть `traefik-public` существует
- [ ] Traefik запущен
- [ ] В docker-compose добавлены labels с `Host()`
- [ ] Контейнер в сети `traefik-public`
- [ ] `traefik.enable=true` в labels
- [ ] Порт контейнера указан в labels
- [ ] Сервис запущен (`docker-compose up -d`)
- [ ] DNS обновился (5-10 минут)
- [ ] SSL сертификат получен
- [ ] Субдомен доступен по HTTPS

---

## 📚 Полезные ссылки

- **Множество приложений**: [docker-compose.multi-apps.yml](docker-compose.multi-apps.yml)
- **Traefik инструкция**: [TRAEFIK_SETUP.md](TRAEFIK_SETUP.md)
- **Quick Start**: [TRAEFIK_QUICKSTART.md](TRAEFIK_QUICKSTART.md)

---

## 🎉 Итого

С **Wildcard DNS** + **Traefik**:

```
Добавить субдомен = 3 строки labels в docker-compose.yml
```

**Без GUI! Без ручных настроек! Всё автоматически!** 🚀
