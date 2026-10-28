# Проверки

- dq_checks.sql: 60 SQL-проверок, таблица PASS/WARN/FAIL. FAIL вызывает исключение и откатывает сборку. SOURCE WARN отражает сохранённые аномалии.
- verify_answers.py: 12 проверок реального вывода пяти SQL-запросов.
- raw_fingerprint.sql: хеши raw payload, исключён только _loaded_at для сравнения разных загрузок.
- core_fingerprint.sql: хеши десяти таблиц core.
- verify_rebuild.py: повторная сборка и отдельная чистая БД, сравнение таблиц, ответов и DQ.

Фактические результаты находятся в model/reports/. Запросы ответов не читают raw.
