# -*- coding: utf-8 -*-
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
from datetime import date, datetime, timedelta

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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
APP_VERSION = "1.2"

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
        "img": "https://source.unsplash.com/400x260/?fountain,night",
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
        "img": "https://source.unsplash.com/400x260/?museum,manor",
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
        "img": "https://source.unsplash.com/400x260/?old,wall,fortress",
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
        "img": "https://source.unsplash.com/400x260/?water,tower",
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
        "img": "https://source.unsplash.com/400x260/?cathedral,orthodox",
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
        "img": "https://source.unsplash.com/400x260/?church,baroque",
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
        "img": "https://source.unsplash.com/400x260/?park,alley",
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
        "img": "https://source.unsplash.com/400x260/?theatre,square",
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
        "img": "https://source.unsplash.com/400x260/?history,museum",
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
        "img": "https://source.unsplash.com/400x260/?synagogue",
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
        "img": "https://source.unsplash.com/400x260/?pharmacy,old",
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
        "img": "https://source.unsplash.com/400x260/?monument,statue",
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
        "img": "https://source.unsplash.com/400x260/?pedestrian,street,europe",
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
        "img": "https://source.unsplash.com/400x260/?river,island,park",
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
        "img": "https://source.unsplash.com/400x260/?botanical,garden",
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
        "keywords": ["парк", "прогулянка", "відпочинок", "дружби народів", "кемпа", "ботанічний"],
        "answer": "🌳 Для прогулянок радимо: **Парк Дружби народів** (алеї, атракціони), "
                  "острів **Кемпа** (краєвиди на річку) та **Ботанічний сад «Поділля»** (тиша й природа).",
    },
    "ресторан": {
        "keywords": ["ресторан", "їжа", "поїсти", "кафе", "де поїсти", "кухня", "веган"],
        "answer": "🍽️ Рекомендую переглянути розділ **«Ресторани»** — там є підбірка закладів з рейтингами, "
                  "адресами й контактами: від української кухні до суші, стейків і веганських страв.",
    },
    "готель": {
        "keywords": ["готель", "хостел", "де зупинитись", "проживання", "ночівля"],
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


def get_bot_response(user_text: str) -> str:
    """Проста rule-based логіка чат-бота на основі ключових слів."""
    text = user_text.lower().strip()
    text_clean = re.sub(r"[^\w\sа-яіїєґ]", "", text)

    if any(g in text_clean for g in GREETINGS):
        return ("Вітаю! 👋 Я віртуальний гід по Вінниці. Запитайте мене про пам'ятки, ресторани, "
                "події, готелі, погоду, освіту чи маршрут — і я підкажу!")

    if any(t in text_clean for t in THANKS):
        return "Будь ласка! 😊 Якщо ще щось цікавить — питайте."

    best_match = None
    best_score = 0
    for topic, data in KNOWLEDGE_BASE.items():
        score = sum(1 for kw in data["keywords"] if kw in text_clean)
        if score > best_score:
            best_score = score
            best_match = data["answer"]

    if best_match:
        return best_match

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


def export_snapshot():
    """Формує JSON-знімок усіх даних користувача для експорту."""
    snapshot = {
        "app_version": APP_VERSION,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "fav_landmarks": sorted(st.session_state.fav_landmarks),
        "fav_restaurants": sorted(st.session_state.fav_restaurants),
        "reviews": st.session_state.reviews,
        "feedback_log": st.session_state.feedback_log,
        "last_route": st.session_state.last_route,
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
            margin-bottom: 1.5rem;
        }
        .hero h1 { font-size: 2.6rem; margin-bottom: 0.3rem; }
        .hero p { font-size: 1.1rem; opacity: 0.95; }
        .stat-box {
            background: #f1f8e9;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 1px solid #c5e1a5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_home():
    st.markdown(
        """
        <div class="hero">
            <h1>🏙️ Моя Вінниця</h1>
            <p>Відкрийте для себе пам'ятки, події та смаки одного з найкрасивіших міст України</p>
        </div>
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
            st.markdown(
                f"<div class='stat-box'><h3>{value}</h3><p>{label}</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("⚡ Швидкий доступ")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    if c1.button("🗺️ Пам'ятки", use_container_width=True):
        st.session_state.page = "Пам'ятки"; st.rerun()
    if c2.button("🎉 Події", use_container_width=True):
        st.session_state.page = "Події"; st.rerun()
    if c3.button("🍽️ Ресторани", use_container_width=True):
        st.session_state.page = "Ресторани"; st.rerun()
    if c4.button("🧭 Маршрут", use_container_width=True):
        st.session_state.page = "Маршрут"; st.rerun()
    if c5.button("🤖 Чат-бот", use_container_width=True):
        st.session_state.page = "Чат-бот"; st.rerun()
    if c6.button("💾 Експорт/Імпорт", use_container_width=True):
        st.session_state.page = "Експорт/Імпорт"; st.rerun()

    st.markdown("---")
    st.subheader("💡 Цікаві факти")
    for fact in FACTS:
        st.markdown(f"- {fact}")

    st.markdown("---")
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
                st.markdown("**Пам'ятки:**")
                for i in found_landmarks:
                    st.write(f"📍 {i['name']} — {i['category']}")
            if found_events:
                st.markdown("**Події:**")
                for e in found_events:
                    st.write(f"🎉 {e['name']} — {e['date']}")
            if found_rest:
                st.markdown("**Ресторани:**")
                for r in found_rest:
                    st.write(f"🍽️ {r['name']} — {r['type']}, ⭐{r['rating']}")


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
                st.subheader(item["name"])
                avg, n_reviews = average_rating(item["name"], item["base_rating"])
                st.caption(
                    f"{item['category']} · ⭐ {avg} ({n_reviews} відгуків) · ⏱ ~{item['duration']} хв\n\n"
                    f"🕒 {item['hours']} · 💵 {item['price']} · 📍 {item['address']}"
                )
                st.write(item["desc"])

                is_fav = item["name"] in st.session_state.fav_landmarks
                label = "💔 Прибрати з обраного" if is_fav else "❤️ Додати в обране"
                if st.button(label, key=f"fav_{item['name']}"):
                    if is_fav:
                        st.session_state.fav_landmarks.discard(item["name"])
                    else:
                        st.session_state.fav_landmarks.add(item["name"])
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
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(f"{ev['name']}  ·  🏷️ {ev['type']}")
                st.write(ev["desc"])
                st.caption(f"📍 {ev['place']} · 💵 {ev['price']} · 📅 Тривалість: ~{ev['days']} дн.")
            with c2:
                st.metric("Період", ev["date"])


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
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(
                f"**{r['name']}**  \n_{r['type']}_  \n"
                f"📍 {r['address']} · 🕒 {r['hours']} · ☎ {r['phone']}"
            )
            c2.write(f"{stars} {r['rating']}")
            c3.write(f"Цінник: {r['price']}")
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
        st.markdown("---")
        st.subheader("Останні відгуки")
        for fb in reversed(st.session_state.feedback_log[-5:]):
            st.markdown(f"**{fb['name']}** — {'⭐' * fb['rating']}")
            st.caption(fb["message"])


def page_chatbot():
    st.header("🤖 Чат-бот — віртуальний гід по Вінниці")
    st.caption("Запитайте про пам'ятки, ресторани, готелі, події, транспорт, погоду, освіту чи маршрут по місту.")

    st.write("**Швидкі запитання:**")
    cols = st.columns(3)
    for i, q in enumerate(QUICK_QUESTIONS):
        if cols[i % 3].button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "assistant", "content": get_bot_response(q)})

    st.markdown("---")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
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

    st.markdown("---")
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

    st.markdown("---")
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

    st.markdown("---")
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
        "Обране": page_favorites,
        "Чат-бот": page_chatbot,
        "Про місто": page_about,
        "Зворотний зв'язок": page_feedback,
        "Експорт/Імпорт": page_export_import,
    }

    with st.sidebar:
        st.markdown("## 🏙️ Моя Вінниця")
        choice = st.radio("Навігація", list(pages.keys()), index=list(pages.keys()).index(st.session_state.page))
        st.session_state.page = choice
        st.markdown("---")
        n_fav = len(st.session_state.fav_landmarks) + len(st.session_state.fav_restaurants)
        st.caption(f"❤️ В обраному: {n_fav}")
        st.caption(f"Версія платформи: {APP_VERSION}")
        st.caption("Демо-платформа про м. Вінниця, зроблена на Streamlit.")

    pages[st.session_state.page]()


if __name__ == "__main__":
    main()
