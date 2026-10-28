"""Конфигурация Superset для Capibara: тема «дикая ягода» Wildberries, русский язык и числа."""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
APP_NAME = "Capibara · Control Tower"

# Язык интерфейса и формат чисел: 13 221 498,11 вместо 13,221,498.11
BABEL_DEFAULT_LOCALE = "ru"
LANGUAGES = {"ru": {"flag": "ru", "name": "Русский"}, "en": {"flag": "us", "name": "English"}}
D3_FORMAT = {"decimal": ",", "thousands": " ", "grouping": [3], "currency": ["", " R$"]}

# Палитра. Основной цвет — «дикая ягода» (приближение к фирменному цвету Wildberries).
BERRY = "#CB11AB"      # дикая ягода
PLUM = "#481173"       # глубокий фиолетовый
VIOLET = "#A73AFD"
PINK = "#F58AD9"
LILAC = "#E7C2F0"
NIGHT = "#1E0733"

THEME_DEFAULT = {
    "token": {
        "brandAppName": APP_NAME,
        "brandLogoAlt": "Capibara",
        "brandLogoUrl": "/static/assets/images/superset-logo-horiz.png",
        "brandLogoMargin": "18px 0",
        "brandLogoHref": "/",
        "brandLogoHeight": "24px",
        "colorPrimary": BERRY,
        "colorLink": BERRY,
        "colorError": "#E04355",
        "colorWarning": "#FCC700",
        "colorSuccess": "#5AC189",
        "colorInfo": VIOLET,
        "fontUrls": [],
        "fontFamily": "Inter, Helvetica, Arial, sans-serif",
        "fontFamilyCode": "'IBM Plex Mono', 'Courier New', monospace",
        "borderRadius": 8,
        "fontWeightStrong": "600",
    },
    "algorithm": "default",
}
THEME_DARK = None  # без тёмной темы: дашборды согласованы под светлую

EXTRA_CATEGORICAL_COLOR_SCHEMES = [{
    "id": "wb_wild_berry",
    "label": "Wildberries · Дикая ягода",
    "description": "Основная палитра дашбордов Capibara",
    "isDefault": True,
    "colors": [BERRY, PLUM, VIOLET, PINK, "#6B2FA0", LILAC, NIGHT],
}]
EXTRA_SEQUENTIAL_COLOR_SCHEMES = [{
    "id": "wb_wild_berry_seq",
    "label": "Wildberries · Дикая ягода (градиент)",
    "isDiverging": False,
    "colors": ["#F6E3F2", LILAC, PINK, BERRY, PLUM],
}]
