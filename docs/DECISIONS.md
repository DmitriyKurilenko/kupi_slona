# Архитектурные решения

## Стек

- **Backend Framework**: Django 5.1 + django-ninja 1.3 (декларативный REST API с автодокументацией)
- **Async Tasks**: Celery 5.4 + Redis 7 (брокер и result backend)
- **Database**: PostgreSQL 16
- **Cache**: Django RedisCache (Redis DB 1)
- **Frontend**: Alpine.js + DaisyUI (поверх Tailwind CSS), HTML-шаблоны Django
- **Web Server**: Nginx (reverse proxy, SSL) + Gunicorn (WSGI)
- **Static/Media**: WhiteNoise (production static) + Nginx (media проксирование)
- **Image Generation**: CairoSVG (SVG → PNG), Pillow
- **Payments**: YooKassa (юкасса) — российский платёжный провайдер
- **Auth**: django-allauth (OAuth Google + email/password)
- **Deployment**: Docker + docker-compose, GitHub Actions CI/CD

## API

- **Framework**: Django Ninja (Router-based, Pydantic schemas)
- **Auth**: session-based через `ninja.security.django_auth`, централизовано в `apps/core/auth.py`
- **Структура**: каждое приложение имеет `api.py` (роутер), `schemas.py` (Pydantic)
- **Регистрация роутеров**: `config/urls.py`
  - `/api/auth/` — accounts
  - `/api/elephants/` — elephants
  - `/api/` — payments (tariffs, orders)
  - `/api/gifts/` — gifts
- **Public endpoints**: health check (`/health/`), gift public page (`/gift/public/<uuid>`), YooKassa webhook (`/api/payments/webhook`)

## Структура backend

- **Монолит с bounded contexts**: `apps/` — каждое приложение = отдельный домен
  - `accounts` — регистрация, вход, OAuth (Google), social connections
  - `elephants` — модель Elephant, генерация изображений, цветовая логика
  - `payments` — Tariff, Order, интеграция YooKassa
  - `gifts` — GiftLink, UUID-based публичные ссылки
  - `core` — shared: auth декоратор, context processors
- **Fat Models**: бизнес-логика в моделях (валидация `clean()`, методы `mark_as_paid()`, `transfer_ownership()`)
- **Service Layer**: сложная логика вынесена в `services.py` (elephants, payments, gifts)
- **Signals**: `apps/elephants/signals.py`, `apps/accounts/signals.py` для side-effects
- **Celery Tasks**: `apps/elephants/tasks.py::generate_elephant_image` — асинхронная генерация после оплаты

## Асинхронность

- **Celery Worker**: отдельный контейнер `celery_worker`, запускает задачи из `tasks.py`
- **Брокер**: Redis (DB 0)
- **Result Backend**: Redis (DB 0)
- **Основная задача**: `generate_elephant_image(order_id)` — после webhook-оплаты YooKassa запускается генерация PNG, обновление Order.status
- **Retry policy**: `max_retries=3`, экспоненциальная задержка `countdown=60 * (2 ** retries)`
- **Concurrency**: `CELERY_WORKER_PREFETCH_MULTIPLIER = 1` (одна задача за раз), `acks_late=True`

## Локализация

- **Язык интерфейса**: `ru-RU`
- **Часовой пояс**: `Europe/Moscow`
- **Django**: `LANGUAGE_CODE = 'ru-RU'`, `TIME_ZONE = 'Europe/Moscow'`, `USE_I18N = True`, `USE_TZ = True`
- **verbose_name** у всех моделей на русском

## Безопасность

- **CSRF**: включён для всех POST/форм, `CSRF_TRUSTED_ORIGINS` настроен, `CSRF_COOKIE_HTTPONLY=False` (JS читает токен), `CSRF_COOKIE_SAMESITE=Lax`
- **Sessions**: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE=Lax`, `SESSION_COOKIE_AGE=86400` (24ч), DB-backed sessions
- **Production hardening**: `SECURE_SSL_REDIRECT` (контролируется env), `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `X_FRAME_OPTIONS=DENY`
- **Reverse Proxy**: `USE_X_FORWARDED_HOST=True`, `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https')`
- **Auth**: django-allauth с email-only регистрацией (`ACCOUNT_AUTHENTICATION_METHOD='email'`, `ACCOUNT_EMAIL_VERIFICATION='none'`), OAuth Google (`profile`, `email` scope)
- **Password validation**: встроенные валидаторы Django (длина, распространённые пароли, similarity)
- **YooKassa webhook**: не требует аутентификации, всегда возвращает 200 (чтобы избежать retries), обработка подписи/тела — в `yookassa_service.py`
- **Owner checks**: все API endpoints проверяют владельца ресурса через service layer
