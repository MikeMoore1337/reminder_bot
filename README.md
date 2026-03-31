# Telegram reminder bot - прод версия

Готовый каркас Telegram-бота на Python, который:
- принимает напоминания от пользователей;
- хранит их в PostgreSQL;
- позволяет каждому пользователю задать свой часовой пояс;
- в нужное время отправляет сообщение с текстом напоминания;
- пишет структурированные логи в stdout;
- запускается на VPS через Docker Compose;
- поддерживает **polling** и **webhook**;
- использует **Alembic** для миграций.

## Стек
- Python 3.12
- aiogram 3.x
- PostgreSQL
- SQLAlchemy 2.x async
- Alembic
- aiohttp
- Docker Compose
- Nginx на VPS

## Команды
- `/start`
- `/help`
- `/timezone Europe/Moscow`
- `/mytimezone`
- `/remind 2026-03-31 18:30 Купить молоко`
- `/list`
- `/cancel 12`

Также поддерживается текстовый формат:
- `напомни 31.03.2026 18:30 купить молоко`

## Архитектура
Сервисы:
- `bot` - принимает апдейты Telegram;
- `worker` - выбирает просроченные напоминания и отправляет их;
- `db` - PostgreSQL;
- `migrate` - однократный сервис для `alembic upgrade head`.

Источник истины - PostgreSQL. Напоминания не теряются после рестартов контейнеров и VPS.

## Важные режимы запуска
### 1. Polling
Самый простой вариант для личного VPS.

В `.env`:
```env
BOT_MODE=polling
```

Запуск:
```bash
docker compose --profile tools run --rm migrate
docker compose up -d db bot worker
```

### 2. Webhook
Нужен домен и HTTPS. Telegram не отправляет webhook на обычный HTTP.

В `.env`:
```env
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://bot.example.com
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET_TOKEN=очень_длинный_секрет
APP_PORT=8080
```

Запуск такой же:
```bash
docker compose --profile tools run --rm migrate
docker compose up -d db bot worker
```

Nginx на VPS проксирует HTTPS на `127.0.0.1:8080`. Пример конфига: `deploy/nginx/reminder_bot.conf`.

## Настройка .env
Скопируй шаблон:
```bash
cp .env.example .env
```

Минимально обязательно заполнить:
```env
BOT_TOKEN=...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/reminder_bot
```

Для webhook ещё и это:
```env
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://bot.example.com
WEBHOOK_SECRET_TOKEN=long_random_secret
```

## Миграции Alembic
Первичная миграция уже добавлена.

Применить миграции:
```bash
docker compose --profile tools run --rm migrate
```

Создать новую миграцию позже:
```bash
docker compose run --rm bot alembic revision -m "add something"
```

## Логи
```bash
docker compose logs -f bot
docker compose logs -f worker
docker compose logs -f db
```

Пример логов:
```text
2026-03-30 20:45:00,123 | INFO | app.services.reminder_service | Created reminder | extra=reminder_id=5 user_id=10 remind_at_utc=2026-03-31T07:30:00+00:00
```

## Пошаговый деплой на VPS
### Вариант без webhook - проще и быстрее
1. Установить Docker и Docker Compose plugin.
2. Скопировать проект на сервер, например в `/opt/reminder_bot`.
3. Создать `.env`.
4. Выполнить:
```bash
cd /opt/reminder_bot
docker compose build
docker compose --profile tools run --rm migrate
docker compose up -d db bot worker
```
5. Проверить логи.

### Вариант с webhook + Nginx
1. Привязать домен к IP VPS.
2. Открыть порты 80 и 443 в firewall.
3. На сервере поднять проект и выставить `BOT_MODE=webhook`.
4. Поднять контейнеры:
```bash
docker compose build
docker compose --profile tools run --rm migrate
docker compose up -d db bot worker
```
5. Скопировать `deploy/nginx/reminder_bot.conf` в `/etc/nginx/sites-available/reminder_bot`.
6. Исправить `server_name` и пути к сертификатам.
7. Выпустить сертификат Let's Encrypt.
8. Включить сайт и перезапустить Nginx.
9. Проверить:
```bash
curl https://bot.example.com/healthz
```

## Что лучше для тебя на личном VPS
### Если нужен просто рабочий бот
Бери **polling**.
- проще настройка;
- не нужен домен;
- не нужен Nginx;
- для одного личного VPS этого обычно достаточно.

### Если нужен более боевой вариант
Бери **webhook + Nginx**.
- меньше лишних запросов к Telegram;
- нормальная внешняя точка входа;
- удобнее масштабировать и мониторить.

## Что уже улучшено по сравнению с базовой версией
- добавлен выбор `polling/webhook`;
- добавлен `healthz` endpoint;
- добавлен Alembic;
- добавлен конфиг Nginx для VPS;
- добавлено более удобное логирование;
- вынесены фабрики `Bot` и `Dispatcher`;
- добавлен middleware для логирования входящих апдейтов.

## Что можно сделать следующим шагом
- повторяющиеся напоминания;
- inline-кнопки удалить/отложить;
- Redis для rate limiting;
- метрики Prometheus;
- отдельный admin-команды `/stats` и `/failed`.


## Новое
- Повторяющиеся напоминания: каждый день / неделю / месяц
- Inline-кнопки в уведомлении: удалить и отложить на 10 минут
- Natural language: `напомни завтра в 9`, `напомни через 30 минут`, `напомни каждый день в 9`
- Админ-команды: `/stats`, `/failed`
- Для админов укажи `ADMIN_IDS` в `.env`, например `ADMIN_IDS=123456789,987654321`
