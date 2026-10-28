# Capibara — SQL-модель команды RWB

Реализованы модель core, витрина уровня заказа, автоматические проверки и пять ответов, рассчитанных исключительно из core. Исходные README.md, docs/, scripts/ и docker-compose.yml организаторов сохранены.

## Запуск в текущем окружении

```bash
bash model/setup.sh
bash model/build.sh
```

Требования: Docker Desktop, Docker Compose >= 2.24.4 и Python 3 со стандартной библиотекой. pandas и psycopg не нужны для SQL-сборки. Для EDA зависимости перечислены отдельно в model/requirements.txt.

model/setup.sh использует исходный compose и model/docker-compose.local.yml: PostgreSQL 16 доступен как postgresql://hack:hack@localhost:5433/marketplace. Порт 5432 и файл организаторов не изменяются. Первичная загрузка выполняется серверным COPY с явными колонками; служебные поля raw заполняются при INSERT. Уже заполненная raw не перезагружается, неожиданный состав или количество строк приводит к остановке. В data/ должны находиться восемь CSV; их скачивает штатный scripts/download_data.sh. Дополнительная геолокация не загружается в raw.

Штатный scripts/setup.sh остаётся доступен для окружения со свободным 5432 и установленным драйвером. Для этой машины используется model/setup.sh, чтобы сохранить исходные файлы и избежать конфликта портов.

## Сборка и результаты

model/build.sh выполняет нумерованные SQL-файлы с ON_ERROR_STOP в одной транзакции REPEATABLE READ, пересоздавая только core и mart. В конце запускаются проверки; FAIL откатывает сборку. Затем экспортируются пять ответов и выполняются 12 независимых проверок контрольных значений. Сверка fingerprints подтверждает неизменность raw payload, включая _source_file; исключён только технический _loaded_at для сравнения разных чистых баз.

- [Архитектура, ключи и связи](model/docs/data_model.md).
- [Короткая записка о решениях](model/docs/decisions.md).
- [Бизнес-правила](model/docs/metrics.md).
- [SQL сборки](model/sql/).
- [60 проверок качества](model/checks/dq_checks.sql).
- [Фактический вывод проверок](model/reports/dq_results.csv).
- [Пять SQL-запросов](model/answers/).
- [Полный вывод запросов](model/answers/results/).
- [Численные ответы и пояснения](model/reports/core_results.md).

Отдельный запрос можно выполнить без пересборки:

```bash
bash model/psql.sh --csv -f - < model/answers/q01_monthly_revenue.sql
```

По умолчанию используется контейнер hack_postgres, пользователь hack, база marketplace. PG_CONTAINER, PGUSER и PGDATABASE позволяют выбрать другую конфигурацию контейнера. DATABASE_URL переключает model/psql.sh на локальный psql; серверный COPY требует доступного серверу каталога /data.

## Проверка воспроизводимости

```bash
python3 model/checks/verify_rebuild.py
```

Проверка повторяет сборку в той же базе, затем создаёт отдельную чистую тестовую БД, загружает её из CSV и повторяет сборку. Сравниваются содержимое десяти таблиц core, восьми таблиц raw, пять CSV ответов и результаты DQ. Созданная проверкой временная БД удаляется, основная raw сохраняется.

Результат: [rebuild_verification.json](model/reports/rebuild_verification.json); детали запуска: [rebuild_verification.log](model/reports/rebuild_verification.log).

## EDA для экспертов

- [HTML с девятью графиками](model/reports/01_eda.html).
- [Выполненный ноутбук](model/notebooks/01_eda.ipynb).
- [Выводы EDA](model/docs/data_quality.md).

EDA и source_check_*.csv — независимые расчёты по исходным CSV. Финальные SQL-ответы находятся в model/answers/results/.

## Репозиторий

origin: https://github.com/PUSH-RWB/rwb-hack.git. Работа выполняется локально; публикация изменений — отдельное действие команды.
