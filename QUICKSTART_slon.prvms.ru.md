# 🚀 Quick Start для slon.prvms.ru

## Перед началом

✅ **DNS настроен**: A record `slon` → IP сервера
✅ **Nginx Proxy Manager установлен** на сервере

---

## 3 простых шага

### 1. Подготовка (1 минута)

```bash
# Скопируйте настройки
cp .env.slon.prvms.ru .env

# Отредактируйте (измените пароли!)
nano .env

# Создайте сеть Docker
docker network create nginx-proxy
```

### 2. Деплой (2-3 минуты)

```bash
# Запустите автоматический деплой
./deploy.sh

# Создайте админа
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 3. Настройка Nginx Proxy Manager (1 минута)

**Откройте**: http://IP_СЕРВЕРА:81

**Add Proxy Host**:
```
Domain:     slon.prvms.ru
Forward to: kupi_slona_nginx:80
SSL:        ✅ Let's Encrypt
Force SSL:  ✅
```

**Готово!** → https://slon.prvms.ru 🎉

---

## Важные настройки в .env

```bash
# Обязательно измените:
SECRET_KEY=длинный-случайный-ключ-50-символов
DB_PASSWORD=сильный-пароль

# Проверьте:
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru
DEBUG=False
```

---

## Полезные команды

```bash
# Логи
docker-compose -f docker-compose.prod.yml logs -f web

# Рестарт
docker-compose -f docker-compose.prod.yml restart

# Статус
docker-compose -f docker-compose.prod.yml ps

# Бэкап БД
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres elephant_shop > backup.sql
```

---

## Тестирование

Откройте в браузере:
- ✅ https://slon.prvms.ru - главная
- ✅ https://slon.prvms.ru/admin/ - админка
- ✅ https://slon.prvms.ru/dashboard/ - личный кабинет

---

📖 **Подробная инструкция**: [SETUP_SUBDOMAIN.md](SETUP_SUBDOMAIN.md)
