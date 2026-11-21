
# Практическая №2 - вариант 2 (Streaming vs Batch)

В этой работе я сделала архитектуру для обработки данных с IoT-датчиков температуры. Данные поступают в реальном времени, но иногда могут приходить с задержкой, не по порядку или повторяться.

Основная задача - сделать так, чтобы можно было отслеживать показания датчиков в реальном времени и при этом получать точные отчёты за сутки без потерь и дубликатов.

## Что находится в проекте

- `отчет.md` - отчёт по шаблону 
- `architecture.drawio` - схема архитектуры, которую можно открыть в draw.io.
- `architecture.png` - изображение схемы.
- `docker-compose.yml` - файл для запуска Redpanda, PostgreSQL и Python processor.
- `app/producer.py` - отправляет 12 тестовых сообщений, из которых 3 являются дубликатами. Также сообщения приходят не по порядку.
- `app/consumer.py` - обрабатывает поступающие сообщения, убирает дубликаты и обновляет текущую статистику.
- `app/batch.py` - пересчитывает итоговую статистику за сутки на основе сохранённых событий.
- `tests/test_event_logic.py` - тесты для проверки обработки времени и событий.

## Как запустить

Для запуска нужен Docker с поддержкой Compose v2. Желательно, чтобы было хотя бы 3 ГБ свободной оперативной памяти.

Сначала запускаем основные сервисы:

```bash
docker compose up -d --build redpanda postgres processor
```

Затем создаём топик для сообщений:

```bash
docker compose exec redpanda rpk topic create iot.events --partitions 3 --replicas 1 -X brokers=redpanda:9092
```

Топик достаточно создать один раз. Если он уже существует, повторно создавать его не нужно.

После этого запускаем отправку тестовых событий:

```bash
docker compose --profile demo run --rm producer
```

Запускаем расчёт суточной статистики:

```bash
docker compose --profile manual run --rm batch
```

Проверяем состояние контейнеров:

```bash
docker compose ps
```

## Проверка результатов

Чтобы проверить, сколько уникальных событий сохранилось в базе, выполняем:

```bash
docker compose exec postgres psql -U iot -d iot -c 'SELECT count(*) FROM raw_events;'
```

Посмотреть итоговую статистику за сутки можно командой:

```bash
docker compose exec postgres psql -U iot -d iot -c 'SELECT * FROM batch_daily_reports ORDER BY event_day, sensor_id;'
```

Также можно посмотреть логи обработки сообщений:

```bash
docker compose logs --tail=30 processor
```
