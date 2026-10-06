# Простое frontend + backend приложение

## Что внутри

- `backend` — Python Flask API
- `frontend` — HTML/JavaScript + Nginx
- `docker-compose.yml` — запускает оба сервиса

## Запуск

```bash
docker compose up --build -d
```

Проверить контейнеры:

```bash
docker compose ps
```

Открыть с самого сервера:

```text
http://localhost:8080
```

С другого компьютера в локальной сети:

```text
http://IP_СЕРВЕРА:8080
```

Нажмите кнопку **«Отправить запрос»**. Frontend сделает запрос:

```text
GET /api/hello
```

Nginx перенаправит его во внутренний Docker-сервис:

```text
http://backend:5000/api/hello
```

Backend вернет JSON:

```json
{
  "message": "Привет от Python backend!"
}
```

## Остановка

```bash
docker compose down
```

## Логи

```bash
docker compose logs -f
```
