"""
Платформа "Моя Вінниця" — інформаційний портал про місто Вінниця
з чат-ботом-гідом, маршрутизатором, обраним, відгуками, live-погодою
та Експортом/Імпортом даних на Streamlit.

Запуск:
    pip install -r requirements.txt
    streamlit run vinnytsia_app.py
"""

import streamlit as st
import re
import json
import csv
import io
import os
from datetime import date, datetime, timedelta

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

import difflib
try:
    from rapidfuzz import fuzz as _rf_fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# =========================================================
#                       НАЛАШТУВАННЯ СТОРІНКИ
# =========================================================
st.set_page_config(
    page_title="Моя Вінниця",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

VINNYTSIA_LAT = 49.2331
VINNYTSIA_LON = 28.4682
APP_VERSION = "1.3"

# Емодзі-іконки для категорій, типів і навігації — суто візуальне покращення,
# кольорова гама та стиль платформи залишаються незмінними.
PAGE_ICONS = {
    "Головна": "🏠",
    "Пам'ятки": "🗺️",
    "Події": "🎉",
    "Ресторани": "🍽️",
    "Маршрут": "🧭",
    "Мої плани": "📔",
    "Транспорт онлайн": "🚌",
    "Обране": "❤️",
    "Чат-бот": "🤖",
    "Про місто": "ℹ️",
    "Зворотний зв'язок": "📝",
    "Експорт/Імпорт": "💾",
}

CATEGORY_ICONS = {
    "Розваги": "🎡",
    "Музей": "🏛️",
    "Історія": "📜",
    "Архітектура": "🏗️",
    "Церква": "⛪",
    "Парк": "🌳",
    "Центр": "🚶",
    "Релігія": "🕍",
    "Пам'ятник": "🗿",
}

RESTAURANT_ICONS = {
    "Українська кухня": "🥟",
    "Українська / пиво": "🍺",
    "Італійська": "🍕",
    "Японська": "🍣",
    "Кав'ярня": "☕",
    "Стейки": "🥩",
    "Вегетаріанська/веганська": "🥗",
}

EVENT_ICONS = {
    "Музика": "🎷",
    "Їжа": "🍔",
    "Культура": "🎭",
    "Сім'я": "👨‍👩‍👧‍👦",
}

STAT_ICONS = {
    "Населення": "👥",
    "Рік заснування": "🏛️",
    "Площа": "📐",
    "Область": "🗺️",
    "Річка": "🌊",
}

# =========================================================
#                       ДАНІ ПРО МІСТО
# =========================================================

CITY_STATS = {
    "Населення": "≈ 370 000",
    "Рік заснування": "1363",
    "Площа": "≈ 113 км²",
    "Область": "Вінницька",
    "Річка": "Південний Буг",
}

FACTS = [
    "Вінниця — батьківщина найбільшого в Європі плавучого фонтану Roshen.",
    "У Вінниці працював і похований видатний хірург Микола Пирогов.",
    "Вінницькі мури — залишки укріплень колишнього єзуїтського монастиря XVII ст.",
    "Місто здобуло звання «Найкраще місто для життя в Україні» за кількома рейтингами.",
    "Вінницька Водонапірна вежа побудована у 1912 році і досі є символом міста.",
    "У Вінниці працює один з найстаріших в Україні працюючих аптек-музеїв.",
    "Місто розташоване на обох берегах Південного Бугу, з'єднаних кількома мостами.",
]

# Кожна пам'ятка: категорія, опис, адреса, теги, час відвідування (хв),
# графік роботи, орієнтовна вартість входу, базовий рейтинг
LANDMARKS = [
    {
        "name": "Фонтан Roshen",
        "category": "Розваги",
        "desc": "Найбільший плавучий світломузичний фонтан у Європі, розташований на річці Південний Буг. "
                "Шоу відбувається у теплу пору року у вечірній час, поєднуючи воду, світло та музику.",
        "address": "Набережна, біля Кемпа",
        "tags": ["фонтан", "roshen", "рошен", "шоу", "музика", "набережна"],
        "duration": 45,
        "hours": "Травень–Жовтень, шоу ~21:00 та ~22:00",
        "price": "Безкоштовно",
        "base_rating": 4.9,
        "img": "https://picsum.photos/seed/vinnytsialandmark1/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark1a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark1b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark1c/700/450",
        ],
    },
    {
        "name": "Музей-садиба М.І. Пирогова «Вишня»",
        "category": "Музей",
        "desc": "Меморіальний комплекс, де жив і працював видатний хірург Микола Пирогов. "
                "У церкві-некрополі зберігається забальзамоване тіло вченого.",
        "address": "вул. Пирогова, 155",
        "tags": ["пирогов", "музей", "садиба", "вишня", "хірург"],
        "duration": 60,
        "hours": "Вт–Нд, 09:00–17:00",
        "price": "60 грн",
        "base_rating": 4.8,
        "img": "https://picsum.photos/seed/vinnytsialandmark2/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark2a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark2b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark2c/700/450",
        ],
    },
    {
        "name": "Вінницькі мури (Мури)",
        "category": "Історія",
        "desc": "Залишки укріплень єзуїтського монастиря XVII століття, одна з найстаріших пам'яток міста, "
                "розташована в історичному центрі.",
        "address": "Старе місто, центр",
        "tags": ["мури", "фортеця", "історія", "центр", "єзуїти"],
        "duration": 30,
        "hours": "Цілодобово (зовнішній огляд)",
        "price": "Безкоштовно",
        "base_rating": 4.5,
        "img": "https://picsum.photos/seed/vinnytsialandmark3/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark3a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark3b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark3c/700/450",
        ],
    },
    {
        "name": "Водонапірна вежа",
        "category": "Архітектура",
        "desc": "Символ Вінниці, споруджена у 1912 році. Нині в приміщенні вежі працює виставковий простір.",
        "address": "вул. Соборна",
        "tags": ["вежа", "водонапірна", "архітектура", "соборна"],
        "duration": 30,
        "hours": "Ср–Нд, 10:00–18:00",
        "price": "40 грн",
        "base_rating": 4.6,
        "img": "https://picsum.photos/seed/vinnytsialandmark4/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark4a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark4b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark4c/700/450",
        ],
    },
    {
        "name": "Спасо-Преображенський кафедральний собор",
        "category": "Церква",
        "desc": "Головний православний храм міста, кафедральний собор з багатою історією та красивим інтер'єром.",
        "address": "вул. Соборна, 23",
        "tags": ["церква", "собор", "храм", "релігія"],
        "duration": 25,
        "hours": "Щодня, 07:00–19:00",
        "price": "Безкоштовно",
        "base_rating": 4.7,
        "img": "https://picsum.photos/seed/vinnytsialandmark5/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark5a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark5b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark5c/700/450",
        ],
    },
    {
        "name": "Костел Пресвятої Діви Марії Ангельської",
        "category": "Церква",
        "desc": "Один з найстаріших католицьких храмів Вінниці, зразок бароккової архітектури.",
        "address": "Старе місто",
        "tags": ["костел", "церква", "храм", "барокко"],
        "duration": 25,
        "hours": "Щодня, 08:00–18:00",
        "price": "Безкоштовно",
        "base_rating": 4.6,
        "img": "https://picsum.photos/seed/vinnytsialandmark6/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark6a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark6b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark6c/700/450",
        ],
    },
    {
        "name": "Парк Дружби народів (Центральний парк)",
        "category": "Парк",
        "desc": "Найпопулярніший парк міста для прогулянок, відпочинку та сімейного дозвілля, з алеями та атракціонами.",
        "address": "вул. Хмельницьке шосе",
        "tags": ["парк", "прогулянка", "відпочинок", "діти", "дружби народів"],
        "duration": 50,
        "hours": "Цілодобово",
        "price": "Безкоштовно",
        "base_rating": 4.7,
        "img": "https://picsum.photos/seed/vinnytsialandmark7/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark7a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark7b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark7c/700/450",
        ],
    },
    {
        "name": "Театральна площа",
        "category": "Центр",
        "desc": "Центральна площа міста з музичним драматичним театром ім. Садовського, місце проведення подій.",
        "address": "Театральна площа",
        "tags": ["площа", "театр", "центр", "події"],
        "duration": 20,
        "hours": "Цілодобово",
        "price": "Безкоштовно",
        "base_rating": 4.5,
        "img": "https://picsum.photos/seed/vinnytsialandmark8/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark8a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark8b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark8c/700/450",
        ],
    },
    {
        "name": "Музей історії міста Вінниці",
        "category": "Музей",
        "desc": "Експозиції з історії Вінниці від найдавніших часів до сьогодення.",
        "address": "вул. Соборна",
        "tags": ["музей", "історія", "експозиція"],
        "duration": 50,
        "hours": "Вт–Нд, 09:00–17:00",
        "price": "50 грн",
        "base_rating": 4.4,
        "img": "https://picsum.photos/seed/vinnytsialandmark9/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark9a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark9b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark9c/700/450",
        ],
    },
    {
        "name": "Синагога «Бейт Кнесет»",
        "category": "Релігія",
        "desc": "Діюча синагога, що є свідченням багатої єврейської історії міста.",
        "address": "центр міста",
        "tags": ["синагога", "релігія", "історія", "євреї"],
        "duration": 20,
        "hours": "За розкладом богослужінь",
        "price": "Безкоштовно",
        "base_rating": 4.5,
        "img": "https://picsum.photos/seed/vinnytsialandmark10/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark10a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark10b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark10c/700/450",
        ],
    },
    {
        "name": "Аптека-музей",
        "category": "Музей",
        "desc": "Одна з найстаріших діючих аптек в Україні з музейною експозицією історії фармації, "
                "розташована у старовинній будівлі в центрі міста.",
        "address": "вул. Соборна, 46",
        "tags": ["аптека", "музей", "фармація", "історія"],
        "duration": 25,
        "hours": "Пн–Сб, 09:00–19:00",
        "price": "30 грн",
        "base_rating": 4.6,
        "img": "https://picsum.photos/seed/vinnytsialandmark11/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark11a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark11b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark11c/700/450",
        ],
    },
    {
        "name": "Пам'ятник Устиму Кармалюку",
        "category": "Пам'ятник",
        "desc": "Пам'ятник легендарному ватажку селянського повстанського руху Устиму Кармалюку, "
                "уродженцю Поділля.",
        "address": "центр міста",
        "tags": ["пам'ятник", "кармалюк", "історія"],
        "duration": 10,
        "hours": "Цілодобово",
        "price": "Безкоштовно",
        "base_rating": 4.2,
        "img": "https://picsum.photos/seed/vinnytsialandmark12/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark12a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark12b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark12c/700/450",
        ],
    },
    {
        "name": "Вулиця Соборна",
        "category": "Центр",
        "desc": "Головна пішохідна вулиця міста з історичною забудовою, кав'ярнями та крамницями — "
                "чудове місце для неспішної прогулянки.",
        "address": "вул. Соборна",
        "tags": ["вулиця", "соборна", "прогулянка", "центр", "кафе"],
        "duration": 40,
        "hours": "Цілодобово",
        "price": "Безкоштовно",
        "base_rating": 4.7,
        "img": "https://picsum.photos/seed/vinnytsialandmark13/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark13a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark13b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark13c/700/450",
        ],
    },
    {
        "name": "Кемпа (острів відпочинку)",
        "category": "Парк",
        "desc": "Острів на Південному Бузі поруч із фонтаном Roshen — популярне місце для прогулянок, "
                "пікніків та фотосесій із краєвидом на набережну.",
        "address": "острів Кемпа",
        "tags": ["кемпа", "острів", "набережна", "прогулянка", "парк"],
        "duration": 40,
        "hours": "Цілодобово",
        "price": "Безкоштовно",
        "base_rating": 4.6,
        "img": "https://picsum.photos/seed/vinnytsialandmark14/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark14a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark14b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark14c/700/450",
        ],
    },
    {
        "name": "Ботанічний сад «Поділля»",
        "category": "Парк",
        "desc": "Науково-освітній ботанічний сад із колекцією рослин регіону Поділля, тихе місце "
                "для прогулянок і вивчення природи.",
        "address": "вул. Академічна",
        "tags": ["ботанічний сад", "поділля", "рослини", "природа", "парк"],
        "duration": 45,
        "hours": "Щодня, 08:00–18:00",
        "price": "20 грн",
        "base_rating": 4.5,
        "img": "https://picsum.photos/seed/vinnytsialandmark15/500/320",
        "gallery": [
            "https://picsum.photos/seed/vinnytsialandmark15a/700/450",
            "https://picsum.photos/seed/vinnytsialandmark15b/700/450",
            "https://picsum.photos/seed/vinnytsialandmark15c/700/450",
        ],
    },
]

# Події: додано тип, ціну та орієнтовну тривалість у днях
EVENTS = [
    {
        "name": "VinnytsiaJazzFest",
        "date": "Червень",
        "month": 6,
        "type": "Музика",
        "price": "Безкоштовно",
        "days": 3,
        "desc": "Міжнародний джазовий фестиваль просто неба за участю українських та закордонних музикантів.",
        "place": "Центральний парк / набережна",
    },
    {
        "name": "Vinnytsia Food Fest",
        "date": "Липень–Серпень",
        "month": 7,
        "type": "Їжа",
        "price": "Вхід вільний, оплата страв окремо",
        "days": 2,
        "desc": "Фестиваль вуличної їжі з десятками локальних закладів і фудтраків.",
        "place": "Театральна площа",
    },
    {
        "name": "«Острів Європи»",
        "date": "Вересень",
        "month": 9,
        "type": "Культура",
        "price": "Безкоштовно",
        "days": 2,
        "desc": "Мультикультурний фестиваль, присвячений європейським традиціям, музиці та кухні різних країн.",
        "place": "Набережна / Кемпа",
    },
    {
        "name": "День міста Вінниці",
        "date": "Вересень",
        "month": 9,
        "type": "Культура",
        "price": "Безкоштовно",
        "days": 1,
        "desc": "Головне міське свято з концертами, ярмарками та феєрверком.",
        "place": "Центр міста",
    },
    {
        "name": "Різдвяний ярмарок",
        "date": "Грудень",
        "month": 12,
        "type": "Сім'я",
        "price": "Безкоштовно",
        "days": 20,
        "desc": "Новорічно-різдвяний ярмарок з ковзанкою, гарячими напоями та сувенірами.",
        "place": "Театральна площа",
    },
    {
        "name": "Фестиваль повітряних зміїв",
        "date": "Травень",
        "month": 5,
        "type": "Сім'я",
        "price": "Безкоштовно",
        "days": 1,
        "desc": "Сімейне свято на березі Південного Бугу з майстер-класами для дітей та запуском зміїв.",
        "place": "Набережна",
    },
]

RESTAURANTS = [
    {
        "name": "Кафе «Вишня»", "type": "Українська кухня", "rating": 4.7, "price": "$$",
        "address": "вул. Соборна, 12", "hours": "09:00–22:00", "phone": "+380 43 200-11-22",
        "tags": ["українська", "затишно", "сімейне"],
    },
    {
        "name": "Пивна ресторація «Козак Мамай»", "type": "Українська / пиво", "rating": 4.5, "price": "$$",
        "address": "вул. Соборна, 34", "hours": "12:00–24:00", "phone": "+380 43 200-22-33",
        "tags": ["пиво", "українська", "компанія"],
    },
    {
        "name": "PizzaMasters", "type": "Італійська", "rating": 4.4, "price": "$",
        "address": "вул. Пирогова, 5", "hours": "10:00–23:00", "phone": "+380 43 200-33-44",
        "tags": ["піца", "швидко", "доставка"],
    },
    {
        "name": "Sushi-Ya", "type": "Японська", "rating": 4.6, "price": "$$",
        "address": "вул. Хмельницьке шосе, 7", "hours": "11:00–22:00", "phone": "+380 43 200-44-55",
        "tags": ["суші", "японська", "доставка"],
    },
    {
        "name": "Кав'ярня «Львівська майстерня шоколаду»", "type": "Кав'ярня", "rating": 4.8, "price": "$",
        "address": "вул. Соборна, 20", "hours": "08:00–21:00", "phone": "+380 43 200-55-66",
        "tags": ["кава", "десерти", "шоколад"],
    },
    {
        "name": "Steak House Bull", "type": "Стейки", "rating": 4.6, "price": "$$$",
        "address": "вул. Козицького, 15", "hours": "12:00–23:00", "phone": "+380 43 200-66-77",
        "tags": ["стейк", "м'ясо", "романтично"],
    },
    {
        "name": "Vegan Corner", "type": "Вегетаріанська/веганська", "rating": 4.5, "price": "$",
        "address": "вул. Немирівське шосе, 3", "hours": "09:00–20:00", "phone": "+380 43 200-77-88",
        "tags": ["веган", "вегетаріанська", "здорова їжа"],
    },
]

HOTELS = [
    {"name": "Готель «南Buk»", "stars": 4, "price_night": "1400 грн", "address": "набережна Південного Бугу"},
    {"name": "Hotel Vinnytsia", "stars": 3, "price_night": "900 грн", "address": "центр міста"},
    {"name": "Апарт-готель «Кемпа Residence»", "stars": 4, "price_night": "1600 грн", "address": "поруч з островом Кемпа"},
    {"name": "Хостел «Дружба»", "stars": 2, "price_night": "400 грн", "address": "вул. Хмельницьке шосе"},
]

TRANSPORT_INFO = """
**Як дістатися до Вінниці:**
- 🚄 Поїздом — прямі рейси з Києва (~3 год), Львова, Одеси, Хмельницького.
- 🚌 Автобусом — регулярні рейси з більшості обласних центрів України.
- 🚗 Автомобілем — траса М12 (Стрий–Знам'янка) проходить через місто.
- ✈️ Найближчий аеропорт — Вінницький міжнародний аеропорт "Гавришівка".

**Міський транспорт:**
- 🚋 Тролейбуси та автобуси — основний вид громадського транспорту, оплата готівкою або картою.
- 🚲 Розвинена мережа велодоріжок, доступна оренда велосипедів (bikesharing).
- 🚕 Таксі та каршерінг доступні через мобільні застосунки (Uber, Bolt, Uklon).
- 🚶 Історичний центр компактний — більшість пам'яток можна обійти пішки за 1 день.
"""

ACHIEVEMENTS = """
- 🏆 Неодноразово визнавалась одним із найкращих міст України для життя.
- 💧 Фонтан Roshen — найбільший плавучий фонтан у Європі.
- 🌳 Високий рівень озеленення та комфортна міська інфраструктура.
- 🏥 Потужна медична школа, започаткована М. Пироговим.
- 💡 Активний розвиток «розумного міста» (Smart City): електронні сервіси, відеоспостереження, енергоефективність.
"""

EDUCATION_INFO = """
**Заклади вищої освіти:**
- Вінницький національний технічний університет (ВНТУ)
- Вінницький національний медичний університет ім. М.І. Пирогова
- Донецький національний університет ім. Василя Стуса (переміщений до Вінниці)
- Вінницький державний педагогічний університет ім. Михайла Коцюбинського

Місто є важливим освітнім центром Поділля з розвиненою мережею шкіл, коледжів та наукових установ.
"""

CLIMATE_INFO = """
**Клімат:** помірно-континентальний.
- ☀️ Літо: тепле, середня температура +19…+24 °C (можливо до +30 °C).
- ❄️ Зима: помірно холодна, середня температура −3…−6 °C.
- 🌦️ Найбільш дощові місяці — червень і липень.
- 🧥 Найкращий час для відвідування: травень–вересень.
"""

# =========================================================
#                       ЧАТ-БОТ (RULE-BASED)
# =========================================================

KNOWLEDGE_BASE = {
    "фонтан": {
        "keywords": ["фонтан", "roshen", "рошен", "шоу фонтану"],
        "answer": "💦 **Фонтан Roshen** — найбільший плавучий світломузичний фонтан у Європі, "
                  "розташований на річці Південний Буг біля Кемпи. Шоу відбувається у теплу пору "
                  "року у вечірній час — вода, світло та музика зливаються в яскраве видовище. Вхід безкоштовний.",
    },
    "пирогов": {
        "keywords": ["пирогов", "музей пирогова", "вишня", "хірург"],
        "answer": "🏥 **Музей-садиба М.І. Пирогова «Вишня»** — місце, де жив і працював видатний хірург. "
                  "У церкві-некрополі на території садиби зберігається забальзамоване тіло вченого. "
                  "Адреса: вул. Пирогова, 155. Графік: Вт–Нд, 09:00–17:00.",
    },
    "вежа": {
        "keywords": ["вежа", "водонапірна", "водонапирна"],
        "answer": "🗼 **Водонапірна вежа** — символ Вінниці, побудована у 1912 році. "
                  "Сьогодні в її приміщенні працює виставковий простір. Адреса: вул. Соборна. "
                  "Графік: Ср–Нд, 10:00–18:00.",
    },
    "мури": {
        "keywords": ["мури", "фортеця", "єзуїт"],
        "answer": "🏰 **Вінницькі мури** — залишки укріплень єзуїтського монастиря XVII століття, "
                  "одна з найстаріших пам'яток міста в історичному центрі. Вхід безкоштовний, доступні цілодобово.",
    },
    "церква": {
        "keywords": ["церква", "собор", "костел", "храм", "релігія", "синагога"],
        "answer": "⛪ У Вінниці варто відвідати: **Спасо-Преображенський кафедральний собор**, "
                  "**Костел Пресвятої Діви Марії Ангельської** та діючу **синагогу «Бейт Кнесет»** — "
                  "всі вони мають багату історію та цікаву архітектуру.",
    },
    "парк": {
        "keywords": ["парк", "прогулянка", "відпочинок", "дружби народів", "кемпа", "ботанічний", "погуляти", "зелень"],
        "answer": "🌳 Для прогулянок радимо: **Парк Дружби народів** (алеї, атракціони), "
                  "острів **Кемпа** (краєвиди на річку) та **Ботанічний сад «Поділля»** (тиша й природа).",
    },
    "ресторан": {
        "keywords": ["ресторан", "їжа", "поїсти", "кафе", "де поїсти", "кухня", "веган",
                     "перекусити", "голодний", "їдальня", "смачно поїсти", "пообідати", "повечеряти"],
        "answer": "🍽️ Рекомендую переглянути розділ **«Ресторани»** — там є підбірка закладів з рейтингами, "
                  "адресами й контактами: від української кухні до суші, стейків і веганських страв.",
    },
    "готель": {
        "keywords": ["готель", "хостел", "де зупинитись", "проживання", "ночівля", "заночувати", "переночувати"],
        "answer": "🏨 У розділі **«Про місто» → Проживання** є варіанти готелів і хостелів різної цінової категорії.",
    },
    "транспорт": {
        "keywords": ["транспорт", "як дістатися", "поїзд", "автобус", "аеропорт", "тролейбус"],
        "answer": "🚌 Детальна інформація про транспорт є на сторінці **«Про місто»**. Коротко: до Вінниці "
                  "зручно дістатись поїздом з Києва (~3 год), а містом їздять тролейбуси та автобуси.",
    },
    "історія": {
        "keywords": ["історія", "заснування", "коли засновано", "рік заснування"],
        "answer": "📜 Вінниця вперше згадується в літописах у **1363 році**. За багатовікову історію місто "
                  "було під владою Литви, Польщі, Російської імперії, а нині є обласним центром України.",
    },
    "події": {
        "keywords": ["подія", "фестиваль", "джазфест", "jazzfest", "food fest", "острів європи", "свято"],
        "answer": "🎉 У Вінниці щороку проходять: **VinnytsiaJazzFest** (червень), **Vinnytsia Food Fest** "
                  "(липень–серпень), **«Острів Європи»** (вересень) та **Різдвяний ярмарок** (грудень). "
                  "Деталі — на сторінці «Події».",
    },
    "погода": {
        "keywords": ["погода", "температура", "прогноз", "клімат"],
        "answer": "🌤️ Актуальну погоду у Вінниці можна побачити на **Головній сторінці** — там підключений "
                  "живий прогноз. Найкращий час для візиту — травень–вересень.",
    },
    "маршрут": {
        "keywords": ["маршрут", "план", "екскурсія", "куди піти", "що відвідати за день"],
        "answer": "🗺️ Скористайтеся сторінкою **«Маршрут»** — оберіть пам'ятки, і я складу для вас "
                  "оптимальний порядок відвідування з орієнтовним часом.",
    },
    "мої плани": {
        "keywords": ["мої плани", "відвідано", "хронологія", "щоденник", "враження", "мій прогрес"],
        "answer": "📔 На сторінці **«Мої плани»** ви побачите візуальну хронологію відвіданих пам'яток. "
                  "Позначайте місця кнопкою «✅ Позначити як відвідано» на сторінці «Пам'ятки» — "
                  "і вони з'являться там із датою та вашими нотатками.",
    },
    "транспорт онлайн": {
        "keywords": ["де тролейбус", "де трамвай", "транспорт зараз", "живий транспорт", "реальний час", "gps транспорт"],
        "answer": "🚌 На сторінці **«Транспорт онлайн»** є демонстраційна карта руху транспорту та посилання "
                  "на офіційні джерела (map.et.vn.ua, EasyWay) для перегляду реального розташування "
                  "тролейбусів і трамваїв.",
    },
    "фото": {
        "keywords": ["фото", "фотографії", "галерея", "зображення", "картинки"],
        "answer": "📸 У кожної пам'ятки на сторінці «Пам'ятки» є розділ **«Фотогалерея»** — розгорніть його, "
                  "щоб погортати кілька фото цього місця.",
    },
    "освіта": {
        "keywords": ["освіта", "університет", "навчання", "студент"],
        "answer": "🎓 У Вінниці працюють кілька провідних ЗВО, зокрема **ВНТУ** та "
                  "**Вінницький національний медичний університет ім. Пирогова**. Деталі — на сторінці «Про місто».",
    },
    "експорт": {
        "keywords": ["експорт", "імпорт", "зберегти дані", "завантажити дані", "backup", "бекап"],
        "answer": "💾 На сторінці **«Експорт/Імпорт»** можна зберегти обране, відгуки та маршрут у файл, "
                  "а також завантажити раніше збережені дані назад.",
    },
}

GREETINGS = ["привіт", "вітаю", "добрий день", "доброго дня", "хай", "hello", "hi"]
THANKS = ["дякую", "спасибі", "дяка", "thanks"]

QUICK_QUESTIONS = [
    "Розкажи про фонтан Roshen",
    "Де музей Пирогова?",
    "Які події найближчим часом?",
    "Порадь ресторан",
    "Як дістатися до Вінниці?",
    "Склади маршрут на день",
]

# Теми, що прив'язані до конкретної, унікальної пам'ятки — потрібно для контекстної пам'яті:
# якщо бот щойно розповів про цю тему, наступне уточнювальне питання ("а скільки коштує?")
# буде застосоване саме до цієї пам'ятки.
TOPIC_TO_LANDMARK = {
    "фонтан": "Фонтан Roshen",
    "пирогов": "Музей-садиба М.І. Пирогова «Вишня»",
    "вежа": "Водонапірна вежа",
    "мури": "Вінницькі мури (Мури)",
}

# Уточнювальні (follow-up) фрази — не прив'язані до конкретної теми, а стосуються
# того, про що йшлося щойно (контекст розмови).
FOLLOWUP_PRICE = ["скільки коштує", "яка ціна", "почому", "вартість", "це платно", "скільки це коштує", "ціна квитка"]
FOLLOWUP_HOURS = ["коли працює", "графік роботи", "розклад роботи", "о котрій", "до котрої", "коли можна прийти"]
FOLLOWUP_ADDRESS = ["де знаходиться", "яка адреса", "де це", "куди йти", "як туди дістатися", "де це знаходиться"]
FOLLOWUP_DURATION = ["скільки часу", "як довго", "тривалість відвідування", "скільки треба часу"]


def _fuzzy_ratio(a: str, b: str) -> float:
    """Ступінь схожості двох рядків (0-100). Використовує найкращу доступну бібліотеку:
    rapidfuzz -> fuzzywuzzy -> стандартний difflib (завжди доступний, без встановлення).
    Це дозволяє боту розуміти запити з друкарськими помилками та синонімами."""
    if HAS_RAPIDFUZZ:
        return _rf_fuzz.ratio(a, b)
    try:
        from fuzzywuzzy import fuzz as _fw_fuzz
        return _fw_fuzz.ratio(a, b)
    except ImportError:
        pass
    return difflib.SequenceMatcher(None, a, b).ratio() * 100


FUZZY_THRESHOLD = 78  # від 0 до 100; нижче — толерантніше до помилок, вище — суворіше


def _keyword_score(text_clean: str, keywords) -> int:
    """Оцінює збіг тексту користувача з ключовими словами теми.
    Точний підрядок дає 2 бали (сильний сигнал), нечіткий збіг (помилка/синонім) — 1 бал."""
    words = [w for w in text_clean.split() if len(w) > 2]
    score = 0
    for kw in keywords:
        if kw in text_clean:
            score += 2
            continue
        if " " in kw:
            if _fuzzy_ratio(kw, text_clean) >= FUZZY_THRESHOLD:
                score += 1
        else:
            if any(_fuzzy_ratio(kw, w) >= FUZZY_THRESHOLD for w in words):
                score += 1
    return score


def _matches_any(text_clean: str, phrases) -> bool:
    """Перевіряє, чи текст користувача відповідає одній із фраз (точно або нечітко)."""
    for p in phrases:
        if p in text_clean:
            return True
        if _fuzzy_ratio(p, text_clean) >= FUZZY_THRESHOLD:
            return True
    return False


def get_bot_response(user_text: str) -> str:
    """Логіка чат-бота: розпізнавання ключових слів + нечіткий пошук (typo/синоніми-стійкий)
    та контекстна пам'ять — бот пам'ятає останню згадану пам'ятку/тему й розуміє уточнення."""
    text = user_text.lower().strip()
    text_clean = re.sub(r"[^\w\sа-яіїєґ]", "", text)

    ctx = st.session_state.chat_context

    if any(g in text_clean for g in GREETINGS):
        return ("Вітаю! 👋 Я віртуальний гід по Вінниці. Запитайте мене про пам'ятки, ресторани, "
                "події, готелі, погоду, освіту чи маршрут — і я підкажу! До речі, я пам'ятаю "
                "контекст розмови 🧠 — можна ставити уточнювальні питання.")

    if any(t in text_clean for t in THANKS):
        return "Будь ласка! 😊 Якщо ще щось цікавить — питайте."

    # 1) Уточнювальне питання про конкретну щойно згадану пам'ятку
    if ctx.get("last_landmark"):
        name_to_item = {i["name"]: i for i in LANDMARKS}
        item = name_to_item.get(ctx["last_landmark"])
        if item:
            if _matches_any(text_clean, FOLLOWUP_PRICE):
                return f"💵 Вхід до «{item['name']}» коштує: **{item['price']}**."
            if _matches_any(text_clean, FOLLOWUP_HOURS):
                return f"🕒 Графік роботи «{item['name']}»: **{item['hours']}**."
            if _matches_any(text_clean, FOLLOWUP_ADDRESS):
                return f"📍 «{item['name']}» знаходиться за адресою: **{item['address']}**."
            if _matches_any(text_clean, FOLLOWUP_DURATION):
                return f"⏱ Огляд «{item['name']}» зазвичай займає близько **{item['duration']} хв**."

    # 2) Уточнення про ціни в контексті теми "ресторани" (без прив'язки до одного закладу)
    if ctx.get("last_topic") == "ресторан" and _matches_any(text_clean, FOLLOWUP_PRICE):
        cheapest = min(RESTAURANTS, key=lambda r: len(r["price"]))
        priciest = max(RESTAURANTS, key=lambda r: len(r["price"]))
        return (
            "💵 Ціни в ресторанах Вінниці різняться: від бюджетних закладів на кшталт "
            f"«{cheapest['name']}» ({cheapest['price']}) до преміальних, як "
            f"«{priciest['name']}» ({priciest['price']}). Детальніше — на сторінці «Ресторани»."
        )

    # 3) Пошук найкращої теми: точні ключові слова + нечіткий (typo/синонім-стійкий) пошук
    best_topic, best_score = None, 0
    for topic, data in KNOWLEDGE_BASE.items():
        score = _keyword_score(text_clean, data["keywords"])
        if score > best_score:
            best_score = score
            best_topic = topic

    if best_topic and best_score > 0:
        ctx["last_topic"] = best_topic
        ctx["last_landmark"] = TOPIC_TO_LANDMARK.get(best_topic)
        return KNOWLEDGE_BASE[best_topic]["answer"]

    return ("🤔 Вибачте, я поки не знаю відповіді на це питання. Спробуйте запитати про фонтан Roshen, "
            "музей Пирогова, Вінницькі мури, церкви, парки, ресторани, готелі, транспорт, погоду, "
            "освіту, історію, події чи маршрут по місту.")




# =========================================================
#                       ДОПОМІЖНІ ФУНКЦІЇ
# =========================================================

def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "Головна"
    if "fav_landmarks" not in st.session_state:
        st.session_state.fav_landmarks = set()
    if "fav_restaurants" not in st.session_state:
        st.session_state.fav_restaurants = set()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Вітаю! 👋 Я віртуальний гід по Вінниці. Чим можу допомогти?"}
        ]
    if "feedback_log" not in st.session_state:
        st.session_state.feedback_log = []
    if "reviews" not in st.session_state:
        st.session_state.reviews = {}  # {landmark_name: [{"author":..,"rating":..,"text":..}]}
    if "last_route" not in st.session_state:
        st.session_state.last_route = []
    if "import_message" not in st.session_state:
        st.session_state.import_message = None
    if "visited" not in st.session_state:
        st.session_state.visited = {}  # {landmark_name: {"date": "YYYY-MM-DD", "note": str}}
    if "transport_positions" not in st.session_state:
        st.session_state.transport_positions = None
    if "transport_tick" not in st.session_state:
        st.session_state.transport_tick = 0
    if "chat_context" not in st.session_state:
        st.session_state.chat_context = {"last_topic": None, "last_landmark": None}


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather():
    """Отримує поточну погоду для Вінниці через безкоштовне Open-Meteo API (без ключа)."""
    if not HAS_REQUESTS:
        return None
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={VINNYTSIA_LAT}&longitude={VINNYTSIA_LON}"
            "&current_weather=true"
        )
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("current_weather")
    except Exception:
        return None
    return None


WEATHER_CODES = {
    0: "☀️ Ясно", 1: "🌤️ Малохмарно", 2: "⛅ Хмарно", 3: "☁️ Похмуро",
    45: "🌫️ Туман", 48: "🌫️ Паморозь",
    51: "🌦️ Легка мряка", 61: "🌧️ Невеликий дощ", 63: "🌧️ Дощ", 65: "🌧️ Сильний дощ",
    71: "🌨️ Невеликий сніг", 73: "🌨️ Сніг", 75: "❄️ Сильний сніг",
    80: "🌦️ Зливи", 95: "⛈️ Гроза",
}


def average_rating(landmark_name, base_rating):
    revs = st.session_state.reviews.get(landmark_name, [])
    if not revs:
        return base_rating, 0
    total = base_rating + sum(r["rating"] for r in revs)
    count = 1 + len(revs)
    return round(total / count, 2), len(revs)


def build_route(selected_names, start_time_str):
    """Простий генератор маршруту: зберігає порядок вибору, рахує час відвідування + 15 хв на переїзд."""
    try:
        h, m = map(int, start_time_str.split(":"))
        current = datetime(2000, 1, 1, h, m)
    except Exception:
        current = datetime(2000, 1, 1, 9, 0)

    route = []
    name_to_item = {i["name"]: i for i in LANDMARKS}
    for name in selected_names:
        item = name_to_item[name]
        start = current
        end = start + timedelta(minutes=item["duration"])
        route.append({
            "name": name,
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "duration": item["duration"],
            "address": item["address"],
        })
        current = end + timedelta(minutes=15)  # +15 хв на переїзд/перехід
    return route, current.strftime("%H:%M")


def mark_visited(name, note=""):
    st.session_state.visited[name] = {
        "date": date.today().isoformat(),
        "note": note,
    }


def unmark_visited(name):
    st.session_state.visited.pop(name, None)


def get_visited_sorted():
    """Повертає відвідані пам'ятки, відсортовані за датою (від найновіших)."""
    name_to_item = {i["name"]: i for i in LANDMARKS}
    entries = []
    for name, info in st.session_state.visited.items():
        item = name_to_item.get(name)
        if item:
            entries.append({"name": name, "date": info.get("date", ""), "note": info.get("note", ""), "item": item})
    entries.sort(key=lambda x: x["date"], reverse=True)
    return entries


# --- Демо-симуляція транспорту в реальному часі ------------------------------
# ПРИМІТКА: офіційна система GPS-моніторингу транспорту Вінниці (map.et.vn.ua,
# КП "Вінницякартсервіс") є закритою для стороннього комерційного використання
# й не надає публічного відкритого API. Тому нижче реалізовано наочну ДЕМО-симуляцію
# руху транспорту навколо реальних зупинок/маршрутів — вона чітко позначена як демо
# і не видається за справжні дані. За реальним рухом дивіться офіційні джерела нижче.
TRANSPORT_ROUTES = [
    {"line": "Тролейбус №4", "type": "🚎", "lat": 49.2331, "lon": 28.4682},
    {"line": "Тролейбус №7", "type": "🚎", "lat": 49.2365, "lon": 28.4610},
    {"line": "Трамвай №3", "type": "🚋", "lat": 49.2285, "lon": 28.4755},
    {"line": "Автобус №20", "type": "🚌", "lat": 49.2410, "lon": 28.4820},
    {"line": "Маршрутка №2А", "type": "🚐", "lat": 49.2260, "lon": 28.4590},
]

OFFICIAL_TRANSPORT_LINKS = [
    {"name": "Онлайн-карта руху транспорту (КП «Вінницякартсервіс»)", "url": "https://map.et.vn.ua/"},
    {"name": "Маршрути Вінниці на EasyWay", "url": "https://www.eway.in.ua/ua/cities/vinnytsia/routes"},
    {"name": "Розклад руху транспорту (rozklad.in.ua)", "url": "https://vn.rozklad.in.ua/"},
]


def simulate_transport_tick():
    """Генерує/оновлює демонстраційні координати транспорту випадковим 'блуканням' навколо базових точок."""
    import random
    if st.session_state.transport_positions is None:
        st.session_state.transport_positions = [dict(t) for t in TRANSPORT_ROUTES]

    for pos in st.session_state.transport_positions:
        pos["lat"] += random.uniform(-0.0025, 0.0025)
        pos["lon"] += random.uniform(-0.0025, 0.0025)
    st.session_state.transport_tick += 1
    return st.session_state.transport_positions



    """Формує JSON-знімок усіх даних користувача для експорту."""
    snapshot = {
        "app_version": APP_VERSION,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "fav_landmarks": sorted(st.session_state.fav_landmarks),
        "fav_restaurants": sorted(st.session_state.fav_restaurants),
        "reviews": st.session_state.reviews,
        "feedback_log": st.session_state.feedback_log,
        "last_route": st.session_state.last_route,
        "visited": st.session_state.visited,
    }
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def import_snapshot(raw_text):
    """Завантажує дані користувача з JSON-рядка назад у session_state."""
    data = json.loads(raw_text)
    st.session_state.fav_landmarks = set(data.get("fav_landmarks", []))
    st.session_state.fav_restaurants = set(data.get("fav_restaurants", []))
    st.session_state.reviews = data.get("reviews", {})
    st.session_state.feedback_log = data.get("feedback_log", [])
    st.session_state.last_route = data.get("last_route", [])
    st.session_state.visited = data.get("visited", {})


def landmarks_to_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Назва", "Категорія", "Адреса", "Графік", "Вартість", "Тривалість (хв)", "Опис"])
    for i in LANDMARKS:
        writer.writerow([i["name"], i["category"], i["address"], i["hours"], i["price"], i["duration"], i["desc"]])
    return output.getvalue()


def restaurants_to_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Назва", "Тип кухні", "Рейтинг", "Ціна", "Адреса", "Графік", "Телефон"])
    for r in RESTAURANTS:
        writer.writerow([r["name"], r["type"], r["rating"], r["price"], r["address"], r["hours"], r["phone"]])
    return output.getvalue()


def events_to_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Назва", "Період", "Тип", "Ціна", "Тривалість (днів)", "Місце", "Опис"])
    for e in EVENTS:
        writer.writerow([e["name"], e["date"], e["type"], e["price"], e["days"], e["place"], e["desc"]])
    return output.getvalue()


def route_to_text(route, finish):
    lines = [f"Маршрут по Вінниці — завершення о {finish}", ""]
    for i, stop in enumerate(route, start=1):
        lines.append(f"{i}. {stop['name']} — {stop['start']}–{stop['end']} ({stop['duration']} хв) · {stop['address']}")
    return "\n".join(lines)


# --- Генерація PDF-гіда (reportlab) ------------------------------------------
# Для коректного відображення кирилиці потрібен TTF-шрифт з підтримкою укр. літер
# (стандартні PDF-шрифти Helvetica/Times цього не вміють). Шукаємо поширені шрифти
# в системі; якщо не знайдено — акуратно транслітеруємо текст у латиницю,
# щоб PDF все одно згенерувався коректно, без "квадратиків" замість літер.
CANDIDATE_REGULAR_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]
CANDIDATE_BOLD_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
]

UA_TRANSLIT_TABLE = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e", "є": "ie",
    "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i", "к": "k", "л": "l",
    "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ь": "",
    "ю": "iu", "я": "ia", "'": "", "’": "", "–": "-", "—": "-",
}


def transliterate_ua(text):
    """Запасний варіант для PDF без кириличного шрифту: транслітерує укр. текст у латиницю."""
    result = []
    for ch in text:
        lower = ch.lower()
        if lower in UA_TRANSLIT_TABLE:
            repl = UA_TRANSLIT_TABLE[lower]
            if ch.isupper() and repl:
                repl = repl[0].upper() + repl[1:]
            result.append(repl)
        else:
            result.append(ch)
    return "".join(result)


def _find_font(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


def _register_pdf_fonts():
    """Реєструє TTF-шрифт із кирилицею для reportlab. Повертає (regular, bold, знайдено_кирилицю)."""
    if not HAS_REPORTLAB:
        return None, None, False
    regular = _find_font(CANDIDATE_REGULAR_FONTS)
    bold = _find_font(CANDIDATE_BOLD_FONTS) or regular
    if not regular:
        return "Helvetica", "Helvetica-Bold", False
    try:
        pdfmetrics.registerFont(TTFont("GuideFont", regular))
        pdfmetrics.registerFont(TTFont("GuideFont-Bold", bold))
        return "GuideFont", "GuideFont-Bold", True
    except Exception:
        return "Helvetica", "Helvetica-Bold", False


def generate_pdf_guide(landmark_names, title="Мій путівник по Вінниці", schedule=None):
    """Формує гарно оформлений PDF-гід із вибраними пам'ятками.
    schedule: необов'язковий dict {назва_пам'ятки: 'HH:MM–HH:MM'} для маршруту.
    Повертає (pdf_bytes, warning) де warning не None, якщо кирилицю довелось транслітерувати
    або якщо reportlab взагалі не встановлено."""
    if not HAS_REPORTLAB:
        return None, "no-reportlab"

    font_name, font_bold, cyrillic_ok = _register_pdf_fonts()

    def T(text):
        return text if cyrillic_ok else transliterate_ua(text)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "GuideTitle", parent=styles["Title"], fontName=font_bold, fontSize=24,
        textColor=colors.HexColor("#1b5e20"), spaceAfter=8, alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "GuideSubtitle", parent=styles["Normal"], fontName=font_name, fontSize=11,
        textColor=colors.HexColor("#555555"), alignment=1, spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "GuideH2", parent=styles["Heading2"], fontName=font_bold, fontSize=15,
        textColor=colors.HexColor("#1b5e20"), spaceBefore=10, spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "GuideMeta", parent=styles["Normal"], fontName=font_name, fontSize=9.5,
        textColor=colors.HexColor("#2e7d32"), spaceAfter=6, leading=14,
    )
    body_style = ParagraphStyle(
        "GuideBody", parent=styles["Normal"], fontName=font_name, fontSize=10.5,
        textColor=colors.HexColor("#222222"), spaceAfter=10, leading=15,
    )
    warn_style = ParagraphStyle(
        "GuideWarn", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=8.5,
        textColor=colors.HexColor("#b71c1c"), alignment=1,
    )

    story = [
        Spacer(1, 40),
        Paragraph(T(title), title_style),
        Paragraph(T("Особистий путівник, згенерований платформою «Моя Вінниця»"), subtitle_style),
        Paragraph(T(f"Дата створення: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), subtitle_style),
        Paragraph(T(f"Кількість пам'яток: {len(landmark_names)}"), subtitle_style),
    ]
    if not cyrillic_ok:
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            "Note: no Cyrillic-capable font found on this system, "
            "so text below is transliterated to Latin letters.",
            warn_style,
        ))
    story.append(PageBreak())

    name_to_item = {i["name"]: i for i in LANDMARKS}
    for idx, name in enumerate(landmark_names, start=1):
        item = name_to_item.get(name)
        if not item:
            continue
        story.append(Paragraph(T(f"{idx}. {item['name']}"), h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#a5d6a7"), spaceAfter=6))

        meta_lines = []
        if schedule and name in schedule:
            meta_lines.append(T(f"Час у маршруті: {schedule[name]}"))
        meta_lines += [
            T(f"Категорія: {item['category']}"),
            T(f"Адреса: {item['address']}"),
            T(f"Графік роботи: {item['hours']}"),
            T(f"Вартість входу: {item['price']}"),
            T(f"Орієнтовний час відвідування: {item['duration']} хв"),
        ]
        story.append(Paragraph("<br/>".join(meta_lines), meta_style))
        story.append(Paragraph(T(item["desc"]), body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes, (None if cyrillic_ok else "no-cyrillic-font")


# =========================================================
#                       ІНТЕРФЕЙС STREAMLIT
# =========================================================

def render_header():
    st.markdown(
        """
        <style>
        .hero {
            padding: 2rem;
            border-radius: 16px;
            background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 60%, #66bb6a 100%);
            color: white;
            text-align: center;
            margin-bottom: 0.6rem;
            box-shadow: 0 6px 18px rgba(27, 94, 32, 0.25);
        }
        .hero h1 { font-size: 2.6rem; margin-bottom: 0.3rem; }
        .hero p { font-size: 1.1rem; opacity: 0.95; }
        .hero-emojis {
            text-align: center;
            font-size: 1.3rem;
            letter-spacing: 0.6rem;
            margin-bottom: 1.5rem;
            opacity: 0.9;
        }
        .stat-box {
            background: #f1f8e9;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 1px solid #c5e1a5;
            transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        .stat-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 14px rgba(102, 187, 106, 0.35);
        }
        .stat-box .stat-icon { font-size: 1.6rem; }
        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            background: #e8f5e9;
            color: #1b5e20;
            font-size: 0.78rem;
            margin: 2px 4px 2px 0;
            border: 1px solid #a5d6a7;
        }
        .badge-price {
            background: #fff8e1;
            color: #8d6e00;
            border: 1px solid #ffe082;
        }
        .badge-rating {
            background: #fff3e0;
            color: #e65100;
            border: 1px solid #ffcc80;
        }
        .section-divider {
            text-align: center;
            color: #66bb6a;
            letter-spacing: 0.5rem;
            margin: 0.5rem 0 1.2rem 0;
            font-size: 1rem;
        }
        .stButton>button {
            border-radius: 10px;
            border: 1px solid #a5d6a7;
            transition: all 0.15s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #2e7d32;
            color: white;
            border-color: #2e7d32;
        }
        .timeline {
            border-left: 3px solid #66bb6a;
            margin-left: 12px;
            padding-left: 24px;
        }
        .timeline-item {
            position: relative;
            margin-bottom: 22px;
        }
        .timeline-dot {
            position: absolute;
            left: -31px;
            top: 4px;
            width: 14px;
            height: 14px;
            background: #2e7d32;
            border-radius: 50%;
            border: 2px solid #f1f8e9;
        }
        .timeline-card {
            background: #f1f8e9;
            border: 1px solid #c5e1a5;
            border-radius: 12px;
            padding: 0.8rem 1rem;
        }
        .timeline-date {
            color: #2e7d32;
            font-weight: 600;
            font-size: 0.85rem;
        }
        .transport-card {
            background: #f1f8e9;
            border: 1px solid #c5e1a5;
            border-radius: 10px;
            padding: 0.6rem 0.9rem;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_divider(emoji="🌿"):
    st.markdown(f"<div class='section-divider'>{emoji} &nbsp; {emoji} &nbsp; {emoji}</div>", unsafe_allow_html=True)


def page_home():
    st.markdown(
        """
        <div class="hero">
            <h1>🏙️ Моя Вінниця</h1>
            <p>Відкрийте для себе пам'ятки, події та смаки одного з найкрасивіших міст України ✨</p>
        </div>
        <div class="hero-emojis">💧 🏰 🌳 ⛪ 🍽️ 🎉</div>
        """,
        unsafe_allow_html=True,
    )

    weather = fetch_weather()
    if weather:
        code = weather.get("weathercode", 0)
        desc = WEATHER_CODES.get(code, "🌡️")
        st.info(
            f"**Погода у Вінниці зараз:** {desc} · {weather.get('temperature')}°C · "
            f"вітер {weather.get('windspeed')} км/год"
        )
    elif HAS_REQUESTS:
        st.caption("⚠️ Не вдалося отримати погоду (немає з'єднання з інтернетом).")
    else:
        st.caption("ℹ️ Встановіть бібліотеку `requests`, щоб бачити live-погоду: `pip install requests`.")

    st.subheader("📊 Місто у цифрах")
    cols = st.columns(len(CITY_STATS))
    for col, (label, value) in zip(cols, CITY_STATS.items()):
        with col:
            icon = STAT_ICONS.get(label, "📌")
            st.markdown(
                f"<div class='stat-box'><div class='stat-icon'>{icon}</div>"
                f"<h3>{value}</h3><p>{label}</p></div>",
                unsafe_allow_html=True,
            )

    section_divider("🌿")
    st.subheader("⚡ Швидкий доступ")
    row1 = st.columns(4)
    row2 = st.columns(4)
    if row1[0].button("🗺️ Пам'ятки", use_container_width=True):
        st.session_state.page = "Пам'ятки"; st.rerun()
    if row1[1].button("🎉 Події", use_container_width=True):
        st.session_state.page = "Події"; st.rerun()
    if row1[2].button("🍽️ Ресторани", use_container_width=True):
        st.session_state.page = "Ресторани"; st.rerun()
    if row1[3].button("🧭 Маршрут", use_container_width=True):
        st.session_state.page = "Маршрут"; st.rerun()
    if row2[0].button("📔 Мої плани", use_container_width=True):
        st.session_state.page = "Мої плани"; st.rerun()
    if row2[1].button("🚌 Транспорт онлайн", use_container_width=True):
        st.session_state.page = "Транспорт онлайн"; st.rerun()
    if row2[2].button("🤖 Чат-бот", use_container_width=True):
        st.session_state.page = "Чат-бот"; st.rerun()
    if row2[3].button("💾 Експорт/Імпорт", use_container_width=True):
        st.session_state.page = "Експорт/Імпорт"; st.rerun()

    section_divider("💚")
    st.subheader("💡 Цікаві факти")
    for fact in FACTS:
        st.markdown(f"✨ {fact}")

    section_divider("🔍")
    st.subheader("🔎 Загальний пошук по платформі")
    query = st.text_input("Введіть назву пам'ятки, події чи ресторану", key="global_search")
    if query:
        q = query.lower()
        found_landmarks = [i for i in LANDMARKS if q in i["name"].lower() or q in i["desc"].lower()]
        found_events = [e for e in EVENTS if q in e["name"].lower() or q in e["desc"].lower()]
        found_rest = [r for r in RESTAURANTS if q in r["name"].lower() or q in r["type"].lower()]

        if not (found_landmarks or found_events or found_rest):
            st.warning("Нічого не знайдено 🤷")
        else:
            if found_landmarks:
                st.markdown("**🗺️ Пам'ятки:**")
                for i in found_landmarks:
                    icon = CATEGORY_ICONS.get(i["category"], "📍")
                    st.write(f"{icon} {i['name']} — {i['category']}")
            if found_events:
                st.markdown("**🎉 Події:**")
                for e in found_events:
                    icon = EVENT_ICONS.get(e["type"], "🎉")
                    st.write(f"{icon} {e['name']} — {e['date']}")
            if found_rest:
                st.markdown("**🍽️ Ресторани:**")
                for r in found_rest:
                    icon = RESTAURANT_ICONS.get(r["type"], "🍽️")
                    st.write(f"{icon} {r['name']} — {r['type']}, ⭐{r['rating']}")


def page_landmarks():
    st.header("🗺️ Пам'ятки Вінниці")
    search = st.text_input("🔍 Пошук пам'ятки (за назвою, категорією або ключовим словом)")

    categories = ["Усі"] + sorted(set(item["category"] for item in LANDMARKS))
    col_a, col_b = st.columns(2)
    selected_cat = col_a.selectbox("Категорія", categories)
    sort_by = col_b.selectbox("Сортувати за", ["Назвою", "Рейтингом", "Часом відвідування"])

    filtered = LANDMARKS
    if selected_cat != "Усі":
        filtered = [i for i in filtered if i["category"] == selected_cat]
    if search:
        s = search.lower()
        filtered = [
            i for i in filtered
            if s in i["name"].lower() or s in i["desc"].lower() or any(s in t for t in i["tags"])
        ]

    if sort_by == "Назвою":
        filtered = sorted(filtered, key=lambda x: x["name"])
    elif sort_by == "Рейтингом":
        filtered = sorted(filtered, key=lambda x: average_rating(x["name"], x["base_rating"])[0], reverse=True)
    else:
        filtered = sorted(filtered, key=lambda x: x["duration"])

    st.write(f"Знайдено: **{len(filtered)}** з {len(LANDMARKS)}")

    cols = st.columns(2)
    for idx, item in enumerate(filtered):
        with cols[idx % 2]:
            with st.container(border=True):
                st.image(item["img"], use_container_width=True)
                cat_icon = CATEGORY_ICONS.get(item["category"], "📍")
                st.subheader(f"{cat_icon} {item['name']}")
                avg, n_reviews = average_rating(item["name"], item["base_rating"])
                st.markdown(
                    f"<span class='badge'>{cat_icon} {item['category']}</span>"
                    f"<span class='badge badge-rating'>⭐ {avg} ({n_reviews})</span>"
                    f"<span class='badge'>⏱ ~{item['duration']} хв</span>"
                    f"<span class='badge badge-price'>💵 {item['price']}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(f"🕒 {item['hours']} &nbsp;·&nbsp; 📍 {item['address']}", unsafe_allow_html=True)
                st.write(f"📝 {item['desc']}")

                is_fav = item["name"] in st.session_state.fav_landmarks
                fav_label = "💔 Прибрати з обраного" if is_fav else "❤️ Додати в обране"
                is_visited = item["name"] in st.session_state.visited
                visit_label = "↩️ Скасувати відвідування" if is_visited else "✅ Позначити як відвідано"

                bc1, bc2 = st.columns(2)
                if bc1.button(fav_label, key=f"fav_{item['name']}", use_container_width=True):
                    if is_fav:
                        st.session_state.fav_landmarks.discard(item["name"])
                    else:
                        st.session_state.fav_landmarks.add(item["name"])
                    st.rerun()
                if bc2.button(visit_label, key=f"visit_{item['name']}", use_container_width=True):
                    if is_visited:
                        unmark_visited(item["name"])
                    else:
                        mark_visited(item["name"])
                    st.rerun()
                if is_visited:
                    st.caption(f"✅ Відвідано {st.session_state.visited[item['name']]['date']}")

                with st.expander("📸 Фотогалерея"):
                    gallery = item.get("gallery") or [item["img"]]
                    gkey = f"gallery_idx_{item['name']}"
                    if gkey not in st.session_state:
                        st.session_state[gkey] = 0
                    g_idx = st.session_state[gkey] % len(gallery)
                    st.image(gallery[g_idx], use_container_width=True)
                    st.caption(f"Фото {g_idx + 1} з {len(gallery)}")
                    gp, gn = st.columns(2)
                    if gp.button("◀️ Попереднє", key=f"prev_{item['name']}", use_container_width=True):
                        st.session_state[gkey] = (g_idx - 1) % len(gallery)
                        st.rerun()
                    if gn.button("▶️ Наступне", key=f"next_{item['name']}", use_container_width=True):
                        st.session_state[gkey] = (g_idx + 1) % len(gallery)
                        st.rerun()

                with st.expander("💬 Відгуки та оцінка"):
                    revs = st.session_state.reviews.get(item["name"], [])
                    if revs:
                        for r in revs:
                            st.markdown(f"**{r['author']}** — {'⭐' * r['rating']}")
                            st.caption(r["text"])
                    else:
                        st.caption("Ще немає відгуків. Будьте першим!")

                    with st.form(key=f"review_form_{item['name']}", clear_on_submit=True):
                        author = st.text_input("Ім'я", key=f"author_{item['name']}")
                        rating = st.slider("Оцінка", 1, 5, 5, key=f"rating_{item['name']}")
                        text = st.text_area("Ваш відгук", key=f"text_{item['name']}")
                        if st.form_submit_button("Залишити відгук"):
                            if text.strip():
                                st.session_state.reviews.setdefault(item["name"], []).append(
                                    {"author": author or "Анонім", "rating": rating, "text": text}
                                )
                                st.success("Дякуємо за відгук!")
                                st.rerun()
                            else:
                                st.warning("Напишіть текст відгуку.")


def page_events():
    st.header("🎉 Події та фестивалі")
    today = date.today()
    st.caption(f"Сьогодні: {today.strftime('%d.%m.%Y')}")

    c1, c2 = st.columns(2)
    month_filter = c1.selectbox("Фільтр за місяцем", ["Усі"] + [f"{m:02d}" for m in range(1, 13)])
    type_filter = c2.selectbox("Тип події", ["Усі"] + sorted(set(e["type"] for e in EVENTS)))

    events_to_show = EVENTS
    if month_filter != "Усі":
        events_to_show = [e for e in events_to_show if e["month"] == int(month_filter)]
    if type_filter != "Усі":
        events_to_show = [e for e in events_to_show if e["type"] == type_filter]

    if not events_to_show:
        st.info("За обраними фільтрами подій не знайдено.")

    for ev in events_to_show:
        ev_icon = EVENT_ICONS.get(ev["type"], "🎉")
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(f"{ev_icon} {ev['name']}")
                st.markdown(
                    f"<span class='badge'>{ev_icon} {ev['type']}</span>"
                    f"<span class='badge badge-price'>💵 {ev['price']}</span>"
                    f"<span class='badge'>📅 ~{ev['days']} дн.</span>",
                    unsafe_allow_html=True,
                )
                st.write(ev["desc"])
                st.caption(f"📍 {ev['place']}")
            with c2:
                st.metric("🗓️ Період", ev["date"])


def page_restaurants():
    st.header("🍽️ Ресторани Вінниці")
    c1, c2, c3 = st.columns(3)
    sort_option = c1.radio("Сортувати за:", ["Рейтингом", "Назвою"], horizontal=True)
    price_filter = c2.selectbox("Цінова категорія", ["Усі", "$", "$$", "$$$"])
    all_tags = sorted({t for r in RESTAURANTS for t in r["tags"]})
    tag_filter = c3.multiselect("Кухня / особливості", all_tags)

    data = RESTAURANTS.copy()
    if price_filter != "Усі":
        data = [r for r in data if r["price"] == price_filter]
    if tag_filter:
        data = [r for r in data if any(t in r["tags"] for t in tag_filter)]
    if sort_option == "Рейтингом":
        data.sort(key=lambda x: x["rating"], reverse=True)
    else:
        data.sort(key=lambda x: x["name"])

    st.write(f"Знайдено: **{len(data)}** з {len(RESTAURANTS)}")

    for r in data:
        stars = "⭐" * int(round(r["rating"]))
        r_icon = RESTAURANT_ICONS.get(r["type"], "🍽️")
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(
                f"**{r_icon} {r['name']}**  \n_{r['type']}_  \n"
                f"📍 {r['address']} · 🕒 {r['hours']} · ☎ {r['phone']}"
            )
            c2.write(f"{stars} {r['rating']}")
            c3.markdown(f"<span class='badge badge-price'>💵 {r['price']}</span>", unsafe_allow_html=True)
            is_fav = r["name"] in st.session_state.fav_restaurants
            label = "💔" if is_fav else "❤️"
            if c4.button(label, key=f"fav_r_{r['name']}"):
                if is_fav:
                    st.session_state.fav_restaurants.discard(r["name"])
                else:
                    st.session_state.fav_restaurants.add(r["name"])
                st.rerun()


def page_route():
    st.header("🧭 Побудова маршруту на день")
    st.write("Оберіть пам'ятки, які хочете відвідати, вкажіть час старту — і отримайте орієнтовний план дня.")

    names = [i["name"] for i in LANDMARKS]
    selected = st.multiselect("Пам'ятки для відвідування", names, default=names[:3])
    start_time = st.time_input("Час початку екскурсії", value=None)
    start_str = start_time.strftime("%H:%M") if start_time else "09:00"

    if st.button("🧮 Скласти маршрут", type="primary"):
        if not selected:
            st.warning("Оберіть хоча б одну пам'ятку.")
        else:
            route, finish = build_route(selected, start_str)
            st.session_state.last_route = route
            st.success(f"Маршрут складено! Орієнтовний час завершення: **{finish}**")
            for i, stop in enumerate(route, start=1):
                st.markdown(
                    f"**{i}. {stop['name']}** — {stop['start']}–{stop['end']} "
                    f"(⏱ {stop['duration']} хв) · 📍 {stop['address']}"
                )
                if i < len(route):
                    st.caption("🚶 ~15 хв на переїзд/перехід до наступної точки")

            st.download_button(
                "⬇️ Завантажити маршрут (.txt)",
                data=route_to_text(route, finish),
                file_name="vinnytsia_marshrut.txt",
                mime="text/plain",
            )

    section_divider("🧭")
    st.caption(
        "💡 Порада: після відвідування пам'ятки не забудьте позначити її як «✅ Відвідано» "
        "на сторінці «Пам'ятки» — вона з'явиться у вашій хронології на сторінці «Мої плани»."
    )


def page_my_plans():
    st.header("📔 Мої плани — хронологія відвідувань")
    st.caption("Особистий щоденник подорожі: позначайте пам'ятки як відвідані на сторінці «Пам'ятки», "
               "а тут дивіться свою візуальну хронологію.")

    total = len(LANDMARKS)
    visited_count = len(st.session_state.visited)
    progress = visited_count / total if total else 0

    c1, c2 = st.columns([3, 1])
    with c1:
        st.progress(progress, text=f"Відвідано {visited_count} з {total} пам'яток ({int(progress * 100)}%)")
    with c2:
        st.metric("🏅 Прогрес", f"{int(progress * 100)}%")

    if visited_count == 0:
        st.info(
            "Ви ще не позначили жодної пам'ятки як відвідану. Перейдіть на сторінку «🗺️ Пам'ятки» "
            "та натисніть «✅ Позначити як відвідано» під потрібною карткою."
        )
        return

    section_divider("📔")
    st.subheader("🕰️ Хронологія відвідувань")

    entries = get_visited_sorted()
    html_parts = ["<div class='timeline'>"]
    for e in entries:
        item = e["item"]
        cat_icon = CATEGORY_ICONS.get(item["category"], "📍")
        note_html = f"<p style='margin-top:6px;'>💭 {e['note']}</p>" if e["note"] else ""
        html_parts.append(
            "<div class='timeline-item'>"
            "<div class='timeline-dot'></div>"
            "<div class='timeline-card'>"
            f"<div class='timeline-date'>📅 {e['date']}</div>"
            f"<div style='font-size:1.05rem;margin-top:2px;'>{cat_icon} <strong>{item['name']}</strong></div>"
            f"<div style='color:#555;font-size:0.85rem;'>{item['category']} · 📍 {item['address']}</div>"
            f"{note_html}"
            "</div>"
            "</div>"
        )
    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)

    section_divider("📝")
    st.subheader("✍️ Додати нотатку до відвідування")
    visited_names = list(st.session_state.visited.keys())
    chosen = st.selectbox("Оберіть відвідану пам'ятку", visited_names)
    current_note = st.session_state.visited.get(chosen, {}).get("note", "")
    new_note = st.text_area("Ваші враження про це місце", value=current_note, key=f"note_{chosen}")
    if st.button("💾 Зберегти нотатку"):
        st.session_state.visited[chosen]["note"] = new_note
        st.success("Нотатку збережено!")
        st.rerun()

    section_divider("🎯")
    st.subheader("🎯 Ще не відвідано")
    not_visited = [i for i in LANDMARKS if i["name"] not in st.session_state.visited]
    if not_visited:
        cols = st.columns(3)
        for idx, item in enumerate(not_visited):
            cat_icon = CATEGORY_ICONS.get(item["category"], "📍")
            with cols[idx % 3]:
                st.markdown(f"{cat_icon} {item['name']}")
    else:
        st.success("🎉 Вітаємо! Ви відвідали всі пам'ятки зі списку!")


def page_transport_live():
    st.header("🚌 Транспорт онлайн")
    st.info(
        "ℹ️ Офіційна система GPS-моніторингу громадського транспорту Вінниці належить "
        "КП «Вінницякартсервіс» і не надає відкритого публічного API для сторонніх застосунків. "
        "Нижче — наочна **демо-симуляція** руху транспорту для ілюстрації того, як виглядатиме "
        "ця функція після підключення офіційного API. Для реального відстеження скористайтесь "
        "офіційними джерелами нижче."
    )

    with st.expander("🔗 Офіційні джерела реального руху транспорту"):
        for link in OFFICIAL_TRANSPORT_LINKS:
            st.markdown(f"- [{link['name']}]({link['url']})")

    section_divider("🚌")
    st.subheader("🗺️ Демо-карта руху транспорту")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("🔄 Оновити позиції", use_container_width=True):
            simulate_transport_tick()
            st.rerun()
        auto = st.checkbox("Демо-автооновлення", value=False)

    positions = st.session_state.transport_positions or simulate_transport_tick()

    if HAS_PANDAS:
        map_df = pd.DataFrame([{"lat": p["lat"], "lon": p["lon"]} for p in positions])
        with c2:
            st.map(map_df)
    else:
        with c2:
            st.warning("Встановіть `pandas` (`pip install pandas`), щоб побачити карту: `pip install -r requirements.txt`.")

    st.caption(f"🔁 Оновлень демо-руху: {st.session_state.transport_tick}")

    section_divider("🚏")
    st.subheader("📋 Умовний список бортів поруч")
    for p in positions:
        st.markdown(
            f"<div class='transport-card'>{p['type']} <strong>{p['line']}</strong> · "
            f"координати: {p['lat']:.4f}, {p['lon']:.4f} · "
            f"<span style='color:#2e7d32;'>демо-дані</span></div>",
            unsafe_allow_html=True,
        )

    if auto:
        import time as _time
        _time.sleep(2)
        simulate_transport_tick()
        st.rerun()


def page_favorites():
    st.header("❤️ Обране")

    if not st.session_state.fav_landmarks and not st.session_state.fav_restaurants:
        st.info("Ви ще нічого не додали в обране. Натисніть ❤️ на сторінках «Пам'ятки» або «Ресторани».")
        return

    if st.session_state.fav_landmarks:
        st.subheader("🗺️ Пам'ятки")
        name_to_item = {i["name"]: i for i in LANDMARKS}
        for name in st.session_state.fav_landmarks:
            item = name_to_item[name]
            st.markdown(f"**{item['name']}** — {item['category']} · 📍 {item['address']}")

    if st.session_state.fav_restaurants:
        st.subheader("🍽️ Ресторани")
        name_to_r = {r["name"]: r for r in RESTAURANTS}
        for name in st.session_state.fav_restaurants:
            r = name_to_r[name]
            st.markdown(f"**{r['name']}** — {r['type']} · ⭐{r['rating']}")


def page_about():
    st.header("ℹ️ Про місто")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🚌 Транспорт", "🏆 Досягнення", "🏨 Проживання", "🎓 Освіта", "🌦️ Клімат"]
    )
    with tab1:
        st.markdown(TRANSPORT_INFO)
    with tab2:
        st.markdown(ACHIEVEMENTS)
    with tab3:
        for h in HOTELS:
            st.markdown(f"**{h['name']}** — {'⭐' * h['stars']} · {h['price_night']}/ніч · 📍 {h['address']}")
    with tab4:
        st.markdown(EDUCATION_INFO)
    with tab5:
        st.markdown(CLIMATE_INFO)


def page_feedback():
    st.header("📝 Зворотний зв'язок")
    st.write("Поділіться враженнями від платформи або запропонуйте нову пам'ятку чи подію.")
    with st.form("feedback_form", clear_on_submit=True):
        name = st.text_input("Ваше ім'я (необов'язково)")
        rating = st.slider("Оцінка платформи", 1, 5, 5)
        message = st.text_area("Повідомлення")
        submitted = st.form_submit_button("Надіслати")
        if submitted:
            if message.strip():
                st.session_state.feedback_log.append(
                    {"name": name or "Анонім", "rating": rating, "message": message}
                )
                st.success("Дякуємо за відгук! 🙌")
            else:
                st.warning("Будь ласка, напишіть повідомлення перед відправкою.")

    if st.session_state.feedback_log:
        section_divider("🌿")
        st.subheader("Останні відгуки")
        for fb in reversed(st.session_state.feedback_log[-5:]):
            st.markdown(f"**{fb['name']}** — {'⭐' * fb['rating']}")
            st.caption(fb["message"])


def page_chatbot():
    st.header("🤖 Чат-бот — віртуальний гід по Вінниці")
    st.caption(
        "Запитайте про пам'ятки, ресторани, готелі, події, транспорт, погоду, освіту чи маршрут по місту. "
        "Бот розуміє запити навіть з друкарськими помилками та пам'ятає контекст розмови 🧠"
    )

    ctx = st.session_state.chat_context
    if ctx.get("last_landmark") or ctx.get("last_topic"):
        remembered = ctx.get("last_landmark") or ctx.get("last_topic")
        cc1, cc2 = st.columns([4, 1])
        cc1.info(f"🧠 Пам'ятаю, що ми говорили про: **{remembered}** — можете уточнювати (ціна, графік, адреса тощо).")
        if cc2.button("🔄 Забути", use_container_width=True):
            st.session_state.chat_context = {"last_topic": None, "last_landmark": None}
            st.rerun()

    st.write("**Швидкі запитання:**")
    cols = st.columns(3)
    for i, q in enumerate(QUICK_QUESTIONS):
        if cols[i % 3].button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "assistant", "content": get_bot_response(q)})

    section_divider("🌿")

    for msg in st.session_state.chat_history:
        avatar = "🤖" if msg["role"] == "assistant" else "🙂"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    user_input = st.chat_input("Напишіть повідомлення...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response = get_bot_response(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    if st.button("🗑️ Очистити чат"):
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Чат очищено. Чим можу допомогти?"}
        ]
        st.session_state.chat_context = {"last_topic": None, "last_landmark": None}
        st.rerun()


def page_export_import():
    st.header("💾 Експорт та Імпорт даних")
    st.write(
        "Тут можна зберегти свої дані платформи (обране, відгуки, маршрут) у файл, "
        "а також завантажити довідкові каталоги пам'яток/подій/ресторанів у форматі CSV."
    )

    st.subheader("⬇️ Експорт особистих даних")
    st.caption("Обране, залишені відгуки, історія відгуків платформи та останній побудований маршрут.")
    snapshot_json = export_snapshot()
    st.download_button(
        "Завантажити мої дані (JSON)",
        data=snapshot_json,
        file_name="vinnytsia_hub_backup.json",
        mime="application/json",
    )
    with st.expander("Переглянути вміст файлу перед завантаженням"):
        st.code(snapshot_json, language="json")

    section_divider("🌿")
    st.subheader("⬆️ Імпорт особистих даних")
    st.caption("Завантажте раніше збережений JSON-файл, щоб відновити обране, відгуки та маршрут.")
    uploaded = st.file_uploader("Оберіть файл резервної копії (.json)", type=["json"])
    if uploaded is not None:
        if st.button("📥 Імпортувати дані", type="primary"):
            try:
                raw_text = uploaded.read().decode("utf-8")
                import_snapshot(raw_text)
                st.success("Дані успішно імпортовано! Перевірте розділи «Обране» та «Маршрут».")
                st.rerun()
            except Exception as e:
                st.error(f"Не вдалося імпортувати файл: {e}")

    section_divider("🌿")
    st.subheader("📂 Експорт довідкових каталогів (CSV)")
    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "🗺️ Пам'ятки (CSV)", data=landmarks_to_csv(),
        file_name="vinnytsia_landmarks.csv", mime="text/csv",
    )
    c2.download_button(
        "🎉 Події (CSV)", data=events_to_csv(),
        file_name="vinnytsia_events.csv", mime="text/csv",
    )
    c3.download_button(
        "🍽️ Ресторани (CSV)", data=restaurants_to_csv(),
        file_name="vinnytsia_restaurants.csv", mime="text/csv",
    )

    section_divider("🌿")
    st.subheader("📄 PDF-гід із вибраними пам'ятками")
    st.caption(
        "Згенеруйте гарно оформлений PDF-путівник — зручно роздрукувати перед прогулянкою "
        "або зберегти на телефоні для офлайн-перегляду."
    )

    if not HAS_REPORTLAB:
        st.warning(
            "Для генерації PDF потрібна бібліотека `reportlab`. Встановіть її: "
            "`pip install reportlab` (вже додано в requirements.txt)."
        )
    else:
        default_selection = sorted(st.session_state.fav_landmarks) or [i["name"] for i in LANDMARKS[:5]]
        pdf_names = st.multiselect(
            "Пам'ятки для включення в PDF",
            [i["name"] for i in LANDMARKS],
            default=default_selection,
            key="pdf_landmark_select",
        )
        include_route_in_pdf = st.checkbox(
            "Додати час відвідування з останнього побудованого маршруту (сторінка «Маршрут»)",
            value=bool(st.session_state.last_route),
        )

        if st.button("📄 Згенерувати PDF-гід", type="primary"):
            if not pdf_names:
                st.warning("Оберіть хоча б одну пам'ятку для PDF-гіда.")
            else:
                schedule = None
                if include_route_in_pdf and st.session_state.last_route:
                    schedule = {
                        stop["name"]: f"{stop['start']}–{stop['end']}"
                        for stop in st.session_state.last_route
                    }
                pdf_bytes, warning = generate_pdf_guide(pdf_names, schedule=schedule)
                if pdf_bytes is None:
                    st.error("Не вдалося згенерувати PDF: бібліотека reportlab недоступна.")
                else:
                    if warning == "no-cyrillic-font":
                        st.info(
                            "ℹ️ На цьому комп'ютері не знайдено шрифт із кирилицею, тому текст у PDF "
                            "транслітеровано латиницею, щоб уникнути «квадратиків» замість літер."
                        )
                    st.success("PDF-гід готовий! 🎉")
                    st.download_button(
                        "⬇️ Завантажити PDF-гід",
                        data=pdf_bytes,
                        file_name="vinnytsia_guide.pdf",
                        mime="application/pdf",
                    )

    section_divider("🌿")
    st.subheader("🧭 Експорт маршруту")
    if st.session_state.last_route:
        finish = st.session_state.last_route[-1]["end"] if st.session_state.last_route else ""
        st.download_button(
            "Завантажити останній маршрут (.txt)",
            data=route_to_text(st.session_state.last_route, finish),
            file_name="vinnytsia_marshrut.txt",
            mime="text/plain",
        )
    else:
        st.info("Ще немає складеного маршруту. Перейдіть на сторінку «Маршрут», щоб створити його.")


# =========================================================
#                       ГОЛОВНА ЛОГІКА / НАВІГАЦІЯ
# =========================================================

def main():
    init_state()
    render_header()

    pages = {
        "Головна": page_home,
        "Пам'ятки": page_landmarks,
        "Події": page_events,
        "Ресторани": page_restaurants,
        "Маршрут": page_route,
        "Мої плани": page_my_plans,
        "Транспорт онлайн": page_transport_live,
        "Обране": page_favorites,
        "Чат-бот": page_chatbot,
        "Про місто": page_about,
        "Зворотний зв'язок": page_feedback,
        "Експорт/Імпорт": page_export_import,
    }

    with st.sidebar:
        st.markdown("## 🏙️ Моя Вінниця 🌻")
        st.radio(
            "Навігація",
            list(pages.keys()),
            key="page",
            format_func=lambda p: f"{PAGE_ICONS.get(p, '📌')}  {p}",
        )
        section_divider("🌿")
        n_fav = len(st.session_state.fav_landmarks) + len(st.session_state.fav_restaurants)
        st.caption(f"❤️ В обраному: {n_fav}")
        st.caption(f"🚀 Версія платформи: {APP_VERSION}")
        st.caption("🌆 Демо-платформа про м. Вінниця, зроблена на Streamlit.")

    pages[st.session_state.page]()


if __name__ == "__main__":
    main()
