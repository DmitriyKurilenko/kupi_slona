# 🚀 Production Deploy Checklist

## Предварительно

- [ ] DNS: A-запись домена → IP сервера
- [ ] Порты 80 и 443 открыты в firewall
- [ ] Docker и docker-compose установлены на сервере

## На сервере (3 шага)

### 1️⃣ Клонируй репозиторий
```bash
cd ~
git clone <repo-url> kupi_slona
cd kupi_slona
```

### 2️⃣ Настрой .env
```bash
./setup-env.sh
```

Установи обязательные переменные:
```bash
DOMAIN=kupislona.prvms.ru
SSL_EMAIL=admin@prvms.ru

DEBUG=False
SECRET_KEY=<генерируй-командой-ниже>
DB_PASSWORD=<сильный-пароль>
```

Сгенерировать SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3️⃣ Запусти init и deploy
```bash
./init-letsencrypt.sh  # Получит SSL сертификат (30-60 сек)
./auto-deploy.sh       # Запустит приложение
```

✅ **Готово!** Сайт доступен на https://твой-домен.ru

---

## Проверка

```bash
# Контейнеры запущены?
docker-compose -f docker-compose.prod.yml ps

# Сайт доступен?
curl -I https://твой-домен.ru

# Сертификат получен?
docker-compose -f docker-compose.prod.yml run --rm certbot certificates
```

---

## Если что-то не работает

### Проблема: "No renewals were attempted"
```bash
# Проверь что DOMAIN и SSL_EMAIL в .env
cat .env | grep -E "^DOMAIN=|^SSL_EMAIL="

# Если пусто - запусти setup заново
./setup-env.sh

# Потом init заново
./init-letsencrypt.sh
```

### Полная диагностика
```bash
./diagnose.sh
```

---

## GitHub Actions (автодеплой)

В Settings → Secrets добавь:
- `SSH_PRIVATE_KEY` - SSH ключ для доступа к серверу
- `SSH_HOST` - IP или домен сервера
- `SSH_USER` - пользователь (обычно root или ubuntu)

После этого каждый push в `main` будет автоматически деплоиться!

---

## Полезные команды

```bash
# Логи
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f nginx

# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление кода
git pull && ./auto-deploy.sh

# Создать суперпользователя
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```
