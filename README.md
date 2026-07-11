# FastAPI File Server

Файловый сервер на FastAPI с JWT-аутентификацией, хранением файлов на диске и метаданными в SQLite.

## Возможности

- Регистрация и вход (JWT)
- Загрузка файлов
- Список файлов с пагинацией
- Скачивание файлов
- Удаление файлов

## Быстрый старт

```bash
# Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать конфигурацию
copy .env.example .env

# Применить миграции
alembic upgrade head

# Запустить сервер
uvicorn app.main:app --reload
```

API документация: http://localhost:8000/docs

## API

### Аутентификация

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Получение JWT токена |

### Файлы (требуют `Authorization: Bearer <token>`)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/files/` | Загрузка файла |
| GET | `/files/` | Список файлов с пагинацией |
| GET | `/files/{file_id}` | Скачивание файла |
| DELETE | `/files/{file_id}` | Удаление файла |

## Примеры запросов

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"user@example.com\", \"password\": \"secret123\"}"

# Логин
curl -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=secret123"

# Загрузка файла
curl -X POST http://localhost:8000/files/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"

# Список с пагинацией
curl "http://localhost:8000/files/?page=1&page_size=10" \
  -H "Authorization: Bearer <token>"

# Скачивание
curl -O -J http://localhost:8000/files/<file_id> \
  -H "Authorization: Bearer <token>"

# Удаление
curl -X DELETE http://localhost:8000/files/<file_id> \
  -H "Authorization: Bearer <token>"
```

## Конфигурация

Переменные окружения в `.env`:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | Строка подключения к БД | `sqlite:///./app.db` |
| `SECRET_KEY` | Секрет для JWT | — |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Срок жизни токена | `30` |
| `UPLOAD_DIR` | Папка для файлов | `./uploads` |
| `MAX_FILE_SIZE_MB` | Макс. размер файла | `50` |

## Структура проекта

```
file-server/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   └── services/
├── uploads/
├── alembic/
├── requirements.txt
└── README.md
```
