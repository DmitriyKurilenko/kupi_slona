# 🚀 Быстрая настройка Production

## На сервере:

### 1. Клонируй и настрой .env

```bash
cd ~
git clone <repo-url> kupi_slona
cd kupi_slona

# Вариант 1: Автоматическая настройка (рекомендуется)
./setup-env.sh

# Вариант 2: Ручная настройка
# cp .env.example .env
# nano .env
```

**ОБЯЗАТЕЛЬНО установи в .env:**
```bash
# Production Domain (первые 2 строки - ОБЯЗАТЕЛЬНЫ для SSL!)
DOMAIN=kupislona.prvms.ru
SSL_EMAIL=admin@prvms.ru

# Django Settings
DEBUG=False
SECRET_KEY=<твой-секретный-ключ>
ALLOWED_HOSTS=kupislona.prvms.ru
CSRF_TRUSTED_ORIGINS=https://kupislona.prvms.ru

# Database
DB_PASSWORD=<сильный-пароль>
```

**Проверь что DOMAIN и SSL_EMAIL установлены:**
```bash
grep -E "^DOMAIN=|^SSL_EMAIL=" .env
# Должно показать:
# DOMAIN=kupislona.prvms.ru
# SSL_EMAIL=admin@prvms.ru
```

### 2. Запусти init для SSL

```bash
./init-letsencrypt.sh
```

Скрипт автоматически:
- Прочитает DOMAIN и SSL_EMAIL из .env
- Создаст nginx конфиг
- Получит SSL сертификат
- Настроит HTTPS

### 3. Задеплой приложение

```bash
./auto-deploy.sh
```

Готово! Сайт доступен на https://kupislona.prvms.ru

---

## Как это работает:

1. **Все настройки в .env** - один файл, одно место
2. **init-letsencrypt.sh** читает DOMAIN и SSL_EMAIL из .env
3. **nginx/conf.d/default.conf** генерируется автоматически (не в git)
4. **Никаких хардкодов** - всё через переменные

---

## Если что-то не работает:

### Проблема: "No renewals were attempted" или сертификат не получен

```bash
# 1. Проверь что .env файл существует и содержит DOMAIN и SSL_EMAIL
cat .env | grep -E "^DOMAIN=|^SSL_EMAIL="

# Если пусто или файла нет:
./setup-env.sh

# 2. Проверь что домен доступен по HTTP (port 80)
curl -I http://ваш-домен.ru

# 3. Проверь логи nginx
docker-compose -f docker-compose.prod.yml logs nginx | tail -50

# 4. Запусти init заново
./init-letsencrypt.sh
```

### Другие проблемы:

```bash
# Проверь контейнеры
docker-compose -f docker-compose.prod.yml ps

# Проверь логи web
docker-compose -f docker-compose.prod.yml logs web | tail -50

# Полная диагностика
./diagnose.sh

# Перезапусти всё
docker-compose -f docker-compose.prod.yml down
./init-letsencrypt.sh
./auto-deploy.sh
```

---

## Смена домена:

1. Измени DOMAIN в .env
2. Запусти: `./init-letsencrypt.sh`
3. Готово!
