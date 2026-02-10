# 🚀 Быстрая настройка Production

## На сервере:

### 1. Клонируй и настрой .env

```bash
cd ~
git clone <repo-url> kupi_slona
cd kupi_slona

# Создай .env из примера
cp .env.example .env

# Отредактируй .env - укажи DOMAIN и SSL_EMAIL
nano .env
```

**Обязательно укажи в .env:**
```bash
DOMAIN=kupislona.prvms.ru
SSL_EMAIL=admin@prvms.ru

DEBUG=False
SECRET_KEY=<твой-секретный-ключ>
ALLOWED_HOSTS=kupislona.prvms.ru
CSRF_TRUSTED_ORIGINS=https://kupislona.prvms.ru

DB_PASSWORD=<сильный-пароль>
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

```bash
# Проверь контейнеры
docker-compose -f docker-compose.prod.yml ps

# Проверь логи nginx
docker-compose -f docker-compose.prod.yml logs nginx

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
