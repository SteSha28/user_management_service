# Микросервис управления пользователями (User Management)

Этот микросервис предоставляет основные функции создания, удаления и управления профилями. Он построен с использованием FastAPI и использует PostgreSQL для хранения данных.

## Функции

- Управление профилем пользователя
- RESTful API с использованием FastAPI
- Асинхронные запросы к базе данных с использованием SQLAlchemy

## Технологии

- **FastAPI**: Веб-фреймворк для построения API
- **PostgreSQL**: Реляционная база данных
- **SQLAlchemy**: ORM для работы с базой данных
- **Docker**: Контейнеризация приложения
- **Docker Compose**: Инструмент для работы с многоконтейнерными приложениями

## Требования

- Python 3.12+
- Docker
- Docker Compose

## Настройка

### 1. Клонирование репозитория

```bash
git clone https://github.com/SteSha28/user_management_service.git
cd user_management
python3 -m venv venv
source venv/bin/activate  # Для Windows используйте venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Docker
```bash
docker-compose build
docker-compose up
```
