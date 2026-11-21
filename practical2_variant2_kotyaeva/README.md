# Практическая №2 — вариант 2 (Streaming vs Batch)

Учебная Lambda-подобная архитектура на примере IoT-датчиков температуры.

## Что внутри

- `отчет.md` — отчёт по шаблону преподавателя.
- `architecture.drawio` — редактируемая схема draw.io.
- `architecture.png` — изображение той же схемы для отчёта.
- `docker-compose.yml` — сервисы Redpanda, PostgreSQL и Python processor.
- `app/producer.py` — 12 сообщений, среди которых 3 дубликата и нарушен порядок.
- `app/consumer.py` — атомарная идемпотентная запись и оперативные агрегаты.
- `app/batch.py` — полный пересчёт суточных итогов из `raw_events`.
- `tests/test_event_logic.py` — тесты разбора времени и демонстрационных событий.

## Запуск

Требования: Docker с Compose v2, желательно 3+ ГБ свободной памяти.

```bash
docker compose up -d --build redpanda postgres processor
docker compose exec redpanda rpk topic create iot.events --partitions 3 --replicas 1 -X brokers=redpanda:9092
docker compose --profile demo run --rm producer
docker compose --profile manual run --rm batch
docker compose ps
```

Команда создания топика нужна только при первом запуске; если он уже существует, повторять её не требуется.

Проверка:

```bash
docker compose exec postgres psql -U iot -d iot -c 'SELECT count(*) FROM raw_events;'
docker compose exec postgres psql -U iot -d iot -c 'SELECT * FROM batch_daily_reports ORDER BY event_day, sensor_id;'
docker compose logs --tail=30 processor
```

При первом тесте ожидается 9 уникальных событий после 12 публикаций. Если повторно запустить producer **в тот же UTC-день**, количество уникальных событий не изменится. При новом дне генерируется новая дневная выборка.

**Ограничение:** авторское окружение без Docker; фактический запуск контейнеров не проверен. `docker ps` нужно выполнить локально и перенести вывод в отчёт. Пароли в Compose — только демонстрационные, для реальной системы их следует вынести в секреты.
