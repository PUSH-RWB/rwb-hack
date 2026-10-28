# Capibara — SQL-модель команды RWB

Реализованы модель core, витрина уровня заказа, автоматические проверки и десять ответов, рассчитанных исключительно из core. Исходные README.md, docs/, scripts/ и docker-compose.yml организаторов сохранены.

## Запуск в текущем окружении

```bash
bash model/setup.sh
bash model/build.sh
```

Требования: Docker Desktop, Docker Compose >= 2.24.4 и Python 3 со стандартной библиотекой. pandas и psycopg не нужны для SQL-сборки. Для EDA зависимости перечислены отдельно в model/requirements.txt.

model/setup.sh использует исходный compose и model/docker-compose.local.yml: PostgreSQL 16 доступен как postgresql://hack:hack@localhost:5433/marketplace. Порт 5432 и файл организаторов не изменяются. Первичная загрузка выполняется серверным COPY с явными колонками; служебные поля raw заполняются при INSERT. Уже заполненная raw не перезагружается, неожиданный состав или количество строк приводит к остановке. В data/ должны находиться восемь CSV; их скачивает штатный scripts/download_data.sh. Дополнительная геолокация не загружается в raw.

Штатный scripts/setup.sh остаётся доступен для окружения со свободным 5432 и установленным драйвером. Для этой машины используется model/setup.sh, чтобы сохранить исходные файлы и избежать конфликта портов.

## Сборка и результаты

model/build.sh выполняет нумерованные SQL-файлы с ON_ERROR_STOP в одной транзакции REPEATABLE READ, пересоздавая только core и mart. В конце запускаются проверки; FAIL откатывает сборку. Затем экспортируются десять ответов и выполняются 56 проверок контрольных значений. Сверка fingerprints подтверждает неизменность raw payload, включая _source_file; исключён только технический _loaded_at для сравнения разных чистых баз.

- [Архитектура, ключи и связи](model/docs/data_model.md).
- [Короткая записка о решениях](model/docs/decisions.md).
- [Бизнес-правила](model/docs/metrics.md).
- [SQL сборки](model/sql/).
- [65 проверок качества](model/checks/dq_checks.sql).
- [Фактический вывод проверок](model/reports/dq_results.csv).
- [SQL-запросы Q1–Q10](model/answers/).
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

Проверка повторяет сборку в той же базе, затем создаёт отдельную чистую тестовую БД, загружает её из CSV и повторяет сборку. Сравниваются содержимое десяти таблиц core, восьми таблиц raw, 11 CSV ответов и результаты DQ. Созданная проверкой временная БД удаляется, основная raw сохраняется.

Результат: [rebuild_verification.json](model/reports/rebuild_verification.json); детали запуска: [rebuild_verification.log](model/reports/rebuild_verification.log).

## EDA для экспертов

- [HTML с девятью графиками](model/reports/01_eda.html).
- [Выполненный ноутбук](model/notebooks/01_eda.ipynb).
- [Выводы EDA](model/docs/data_quality.md).

EDA и source_check_*.csv — независимые расчёты по исходным CSV. Финальные SQL-ответы находятся в model/answers/results/.

## Репозиторий

origin: https://github.com/PUSH-RWB/rwb-hack.git. Работа выполняется локально; публикация изменений — отдельное действие команды.

## Блок Б и вброс

Q6–Q10 реализованы; Q9 выгружается двумя файлами, итого11 CSV. Правила выборок: model/docs/metrics.md. Старые ответы при миграции сохранены побайтово: model/reports/migration_verification.json.

Версии товара сохраняются в history.product_versions, которая не удаляется при сборке. core.dim_product получает product_key и интервалы, позиция выбирает версию по purchase_at. history.product_publication защищает опубликованные продажи от переотнесения задним числом. Адрес каждого заказа уже хранится в fct_orders.

Для обновлённого снимка с известной датой изменения:

```bash
MODEL_PRODUCT_CHANGE_AT='2026-10-28 18:00:00' bash model/build.sh
```

Без параметра изменение датируется временем наблюдения. Достоверно восстановить неизвестные предыдущие версии из одного CSV нельзя. Непустой неизвестный статус принимается с false-флагами и предупреждением. Эталон model/checks/raw_baseline.csv не перезаписывается автоматически.

Проверки сценариев на временных копиях:

```bash
python3 model/checks/verify_resilience.py
python3 model/checks/verify_rebuild.py
python3 model/checks/verify_failure_guard.py
python3 model/checks/verify_customer_address.py
```

Запускать последовательно. При DATABASE_URL проверяющие скрипты выбирают отдельный URL для каждой тестовой базы. Временные результаты не заменяют основные CSV. Начальная загрузка model/setup.sh по-прежнему предназначена для восьми исходных CSV; сценарии обновлений меняют raw только в тестовых копиях.
