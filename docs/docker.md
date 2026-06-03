# MosaicMed в Docker

Стек: **PostgreSQL** в контейнере `db`, все прикладные процессы (Django, Dash, Dagster, dash_dn) в одном контейнере `mosaicmed`. Redis не используется (Celery в коде не задействован задачами).

## Требования

- Docker Engine 24+
- Docker Compose v2
- Доступ к внутренней сети (10.36.x) из контейнера для Selenium/ISZL

## Быстрый старт

При старте контейнера автоматически выполняются `migrate` и **`collectstatic`** (статика отдаётся через **WhiteNoise** при `DJANGO_ENV=prod`).

```bash
cd /path/to/MosaicMedProject
cp .env.docker.example .env
# Отредактируйте POSTGRES_PASSWORD и SECRET_KEY

mkdir -p backup
# Положите дамп: backup/mosaicmed_backup.sql

docker compose up -d db
# Дождитесь healthy: docker compose ps

# Восстановление БД (plain SQL)
docker compose exec -T db psql -U postgres -d mosaicmed -f /backup/mosaicmed_backup.sql

# При необходимости дельта-миграции (если код новее дампа)
docker compose run --rm mosaicmed python manage.py migrate --noinput

docker compose up -d --build mosaicmed
docker compose logs -f mosaicmed
```

Обновление на сервере: [`scripts/deploy-docker.sh`](../scripts/deploy-docker.sh).

## Порты (хост)

| Сервис | Переменная | По умолчанию |
|--------|------------|--------------|
| Django / admin | `DJANGO_PORT` | 8000 |
| Аналитика Dash | `PORT_DASH` | 5000 |
| Chief Dash | `PORT_DASH_CHIEF` | 5001 |
| Masterd | `MASTERD_PORT` | 5020 |
| Dagster UI | `DAGSTER_PORT` | 3000 |
| Подбор услуг ДН | `PORT_DASH_DN` | 7777 |
| PostgreSQL | `POSTGRES_PUBLISH_PORT` | 5432 |

## Volumes

| Volume | Путь в контейнере | Назначение |
|--------|-------------------|------------|
| `postgres_data` | `/var/lib/postgresql/data` | База `mosaicmed` |
| `mosaic_etl_data` | `/app/mosaic_conductor/etl/data` | Входящие выгрузки ETL |
| `mosaic_dagster_home` | `/app/mosaic_conductor/dagster_home` | Состояние Dagster |
| `mosaic_uploads` | `/app/uploads` | MEDIA_ROOT Django |
| `mosaic_logs` | `/app/logs` | Логи процессов |

**Не удаляйте** `postgres_data` без свежего `pg_dump`.

Каталог `./backup` монтируется в `db` как `/backup:ro` для `psql -f /backup/...`.

### Перенос данных с bare-metal

```bash
# Остановите старые nohup-процессы (scripts/update_MosaicMed.sh делает pkill)

# После первого up db + restore SQL:
docker run --rm -v mosaicmedproject_mosaic_etl_data:/data -v "$(pwd)/mosaic_conductor/etl/data:/src:ro" \
  alpine sh -c "cp -a /src/. /data/"   # при необходимости; имя volume смотрите: docker volume ls

# Аналогично dagster_home, uploads — через docker volume cp или временный контейнер
```

Проще на первом переезде: скопировать папки на хост, затем один раз примонтировать bind в `docker-compose.override.yml` (только для миграции).

## Восстановление дампа

### Plain SQL (как в instruction.md)

```bash
docker compose exec -T db psql -U postgres -d mosaicmed -f /backup/mosaicmed_backup.sql
```

### Custom format

```bash
docker compose cp backup/your.dump db:/tmp/restore.dump
docker compose exec db pg_restore -U postgres -d mosaicmed --clean --if-exists /tmp/restore.dump
```

## Переменные окружения

Шаблон: [`.env.docker.example`](../.env.docker.example).

Django prod читает `Name`, `USER`, `PASSWORD`, `HOST`, `PORT` — в Compose для `mosaicmed` задаётся `HOST=db`.

`RUN_IMPORT_INDICATORS=1` в `.env` — при старте выполнить `import_indicators_structure` (как в `update_MosaicMed.sh`).

## Логи и отладка

```bash
docker compose logs -f mosaicmed
docker compose exec mosaicmed tail -f /app/logs/django.log
docker compose exec mosaicmed tail -f /app/logs/analytical_app.log
docker compose exec mosaicmed sh -c "ps aux | grep python"
```

Перезапуск только приложения:

```bash
docker compose restart mosaicmed
```

## Ограничения v1

- Django и Dash запускаются через dev-серверы (`runserver` / `app.run`), не gunicorn.
- Один контейнер `mosaicmed` — при падении процесса может потребоваться `docker compose restart mosaicmed`.
- **Dagster UI (:3000)** после старта может подниматься 1–2 минуты (загрузка code locations).
- В `.env` символ `$` в паролях экранируйте как `$$` для docker compose (см. `.env.docker.example`).
- Переменная `HOST=db` в compose — это хост PostgreSQL для Django; для `masterd_dashboard` порт задаётся через `PORT=${MASTERD_PORT}` в `start-services.sh`.
- В админке **MainSettings** (`/admin/home/`) проверьте IP Dash/Dagster — укажите IP хоста Docker, не `127.0.0.1`, для доступа с браузера пользователей.
- На одном сервере с MosaicPortal разведите порты (Portal часто 6080, Med — 8000, 5000, …).

## Coexistence с bare-metal

Не запускайте одновременно `update_MosaicMed.sh` и Compose на тех же портах. Для теста Docker используйте другие `DJANGO_PORT` / `PORT_DASH` в `.env`.
