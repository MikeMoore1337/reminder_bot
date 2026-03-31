# 🤖 Reminder Bot

Современный Telegram-бот для напоминаний с поддержкой естественного языка, повторяющихся задач и масштабируемой архитектуры.

---

## 🚀 Возможности

### 🕒 Напоминания
- по дате и времени  
- через промежуток времени  
- повторяющиеся  

### 📌 Примеры
напомни завтра в 9 созвон  
напомни через 30 минут выключить духовку  
напомни каждый день в 10 выпить витамины  
напомни каждые 2 часа пить воду  
напомни каждые 10 минут проверить сервер  
напомни 31.03.2026 18:30 купить молоко  

---

### 🔁 Повторения

Поддерживается:

- каждые X минут (минимум 5)
- каждый час / каждые X часов
- каждый день / каждые X дней
- каждую неделю
- каждый месяц

Примеры:
каждые 5 минут  
каждый час  
каждые 2 часа  
каждый день  
каждую неделю  
каждый месяц  

---

### 🌍 Часовые пояса
- индивидуально для каждого пользователя  
- формат IANA (Europe/Moscow, Europe/Helsinki и т.д.)  
- хранение времени в UTC  

---

## 🧠 UX / UI

### `/start`
- короткое описание
- примеры использования
- текущий часовой пояс
- кнопки управления

### Reply-клавиатура
- ➕ Создать напоминание  
- 📋 Мои напоминания  
- 🌍 Часовой пояс  
- ❓ Помощь  

### `/help`
подробная инструкция

---

## ⚙️ Команды

Публичные:
- /start  
- /help  
- /timezone  
- /mytimezone  
- /remind  
- /list  
- /cancel  

Админ:
- /stats  
- /failed  

---

## 🏗 Архитектура

Telegram → Bot (aiogram) → PostgreSQL → Worker

Почему так:
- нет потери задач при рестарте
- масштабируемость
- устойчивость

---

## 🗂 Структура проекта

app/
 ├── handlers/
 ├── services/
 ├── db/
 ├── workers/
 ├── keyboards/
 ├── middlewares/
 ├── main.py
 └── bot_factory.py

---

## ⚙️ Установка

### 1. Клонирование
git clone <repo>
cd reminder_bot

---

### 2. Настройка .env

BOT_TOKEN=your_token  
BOT_MODE=polling  
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/reminder_bot  
LOG_LEVEL=INFO  
DEFAULT_TIMEZONE=Europe/Helsinki  
ADMIN_IDS=123456789  

---

### 3. Запуск

docker compose build  
docker compose --profile tools run --rm migrate  
docker compose up -d db bot worker  

---

### 4. Логи

docker compose logs -f bot  
docker compose logs -f worker  

---

## 🔁 Управление

Перезапуск:
docker compose restart  

Остановка:
docker compose down  

Обновление:
git pull  
docker compose build  
docker compose up -d  

---

## ⚠️ Важно

- все даты хранятся в UTC  
- пользователю показывается локальное время  
- повторения обновляются без создания новых записей  
- worker обрабатывает задачи через БД  

---

## 📈 Возможности для развития

- inline-кнопки управления  
- cron-подобные расписания  
- rate limiting  
- уведомления о сбоях  
- webhook + HTTPS  

---

## 🧠 Концепция

- БД = источник истины  
- worker = обработка  
- bot = интерфейс  

Это даёт:
- стабильность  
- масштабируемость  
- предсказуемость  

---

## 👨‍💻 Автор

Python QA Automation Engineer
