"""Создаёт в Superset подключение к core, датасеты, графики и 10 дашбордов (по одному на вопрос).

Идемпотентно: объекты Capibara пересоздаются, чужие не затрагиваются.
Запуск: python3 dashboard/provision.py [slug ...]   например: provision.py capibara-q3
Зависимостей нет, только стандартная библиотека.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from sbclient import Superset  # noqa: E402

HERE = Path(__file__).parent
ANSWERS = HERE.parent / "model" / "answers"


def load_env():
    env = dict(os.environ)
    f = HERE / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    return env


ENV = load_env()
URL = ENV.get("SUPERSET_URL", "http://127.0.0.1:8088")
DB_NAME = "Capibara · core (PostgreSQL)"
DB_URI = (f"postgresql+psycopg2://{ENV.get('POSTGRES_USER', 'hack')}:{ENV.get('POSTGRES_PASSWORD', 'hack')}"
          f"@{ENV.get('POSTGRES_HOST', 'host.docker.internal')}:{ENV.get('POSTGRES_PORT', '5433')}"
          f"/{ENV.get('POSTGRES_DB', 'marketplace')}")
SCHEME = "wb_wild_berry"
REVENUE_TOTAL = "(SELECT sum(price) FROM core.fct_order_items WHERE is_revenue)"


def answer(name):
    """SQL ответа из model/answers без комментариев и завершающей точки с запятой."""
    text = (ANSWERS / name).read_text(encoding="utf-8")
    text = "\n".join(l for l in text.splitlines() if not l.strip().startswith("--"))
    return text.strip().rstrip(";")


Q1, Q2, Q3, Q4, Q5 = (answer(n) for n in (
    "q01_monthly_revenue.sql", "q02_top_sellers.sql", "q03_average_order_value.sql",
    "q04_repeat_customers.sql", "q05_category_revenue.sql"))

CAT = "CASE WHEN category_name_pt='__unknown__' THEN 'Без категории' ELSE category_name_display END"
Q6_BASE = """WITH t AS (SELECT product_id FROM core.fct_order_items GROUP BY 1 ORDER BY count(DISTINCT price) DESC, product_id LIMIT 1)
SELECT i.purchase_date AS date, i.price, count(*) AS units
FROM core.fct_order_items i JOIN t USING(product_id) GROUP BY 1,2"""
STATUS_RU = ("CASE order_status WHEN 'created' THEN 'создан' WHEN 'approved' THEN 'подтверждён' "
             "WHEN 'invoiced' THEN 'выставлен счёт' WHEN 'processing' THEN 'в обработке' "
             "WHEN 'shipped' THEN 'передан в доставку' WHEN 'delivered' THEN 'вручён' "
             "WHEN 'canceled' THEN 'отменён' WHEN 'unavailable' THEN 'нет в наличии' ELSE order_status END")
STATUS_ORD = ("CASE order_status WHEN 'created' THEN 1 WHEN 'approved' THEN 2 WHEN 'invoiced' THEN 3 "
              "WHEN 'processing' THEN 4 WHEN 'shipped' THEN 5 WHEN 'delivered' THEN 6 WHEN 'canceled' THEN 7 ELSE 8 END")
Q7_BASE = """SELECT o.customer_state_source AS state, count(*) AS orders, round(avg(o.delivery_days),2) AS avg_days,
 round(100.0*count(*) FILTER (WHERE o.is_late)/count(*) FILTER (WHERE o.is_late IS NOT NULL),2) AS late_pct
FROM core.fct_orders o WHERE o.order_status='delivered' AND o.delivery_days IS NOT NULL
GROUP BY 1 HAVING count(*)>=500"""
Q9_STATES = """SELECT o.customer_state_source AS state, count(*) AS payments, round(sum(p.payment_value),2) AS amount,
 round(avg(p.payment_installments),2) AS avg_installments
FROM core.fct_payments p JOIN core.fct_orders o USING(order_id)
WHERE o.purchase_date >= date '2018-01-01' AND o.purchase_date < date '2019-01-01' GROUP BY 1"""
Q10_BASE = """SELECT r.review_score AS score, count(DISTINCT o.order_id) AS orders, round(avg(o.delivery_days),2) AS avg_days,
 round(100.0*count(*) FILTER (WHERE o.is_late)/count(*) FILTER (WHERE o.is_late IS NOT NULL),2) AS late_pct
FROM core.fct_reviews r JOIN core.fct_orders o USING(order_id)
WHERE o.order_status='delivered' AND o.delivery_days IS NOT NULL GROUP BY 1"""

# ---------------------------------------------------------------- датасеты (виртуальные, SQL к core)
DATASETS = {
    "cb_q1_monthly": Q1,
    "cb_q1_kpi": f"SELECT sum(revenue) AS revenue_total, count(*) AS months_cnt, sum(order_count) AS orders_total, max(revenue) AS revenue_peak FROM ({Q1}) t",
    "cb_q2_sellers": f"SELECT initcap(city)||' · '||state AS seller, order_count, units, revenue FROM ({Q2}) t",
    "cb_q2_kpi": f"SELECT max(revenue) AS leader_revenue, sum(revenue) AS top10_revenue, round(100*sum(revenue)/{REVENUE_TOTAL},2)/100 AS top10_share FROM ({Q2}) t",
    "cb_q2_table": f'SELECT seller_id AS "ID продавца", initcap(city) AS "Город", state AS "Штат", order_count AS "Заказы", units AS "Единиц", revenue AS "Выручка" FROM ({Q2}) t',
    "cb_q3": Q3,
    "cb_q4": Q4,
    "cb_q4_share": f"SELECT repeat_customers::numeric/customers AS repeat_share FROM ({Q4}) t",
    "cb_q4_accounts": "SELECT count(DISTINCT source_customer_id) AS accounts FROM core.fct_orders",
    "cb_q5_kpi": f"SELECT count(*) AS categories, max(revenue) AS top_revenue, sum(revenue) AS total_revenue, coalesce(sum(revenue) FILTER (WHERE category_name_pt='__unknown__'),0) AS unknown_revenue FROM ({Q5}) t",
    "cb_q5_top15": f"SELECT {CAT} AS category, revenue FROM ({Q5}) t ORDER BY revenue DESC LIMIT 15",
    "cb_q5_donut": f"""WITH r AS (SELECT {CAT} AS category, revenue, row_number() OVER (ORDER BY revenue DESC) AS rn FROM ({Q5}) t)
SELECT category, revenue::numeric AS revenue FROM r WHERE rn<=6 UNION ALL SELECT 'Остальные', sum(revenue)::numeric FROM r WHERE rn>6""",
    "cb_q5_all": f'SELECT {CAT} AS "Категория", revenue AS "Выручка", revenue_share_percentage AS "Доля %" FROM ({Q5}) t ORDER BY revenue DESC',
    "cb_q6_daily": f"SELECT date, min(price) AS min_price, round(sum(price*units)/sum(units),2) AS avg_price, max(price) AS max_price, sum(units) AS units FROM ({Q6_BASE}) x GROUP BY date",
    "cb_q6_kpi": f"SELECT count(DISTINCT price) AS prices_cnt, sum(units) AS units_total, min(price) AS price_min, max(price) AS price_max FROM ({Q6_BASE}) x",
    "cb_q7_states": Q7_BASE,
    "cb_q7_table": f'SELECT state AS "Штат", orders AS "Заказов", avg_days AS "Дней доставки", late_pct AS "Опоздания %" FROM ({Q7_BASE}) t ORDER BY orders DESC LIMIT 5',
    "cb_q8_statuses": f"SELECT {STATUS_RU} AS status, {STATUS_ORD} AS stage, count(*) AS orders, round(100.0*count(*)/sum(count(*)) OVER (),2) AS share_pct, count(*) FILTER (WHERE NOT has_items) AS without_items FROM core.fct_orders GROUP BY order_status",
    "cb_q8_table": f'SELECT {STATUS_RU} AS "Статус", count(*) AS "Заказов", round(100.0*count(*)/sum(count(*)) OVER (),2) AS "Доля %", count(*) FILTER (WHERE NOT has_items) AS "Без позиций" FROM core.fct_orders GROUP BY order_status ORDER BY {STATUS_ORD}',
    "cb_q9_states": f"SELECT state, payments, amount, round(amount/1000,0) AS amount_k, avg_installments FROM ({Q9_STATES}) t",
    "cb_q9_kpi": """SELECT count(*) AS payments, round(sum(p.payment_value),2) AS amount, round(avg(p.payment_installments),2) AS avg_installments
FROM core.fct_payments p JOIN core.fct_orders o USING(order_id) WHERE o.purchase_date >= date '2018-01-01' AND o.purchase_date < date '2019-01-01'""",
    "cb_q9_table": f'SELECT state AS "Штат", payments AS "Платежей", amount AS "Сумма R$", avg_installments AS "Срок рассрочки" FROM ({Q9_STATES}) t ORDER BY amount DESC LIMIT 5',
    "cb_q9_types": 'SELECT payment_type AS "Способ оплаты", count(*) AS "Платежей", round(avg(payment_installments),2) AS "Срок рассрочки" FROM core.fct_payments GROUP BY 1 ORDER BY 2 DESC',
    "cb_ov_delivery": "SELECT round(count(*) FILTER (WHERE is_late)::numeric / nullif(count(*) FILTER (WHERE is_late IS NOT NULL), 0), 4) AS late_share FROM core.fct_orders WHERE order_status='delivered'",
    "cb_q10": Q10_BASE,
    "cb_q10_table": f'SELECT score AS "Оценка", orders AS "Заказов", avg_days AS "Дней доставки", late_pct AS "Опоздания %" FROM ({Q10_BASE}) t ORDER BY score',
}


# ---------------------------------------------------------------- описание графиков
def metric(expr, label):
    return {"expressionType": "SQL", "sqlExpression": expr, "label": label, "hasCustomLabel": True,
            "optionName": f"metric_{label}"}


def big(ds, expr, label, fmt=",.0f", sub=""):
    return ds, "big_number_total", {
        "metric": metric(expr, label), "adhoc_filters": [], "header_font_size": 0.5, "subheader": sub,
        "subheader_font_size": 0.14, "y_axis_format": fmt, "force_timestamp_formatting": False}


def bar(ds, x, expr, label, fmt=",.0f", horizontal=False, sort=None, show_value=True, grain=None, all_labels=False):
    p = {"x_axis": x, "metrics": [metric(expr, label)], "groupby": [], "adhoc_filters": [], "row_limit": 1000,
         "color_scheme": SCHEME, "show_value": show_value, "orientation": "horizontal" if horizontal else "vertical",
         "y_axis_format": fmt, "show_legend": False, "rich_tooltip": True, "zoomable": False,
         "truncate_metric": True, "show_empty_columns": True}
    if all_labels:
        p["xAxisLabelInterval"] = 0
        p["xAxisLabelRotation"] = 0
    if sort is not None:                      # sort="asc"|"desc": по значению метрики, а не по названию
        p["x_axis_sort"] = label
        p["x_axis_sort_asc"] = sort == "asc"
    if grain:
        p["time_grain_sqla"] = grain
    return ds, "echarts_timeseries_bar", p


def line(ds, x, metrics, fmt=",.2f", area=False, grain=None, legend=False, markers=False):
    p = {"x_axis": x, "metrics": [metric(e, l) for e, l in metrics], "groupby": [], "adhoc_filters": [],
         "row_limit": 10000, "color_scheme": SCHEME, "show_legend": legend, "y_axis_format": fmt,
         "rich_tooltip": True, "zoomable": False, "seriesType": "line", "opacity": 0.35 if area else 0.2,
         "markerEnabled": markers, "markerSize": 6, "truncateYAxis": not area, "y_axis_bounds": [None, None]}
    if grain:
        p["time_grain_sqla"] = grain
    return ds, "echarts_area" if area else "echarts_timeseries_line", p


def table(ds, cols, order, numfmt=None, bars=None):
    cfg = {}
    for c, f in (numfmt or {}).items():
        cfg[c] = {"d3NumberFormat": f, "horizontalAlign": "right"}
    for c in bars or []:
        cfg.setdefault(c, {})["showCellBars"] = True
    return ds, "table", {
        "query_mode": "raw", "all_columns": cols, "groupby": [], "metrics": [], "percent_metrics": [],
        "adhoc_filters": [], "order_by_cols": [json.dumps([order[0], order[1]])], "row_limit": 1000,
        "server_page_length": 10, "page_length": 0, "include_search": False, "show_cell_bars": False,
        "color_pn": False, "allow_rearrange_columns": False, "column_config": cfg}


def pie(ds, cat, expr, label, fmt=",.2f"):
    return ds, "pie", {
        "groupby": [cat], "metric": metric(expr, label), "adhoc_filters": [], "row_limit": 10,
        "sort_by_metric": True, "color_scheme": SCHEME, "show_labels": False, "label_type": "key_percent",
        "labels_outside": False, "show_legend": True, "legendType": "plain", "legendOrientation": "right",
        "donut": True, "innerRadius": 45, "outerRadius": 75, "show_total": True, "number_format": fmt}


def small_pie(spec):
    ds, viz, params = spec
    return ds, viz, dict(params, show_legend=False, show_labels=False, show_total=False, innerRadius=55, outerRadius=85)


def md(text, h=9):
    return ("md", text, h)


# Раскладка: список строк; элемент строки = (ключ графика, ширина из 12, высота в 8px-единицах)
DASHBOARDS = [
    {"slug": "capibara-overview", "title": "Ключевые показатели Capibara", "accent": ["t1"],
     "charts": {
         # по одному элементу от каждого дашборда: число, где есть заглавный показатель, и график, где важна форма
         "t1": ("Обзор · Q1 · Выручка, R$", big("cb_q1_kpi", "MAX(revenue_total)", "revenue_total", ",.2f", "Q1 · доставленные заказы, без доставки")),
         "t2": ("Обзор · Q2 · Лидер-продавец, R$", big("cb_q2_kpi", "MAX(leader_revenue)", "leader_revenue", ",.2f", "Q2 · выручка первого из топ-10")),
         "t3": ("Обзор · Q3 · Средний чек, R$", big("cb_q3", "MAX(average_order_value)", "average_order_value", ",.2f", "Q3 · заказ с доставкой")),
         "t4": ("Обзор · Q4 · Повторные", big("cb_q4_share", "MAX(repeat_share)", "repeat_share", ".2%", "Q4 · вернулись за второй покупкой")),
         "t5": ("Обзор · Q5 · Структура выручки", small_pie(pie("cb_q5_donut", "category", "SUM(revenue)", "revenue"))),
         "t6": ("Обзор · Q6 · Цена товара по дням, R$", line("cb_q6_daily", "date", [("MAX(avg_price)", "avg_price")], ",.2f", grain="P1D")),
         "t7": ("Обзор · Q7 · Опоздания доставки", big("cb_ov_delivery", "MAX(late_share)", "late_share", ".2%", "Q7 · доля доставленных заказов с опозданием")),
         "t8": ("Обзор · Q8 · Доставлено, % заказов", big("cb_q8_statuses", "MAX(CASE WHEN status='вручён' THEN share_pct END)/100", "delivered_share", ".2%", "Q8 · статус «вручён»")),
         "t9": ("Обзор · Q9 · Платежи 2018, R$", big("cb_q9_kpi", "MAX(amount)", "amount", ",.2f", "Q9 · все способы оплаты")),
         "t10": ("Обзор · Q10 · Опоздания по оценкам, %", bar("cb_q10", "score", "MAX(late_pct)", "late_pct", ",.2f"))},
     "layout": [[("t1", 3, 22), ("t2", 3, 22), ("t3", 3, 22), ("t4", 3, 22)],
                [("t5", 4, 24), ("t6", 4, 24), ("t7", 4, 24)],
                [("t8", 4, 24), ("t9", 4, 24), ("t10", 4, 24)],
                [md("**Подробнее:** " + " · ".join(f"[{t}](/superset/dashboard/capibara-q{i}/)" for i, t in enumerate(
                    ["Q1 Выручка по месяцам", "Q2 Продавцы", "Q3 Средний чек", "Q4 Покупатели", "Q5 Категории", "Q6 История цены",
                     "Q7 Доставка по штатам", "Q8 Воронка статусов", "Q9 Оплата", "Q10 Оценки и доставка"], start=1)), h=7)]]},
    {"slug": "capibara-q1", "title": "Q1 · Выручка и заказы по месяцам",
     "charts": {
         "k1": ("Q1 · Выручка за период, R$", big("cb_q1_kpi", "MAX(revenue_total)", "revenue_total", ",.2f", "доставленные заказы")),
         "k2": ("Q1 · Месяцев в отчёте", big("cb_q1_kpi", "MAX(months_cnt)", "months_cnt", ",.0f", "включая ноябрь 2016 без заказов")),
         "k3": ("Q1 · Заказов за период", big("cb_q1_kpi", "MAX(orders_total)", "orders_total", ",.0f", "все статусы")),
         "k4": ("Q1 · Пик месячной выручки, R$", big("cb_q1_kpi", "MAX(revenue_peak)", "revenue_peak", ",.2f", "ноябрь 2017")),
         "c1": ("Q1 · Выручка по месяцам, R$", bar("cb_q1_monthly", "month_key", "MAX(revenue)", "revenue", ",.0f", show_value=False)),
         "c2": ("Q1 · Заказы по месяцам", line("cb_q1_monthly", "month_key", [("MAX(order_count)", "order_count")], ",.0f", area=True))},
     "layout": [[("k1", 3, 28), ("k2", 3, 28), ("k3", 3, 28), ("k4", 3, 28)], [("c1", 12, 44)], [("c2", 12, 34)],
                [md("**Источник:** `core.fct_orders`, календарь `core.dim_date`. **Формулы:** выручка = SUM(item_amount) при `is_revenue` (доставленные заказы, без доставки); "
                    "заказы = COUNT(*) по месяцу оформления, все статусы. Месяц без заказов (2016-11) присутствует, потому что месяцы берутся из календаря, а не из заказов.")]]},
    {"slug": "capibara-q2", "title": "Q2 · Топ-10 продавцов по выручке",
     "charts": {
         "k1": ("Q2 · Лидер, R$", big("cb_q2_kpi", "MAX(leader_revenue)", "leader_revenue", ",.2f", "Guariba · SP")),
         "k2": ("Q2 · Топ-10 суммарно, R$", big("cb_q2_kpi", "MAX(top10_revenue)", "top10_revenue", ",.2f", "10 продавцов")),
         "k3": ("Q2 · Доля топ-10 в выручке", big("cb_q2_kpi", "MAX(top10_share)", "top10_share", ".2%", "концентрация низкая")),
         "c1": ("Q2 · Выручка продавцов, R$", bar("cb_q2_sellers", "seller", "MAX(revenue)", "revenue", ",.0f", horizontal=True, sort="asc")),
         "t1": ("Q2 · Продавцы подробно", table("cb_q2_table", ["ID продавца", "Город", "Штат", "Заказы", "Единиц", "Выручка"], ("Выручка", False),
                                              {"Выручка": ",.2f", "Заказы": ",.0f", "Единиц": ",.0f"}, ["Выручка"]))},
     "layout": [[("k1", 4, 22), ("k2", 4, 22), ("k3", 4, 22)], [("c1", 6, 78), ("t1", 6, 78)],
                [md("**Источник:** `core.fct_order_items`, `core.dim_seller`. **Формула:** выручка продавца = SUM(price) только по его позициям в доставленных заказах; "
                    "заказы = COUNT(DISTINCT order_id). В 1 278 заказах товары разных продавцов, поэтому сумма заказа продавцу не приписывается.")]]},
    {"slug": "capibara-q3", "title": "Q3 · Средний чек заказа",
     "charts": {
         "k1": ("Q3 · Средний чек, R$", big("cb_q3", "MAX(average_order_value)", "average_order_value", ",.2f", "товары и доставка на заказ")),
         "k2": ("Q3 · Строк в заказе", big("cb_q3", "MAX(average_lines_per_order)", "average_lines_per_order", ",.2f", "среднее число позиций")),
         "k3": ("Q3 · Единиц товара в заказе", big("cb_q3", "MAX(average_units_per_order)", "average_units_per_order", ",.2f", "каждая строка — одна единица")),
         "k4": ("Q3 · Доставленных заказов", big("cb_q3", "MAX(order_count)", "order_count", ",.0f", "база расчёта"))},
     "layout": [[("k1", 6, 34), ("k2", 6, 34)], [("k3", 6, 34), ("k4", 6, 34)],
                [md("**Источник:** `core.fct_orders`. **Формула:** AVG(order_amount) по доставленным заказам, где order_amount = товары + доставка. Уровень расчёта — заказ, не позиция: "
                    "по позициям вышло бы 139,97, по цене товара без доставки — 123,75.")]]},
    {"slug": "capibara-q4", "title": "Q4 · Покупатели и повторные покупки", "accent": ["k3"],
     "charts": {
         "k1": ("Q4 · Покупателей", big("cb_q4", "MAX(customers)", "customers", ",.0f", "customer_unique_id — один человек")),
         "k2": ("Q4 · Вернулись за второй покупкой", big("cb_q4", "MAX(repeat_customers)", "repeat_customers", ",.0f", "два и более заказа")),
         "k3": ("Q4 · Доля повторных", big("cb_q4_share", "MAX(repeat_share)", "repeat_share", ".2%", "в наблюдаемом окне, не когортное удержание")),
         "k4": ("Q4 · Аккаунтов заказа (customer_id)", big("cb_q4_accounts", "MAX(accounts)", "accounts", ",.0f", "не покупатели: по ним повторных нет"))},
     "layout": [[("k1", 6, 34), ("k2", 6, 34)], [("k3", 6, 34), ("k4", 6, 34)],
                [md("**Источник:** `core.fct_orders`, `core.dim_customer`. **Формулы:** покупатель = `customer_unique_id`; повторный = человек с двумя и более заказами, все статусы. "
                    "`customer_id` заводится заново на каждый заказ, поэтому по нему повторных покупок не бывает.")]]},
    {"slug": "capibara-q5", "title": "Q5 · Выручка по категориям", "label_colors": {"Остальные": "#CFCFCF"},
     "charts": {
         "k1": ("Q5 · Категорий", big("cb_q5_kpi", "MAX(categories)", "categories", ",.0f", "73 реальные + «без категории»")),
         "k2": ("Q5 · Лидер, R$", big("cb_q5_kpi", "MAX(top_revenue)", "top_revenue", ",.2f", "health_beauty · 9,33 %")),
         "k3": ("Q5 · Без категории, R$", big("cb_q5_kpi", "MAX(unknown_revenue)", "unknown_revenue", ",.2f", "610 товаров сохранены")),
         "k4": ("Q5 · Итого, R$", big("cb_q5_kpi", "MAX(total_revenue)", "total_revenue", ",.2f", "равно выручке за период")),
         "c1": ("Q5 · Топ-15 категорий по выручке, R$", bar("cb_q5_top15", "category", "MAX(revenue)", "revenue", ",.0f", horizontal=True, sort="asc")),
         "c2": ("Q5 · Структура выручки", pie("cb_q5_donut", "category", "SUM(revenue)", "revenue"))},
     "layout": [[("k1", 3, 24), ("k2", 3, 24), ("k3", 3, 24), ("k4", 3, 24)], [("c1", 7, 76), ("c2", 5, 76)],
                [md("**Источник:** `core.fct_order_items`, `core.dim_product`. **Формула:** выручка категории = SUM(price) доставленных позиций по исходному коду категории. "
                    "Пустая категория — явная строка «Без категории»; сумма по 74 категориям равна выручке из Q1.")]]},
    {"slug": "capibara-q6", "title": "Q6 · История цены товара",
     "charts": {
         "k1": ("Q6 · Разных цен у товара", big("cb_q6_kpi", "MAX(prices_cnt)", "prices_cnt", ",.0f", "максимум среди всех товаров")),
         "k2": ("Q6 · Продано единиц", big("cb_q6_kpi", "MAX(units_total)", "units_total", ",.0f", "все статусы заказов")),
         "k3": ("Q6 · Максимальная цена, R$", big("cb_q6_kpi", "MAX(price_max)", "price_max", ",.2f", "")),
         "c1": ("Q6 · Цена товара по дням, R$", line("cb_q6_daily", "date", [("MIN(min_price)", "min_price"), ("MAX(avg_price)", "avg_price"), ("MAX(max_price)", "max_price")], ",.2f", grain="P1D", legend=True, markers=True)),
         "c2": ("Q6 · Продано единиц по дням", bar("cb_q6_daily", "date", "SUM(units)", "units", ",.0f", grain="P1D", show_value=False))},
     "layout": [[("k1", 4, 24), ("k2", 4, 24), ("k3", 4, 24)], [("c1", 12, 44)], [("c2", 12, 32)],
                [md("**Источник:** `core.fct_order_items`. Товар с наибольшим числом разных цен. Допущение: учитываются все статусы заказов; "
                    "в один день бывает несколько цен, поэтому показаны минимум, средневзвешенная и максимум за день.")]]},
    {"slug": "capibara-q7", "title": "Q7 · Доставка по штатам покупателя",
     "charts": {
         "c1": ("Q7 · Среднее время доставки, дней", bar("cb_q7_states", "state", "MAX(avg_days)", "avg_days", ",.2f", sort="desc")),
         "c2": ("Q7 · Доля опозданий, %", bar("cb_q7_states", "state", "MAX(late_pct)", "late_pct", ",.2f", sort="desc")),
         "t1": ("Q7 · Топ-5 штатов по числу заказов", table("cb_q7_table", ["Штат", "Заказов", "Дней доставки", "Опоздания %"], ("Заказов", False),
                                           {"Заказов": ",.0f", "Дней доставки": ",.2f", "Опоздания %": ",.2f"}, ["Дней доставки", "Опоздания %"]))},
     "layout": [[("c1", 6, 50), ("c2", 6, 50)], [("t1", 12, 50)],
                [md("**Источник:** `core.fct_orders`. Только штаты, где не меньше 500 доставленных заказов с известными датами. **Формулы:** срок = дни от оформления до вручения; "
                    "опоздание = вручение позже обещанной даты, доля считается среди заказов с обеими датами.")]]},
    {"slug": "capibara-q8", "title": "Q8 · Воронка статусов заказов",
     "charts": {
         "c1": ("Q8 · Заказы по статусам", bar("cb_q8_statuses", "status", "MAX(orders)", "orders", ",.0f", sort="desc", all_labels=True)),
         "c2": ("Q8 · Заказы без позиций по статусам", bar("cb_q8_statuses", "status", "MAX(without_items)", "without_items", ",.0f", sort="desc", all_labels=True)),
         "t1": ("Q8 · Статусы подробно", table("cb_q8_table", ["Статус", "Заказов", "Доля %", "Без позиций"], ("Заказов", False),
                                              {"Заказов": ",.0f", "Доля %": ",.2f", "Без позиций": ",.0f"}, ["Доля %"]))},
     "layout": [[("c1", 6, 32), ("c2", 6, 32)], [("t1", 12, 68)],
                [md("**Источник:** `core.fct_orders`. Заказы без позиций остаются в модели: иначе число заказов занижается. "
                    "Так, 603 из 609 заказов в статусе «нет в наличии» не содержат ни одного товара.")]]},
    {"slug": "capibara-q9", "title": "Q9 · Оплата и рассрочка",
     "charts": {
         "k1": ("Q9 · Платежей в 2018", big("cb_q9_kpi", "MAX(payments)", "payments", ",.0f", "по заказам 2018 года")),
         "k2": ("Q9 · Сумма платежей, R$", big("cb_q9_kpi", "MAX(amount)", "amount", ",.2f", "все способы оплаты")),
         "k3": ("Q9 · Средний срок рассрочки", big("cb_q9_kpi", "MAX(avg_installments)", "avg_installments", ",.2f", "частей на платёж")),
         "c1": ("Q9 · Сумма платежей по штатам, 2018, тыс. R$", bar("cb_q9_states", "state", "MAX(amount_k)", "amount_k", ",.0f", sort="desc")),
         "t1": ("Q9 · Топ-5 штатов, 2018", table("cb_q9_table", ["Штат", "Платежей", "Сумма R$", "Срок рассрочки"], ("Сумма R$", False),
                                         {"Платежей": ",.0f", "Сумма R$": ",.2f", "Срок рассрочки": ",.2f"}, ["Сумма R$"])),
         "t2": ("Q9 · Способы оплаты, все годы", table("cb_q9_types", ["Способ оплаты", "Платежей", "Срок рассрочки"], ("Платежей", False),
                                                       {"Платежей": ",.0f", "Срок рассрочки": ",.2f"}, ["Платежей"]))},
     "layout": [[("k1", 4, 19), ("k2", 4, 19), ("k3", 4, 19)], [("c1", 12, 28)], [("t1", 7, 51), ("t2", 5, 51)],
                [md("**Источник:** `core.fct_payments`, `core.fct_orders` · платёж относится к штату покупателя заказа, год — по дате заказа.", h=7)]]},
    {"slug": "capibara-q10", "title": "Q10 · Оценка покупателя и срок доставки",
     "charts": {
         "c1": ("Q10 · Средний срок доставки по оценке, дни", bar("cb_q10", "score", "MAX(avg_days)", "avg_days", ",.2f")),
         "c2": ("Q10 · Доля опозданий по оценке, %", bar("cb_q10", "score", "MAX(late_pct)", "late_pct", ",.2f")),
         "t1": ("Q10 · Оценка и исполнение заказа", table("cb_q10_table", ["Оценка", "Заказов", "Дней доставки", "Опоздания %"], ("Оценка", True),
                                                          {"Заказов": ",.0f", "Дней доставки": ",.2f", "Опоздания %": ",.2f"}, ["Опоздания %"]))},
     "layout": [[("c1", 6, 50), ("c2", 6, 50)], [("t1", 12, 50)],
                [md("**Источник:** `core.fct_reviews`, `core.fct_orders`. Доставленные заказы с известными датами. Это наблюдение, а не причинность; "
                    "заказ с несколькими отзывами попадает в несколько групп оценок.")]]},
]

# Крупные плитки Q3 и Q4 — одни числа, шрифт больше, чем у показателей в строках
BIG_ONLY = {"capibara-q3", "capibara-q4"}
OVERVIEW_SLUG = "capibara-overview"

CSS = """
.dashboard { background: #F6EFF9 !important; }
.dashboard-component-chart-holder, .dashboard-component-markdown .markdown-viewer { border-radius: 14px; box-shadow: 0 1px 4px rgba(72, 17, 115, 0.14); }
.header-line { color: #481173 !important; font-weight: 700 !important; }
.subheader-line { color: #7B6A8A !important; }
"""
for _d in DASHBOARDS:
    if _d["slug"] == OVERVIEW_SLUG:
        for _name, (_ds, _viz, _params) in _d["charts"].values():
            if _viz == "big_number_total":
                _params.update(header_font_size=0.42, subheader_font_size=0.13)
    if _d["slug"] in BIG_ONLY:
        for _name, (_ds, _viz, _params) in _d["charts"].values():
            _params.update(header_font_size=0.5, subheader_font_size=0.16)

ACCENT = ".dashboard-chart-id-%d .header-line { color: #CB11AB !important; }\n"
CSS += ".dashboard-markdown, .dashboard-markdown .markdown-viewer { font-size: 12px; line-height: 1.35; }\n"

# Дашборд занимает ровно один экран. Superset рисует график по высоте из раскладки (в 8-пиксельных единицах),
# а не по размеру контейнера, поэтому высоты строк считаем заранее под высоту окна браузера.
TARGET_H = int(ENV.get("DASHBOARD_VIEWPORT_H", "800"))    # высота окна, под которую считаем (ноутбук ~800)
TOP_PX, BOTTOM_PX, GAP_PX, UNIT = 142, 26, 16, 8          # навигация + шапка; запас снизу; зазор строк; единица Superset


def fit_heights(d):
    rows = d["layout"]
    chart_rows = [r for r in rows if r[0][0] != "md"]
    md_px = sum(r[0][2] * UNIT for r in rows if r[0][0] == "md")
    remain = TARGET_H - TOP_PX - BOTTOM_PX - GAP_PX * (len(rows) - 1) - md_px
    total = sum(max(it[2] for it in r) for r in chart_rows)
    heights = {}
    for r in chart_rows:
        units = max(10, int(remain * max(it[2] for it in r) / total // UNIT))
        for it in r:
            heights[it[0]] = units
    return heights


# ---------------------------------------------------------------- сборка
def build_position(charts_by_key, rows, ids, heights):
    pos = {"DASHBOARD_VERSION_KEY": "v2",
           "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
           "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]}}
    for i, row in enumerate(rows):
        rid = f"ROW-{i + 1}"
        pos["GRID_ID"]["children"].append(rid)
        pos[rid] = {"type": "ROW", "id": rid, "children": [], "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        for j, item in enumerate(row):
            if item[0] == "md":
                cid = f"MARKDOWN-{i + 1}-{j}"
                pos[cid] = {"type": "MARKDOWN", "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", rid],
                            "meta": {"width": 12, "height": item[2], "code": item[1]}}
            else:
                key, w, h = item
                cid = f"CHART-{key}"
                pos[cid] = {"type": "CHART", "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", rid],
                            "meta": {"width": w, "height": heights.get(key, h), "chartId": ids[key], "sliceName": charts_by_key[key][0]}}
            pos[rid]["children"].append(cid)
    return pos


def main():
    only = set(sys.argv[1:])
    for _ in range(60):
        try:
            urllib.request.urlopen(URL + "/health", timeout=5)
            break
        except Exception:
            time.sleep(3)
    s = Superset(URL, ENV.get("SUPERSET_ADMIN_USER", "admin"), ENV.get("SUPERSET_ADMIN_PASSWORD", "admin"))

    # подключение к базе
    found = s.find("database", "database_name", DB_NAME)
    if found:
        db_id = found[0]["id"]
        s.call("PUT", f"/api/v1/database/{db_id}", {"sqlalchemy_uri": DB_URI})
    else:
        db_id = s.call("POST", "/api/v1/database/", {"database_name": DB_NAME, "sqlalchemy_uri": DB_URI,
                                                      "expose_in_sqllab": True, "allow_dml": False})["id"]
    print(f"база: id={db_id}")

    wanted = [d for d in DASHBOARDS if not only or d["slug"] in only]
    # очистка прежних объектов Capibara: дашборды, затем графики, затем датасеты
    for d in wanted:
        for old in s.find("dashboard", "dashboard_title", d["title"]):
            s.call("DELETE", f"/api/v1/dashboard/{old['id']}")
    for d in wanted:
        for _, (name, _) in d["charts"].items():
            for old in s.find("chart", "slice_name", name):
                s.call("DELETE", f"/api/v1/chart/{old['id']}")
        if d["slug"] == OVERVIEW_SLUG:          # плитки прежних версий общего дашборда
            for old in s.find("chart", "slice_name", "Обзор · ", "sw"):
                s.call("DELETE", f"/api/v1/chart/{old['id']}")
    need = {chart[1][0] for d in wanted for chart in d["charts"].values()}
    ds_ids = {}
    for name in sorted(need):
        old = s.find("dataset", "table_name", name)
        if old:
            ds_ids[name] = old[0]["id"]
            s.call("PUT", f"/api/v1/dataset/{ds_ids[name]}", {"sql": DATASETS[name]})
        else:
            ds_ids[name] = s.call("POST", "/api/v1/dataset/", {"database": db_id, "schema": "core", "table_name": name,
                                                              "sql": DATASETS[name]})["id"]
    print(f"датасетов: {len(ds_ids)}")

    for d in wanted:
        dash_id = s.call("POST", "/api/v1/dashboard/", {
            "dashboard_title": d["title"], "slug": d["slug"], "published": True, "css": CSS,
            "json_metadata": json.dumps({"color_scheme": SCHEME, "refresh_frequency": 0, "expanded_slices": {},
                                         "label_colors": d.get("label_colors", {}), "timed_refresh_immune_slices": [],
                                         "cross_filters_enabled": True, "default_filters": "{}"})})["id"]
        ids = {}
        for key, (name, (ds, viz, params)) in d["charts"].items():
            params = dict(params, datasource=f"{ds_ids[ds]}__table", viz_type=viz)
            ids[key] = s.call("POST", "/api/v1/chart/", {
                "slice_name": name, "viz_type": viz, "datasource_id": ds_ids[ds], "datasource_type": "table",
                "params": json.dumps(params, ensure_ascii=False), "dashboards": [dash_id]})["id"]
        pos = build_position(d["charts"], d["layout"], ids, fit_heights(d))
        css = CSS + "".join(ACCENT % ids[k] for k in d.get("accent", ["k1"]) if k in ids)
        s.call("PUT", f"/api/v1/dashboard/{dash_id}", {"position_json": json.dumps(pos, ensure_ascii=False), "css": css})
        print(f"дашборд {d['slug']}: id={dash_id}, графиков {len(ids)}  ->  {URL}/superset/dashboard/{d['slug']}/")


if __name__ == "__main__":
    main()
