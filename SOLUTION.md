# Capibara — решение команды RWB

Материалы организаторов сохранены в README.md, docs/, scripts/ и docker-compose.yml. Наше решение находится в model/.

Текущий результат: выполненное исследование исходных данных вокруг пяти вопросов хакатона, проверка контрольных значений, графики и выводы для будущей модели core. SQL-модель и окончательные ответы из core пока не реализованы.

## Что открыть экспертам

- [HTML-отчёт с графиками, без кода](model/reports/01_eda.html) — можно открыть в браузере без Jupyter.
- [Выполненный EDA-ноутбук](model/notebooks/01_eda.ipynb) — полный воспроизводимый расчёт.
- [Проблемы данных и правила обработки](model/docs/data_quality.md).
- [Определения метрик](model/docs/metrics.md).
- [Графики для презентации](model/reports/figures/).
- [Результат выполнения](model/reports/execution_summary.json).

## Структура нашего решения

- model/notebooks/ — исследование данных.
- model/reports/ — вычисленные результаты и графики; source_check_*.csv относятся к исходникам.
- model/docs/ — бизнес-правила, находки, журнал работы с ИИ.
- model/sql/ — место для реализации core после согласования модели.
- model/checks/ — место для SQL-проверок.
- model/answers/ — место для финальных запросов и их вывода из core.
- model/presentation/ — рекомендации по использованию готовых материалов.

## Воспроизведение EDA

Из корня репозитория, Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r model/requirements.txt
python model/run_eda.py
```

Если зависимости уже установлены, достаточно `python3 model/run_eda.py`.

Восемь оригинальных CSV находятся в data/ и исключены из Git. Для нового checkout их можно получить штатным `bash scripts/download_data.sh`. Контрольные суммы исследованной версии находятся в data/source_manifest.json. При изменении исходников ноутбук остановится на сверке SHA-256: новую версию нужно исследовать и зафиксировать явно.

Дополнительная геолокация находится отдельно в data/extra/. Она не участвует в ответах на пять вопросов, поскольку не входит в исходные восемь таблиц raw хакатона.

## Git

- origin — https://github.com/PUSH-RWB/rwb-hack.git
- upstream — https://github.com/daniilivanovp-droid/hackathon-students.git

Работа ведётся локально. Коммиты и push в рамках подготовки этого исследования не выполнялись.
