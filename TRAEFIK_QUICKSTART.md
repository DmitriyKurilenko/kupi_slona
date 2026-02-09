# 🚀 Traefik Quick Start для slon.prvms.ru

## 3 простых шага

### 1. Подготовка (2 минуты)

```bash
# DNS: Создайте A records
# slon.prvms.ru → IP_СЕРВЕРА
# traefik.prvms.ru → IP_СЕРВЕРА

# Скопируйте .env
cp .env.slon.prvms.ru .env
nano .env

# Добавьте в .env:
ACME_EMAIL=admin@prvms.ru
DEBUG=False
SECRET_KEY=ваш-длинный-ключ
ALLOWED_HOSTS=slon.prvms.ru
CSRF_TRUSTED_ORIGINS=https://slon.prvms.ru
DB_PASSWORD=сильный-пароль
```

### 2. Генерация пароля для Dashboard

```bash
# Установите htpasswd (если нет)
sudo apt-get install apache2-utils

# Создайте пароль
echo $(htpasswd -nb admin yourpassword) | sed -e s/\\$/\\$\\$/g

# Результат вставьте в docker-compose.traefik.yml строка 68
```

### 3. Запуск (1 минута)

```bash
# Соберите и запустите
docker-compose -f docker-compose.traefik.yml build
docker-compose -f docker-compose.traefik.yml up -d

# Миграции и статика
docker-compose -f docker-compose.traefik.yml exec web python manage.py migrate
docker-compose -f docker-compose.traefik.yml exec web python manage.py collectstatic --noinput

# Создайте админа
docker-compose -f docker-compose.traefik.yml exec web python manage.py createsuperuser
```

## ✅ Готово!

- **Сайт**: https://slon.prvms.ru 🔒
- **Dashboard**: https://traefik.prvms.ru (admin/yourpassword)

---

## 🎯 Главное преимущество Traefik

### Добавить новое приложение = просто добавить labels!

**Пример: Добавляем WordPress на blog.prvms.ru**

```yaml
services:
  wordpress:
    image: wordpress:latest
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.blog.rule=Host(`blog.prvms.ru`)"
      - "traefik.http.routers.blog.entrypoints=websecure"
      - "traefik.http.routers.blog.tls.certresolver=letsencrypt"

networks:
  traefik-public:
    external: true
```

**Запустили** → **Traefik автоматически**:
- ✅ Обнаружил сервис
- ✅ Настроил роутинг
- ✅ Получил SSL сертификат

**Никаких ручных настроек!** 🎉

---

## 📊 Полезные команды

```bash
# Логи
docker-compose -f docker-compose.traefik.yml logs -f traefik
docker-compose -f docker-compose.traefik.yml logs -f web

# Статус
docker-compose -f docker-compose.traefik.yml ps

# Рестарт
docker-compose -f docker-compose.traefik.yml restart

# Проверка конфигурации
docker-compose -f docker-compose.traefik.yml config
```

---

## 🐛 Если что-то не работает

### SSL не выдаётся?
```bash
# Подождите 2-3 минуты после запуска
# Проверьте DNS
dig slon.prvms.ru

# Проверьте логи
docker-compose -f docker-compose.traefik.yml logs traefik | grep -i acme
```

### 404 Not Found?
```bash
# Проверьте Dashboard
https://traefik.prvms.ru

# Убедитесь что контейнер в сети traefik-public
docker network inspect traefik-public
```

---

📖 **Подробная документация**: [TRAEFIK_SETUP.md](TRAEFIK_SETUP.md)
