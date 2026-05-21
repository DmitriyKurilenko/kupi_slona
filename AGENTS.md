# AGENTS: Protocol for This Repository

## Project Overview

**Elephant Color Shop (kupi_slona)** — веб-приложение для покупки уникальных изображений слонов, закрашенных определённым цветом из палитры RGB. Каждый цвет может быть куплен только один раз.

- **Версия**: 0.1.0 (MVP)
- **Репозиторий**: монолитный Django-проект с Docker-оркестрацией
- **Язык интерфейса**: русский (ru-RU)
- **Production domain**: `slon.prvms.ru`

### Структура репозитория

```
kupi_slona/
├── config/                  # Django настройки
│   ├── settings.py
│   ├── urls.py              # Корневые URL + Django Ninja API
│   ├── celery.py
│   └── wsgi.py
├── apps/                    # Django приложения (bounded contexts)
│   ├── accounts/            # Аутентификация (email + OAuth Google)
│   ├── core/                # Shared infrastructure (auth, context_processors)
│   ├── elephants/           # Слоны: модели, генерация изображений, API
│   ├── gifts/               # Подарочные ссылки (UUID-based)
│   └── payments/            # Тарифы, заказы, интеграция YooKassa
├── templates/               # HTML шаблоны (Jinja2/Django)
├── static/                  # Статика (Tailwind CSS, Alpine.js)
├── media/                   # Загруженные изображения слонов
├── nginx/                   # Nginx конфигурация (dev + prod)
├── logs/                    # Логи Django, Celery, приложений
├── scripts/                 # Backup/restore скрипты
├── docker-compose.yml       # Development
├── docker-compose.prod.yml  # Production
├── Dockerfile
├── requirements.txt
├── manage.py
├── .env.example
├── DEPLOY_CHECKLIST.md      # Production deploy guide
├── AGENTS.md                # ← этот файл
└── docs/                    # Живая документация проекта
    ├── DECISIONS.md
    ├── DEV_LOG.md
    ├── KNOWN_ISSUES.md
    ├── RELEASE_NOTES.md
    ├── TASK_STATE.md
    └── VERSIONING.md
```

## Mandatory Read Order Before Any Code Change
1. `docs/TASK_STATE.md`
2. `docs/DECISIONS.md`
3. `docs/KNOWN_ISSUES.md`
4. `docs/DEV_LOG.md` (latest entries first)
5. Current task file (`TASKS/*.md` when present)

If instructions conflict — STOP and ask user.

## Update Ritual (After Non-Trivial Changes)
1. `docs/DECISIONS.md` — если изменилось поведение/инвариант
2. `docs/TASK_STATE.md` — обновить статус (done/in-progress/blocked)
3. `docs/DEV_LOG.md` — дата, файлы, валидация, риски
4. `docs/KNOWN_ISSUES.md` — если найден или закрыт баг
5. `docs/RELEASE_NOTES.md` — если изменение видно пользователю:
   - Язык: русский
   - Группировка по дате → «Новое», «Улучшения», «Исправления»

## Validation Baseline (Docker)
1. `docker compose down`
2. `docker compose up -d --build`
3. `docker compose run --rm backend python manage.py check`
4. Targeted tests for changed modules
5. Manual HTTP check for affected pages

If any step fails — fix and rerun. Partial validation ≠ done.

## Decision Rules (Self-Limitation)
1. Если выполнение одной задачи занимает больше 2 итераций — остановись и спроси.
2. Если что-то непонятно из известных знаний — спроси.
3. Если не уверен на 100% что делать — спроси.
4. Если есть разные варианты решения — спроси.
5. Никогда не зацикливайся на одной проблеме. Если не нашлось решения за 2 итерации — спроси.
