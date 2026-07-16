# -*- coding: utf-8 -*-
"""
Платформа "Моя Вінниця" — інформаційний портал про місто Вінниця
з чат-ботом-гідом, маршрутизатором, обраним та live-погодою на Streamlit.

Запуск:
    pip install streamlit requests
    streamlit run vinnytsia_app.py
"""

import streamlit as st
import re
from datetime import date

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
]

# Кожна пам'ятка має орієнтовний час відвідування (у хвилинах) — потрібно для маршрутизатора
LANDMARKS = [
    {
        "name": "Фонтан Roshen",
        "category": "Розваги",
        "desc": "Найбільший плавучий світломузичний фонтан у Європі, розташований на річці Південний Буг. "
                "Шоу відбувається у теплу пору року у вечірній час, поєднуючи воду, світло та музику.",
        "address": "Набережна, біля Кемпа",
        "tags": ["фонтан", "roshen", "рошен", "шоу", "музика", "набережна"],
        "duration": 45,
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
        "img": "https://source.unsplash.com/400x260/?old,wall,fortress",
    },
    {
        "name": "Водонапірна вежа",
        "category": "Архітектура",
        "desc": "Символ Вінниці, споруджена у 1912 році. Нині в приміщенні вежі працює виставковий простір.",
        "address": "вул. Соборна",
        "tags": ["вежа", "водонапірна", "архітектура", "соборна"],
        "duration": 30,
        "img": "https://source.unsplash.com/400x260/?water,tower",
    },
    {
        "name": "Спасо-Преображенський кафедральний собор",
        "category": "Церква",
        "desc": "Головний православний храм міста, кафедральний собор з багатою історією та красивим інтер'єром.",
        "address": "вул. Соборна, 23",
        "tags": ["церква", "собор", "храм", "релігія"],
        "duration": 25,
        "img": "https://source.unsplash.com/400x260/?cathedral,orthodox",
    },
    {
        "name": "Костел Пресвятої Діви Марії Ангельської",
        "category": "Церква",
        "desc": "Один з найстаріших католицьких храмів Вінниці, зразок бароккової архітектури.",
        "address": "Старе місто",
        "tags": ["костел", "церква", "храм", "барокко"],
        "duration": 25,
        "img": "https://source.unsplash.com/400x260/?church,baroque",
    },
    {
        "name": "Парк Дружби народів (Центральний парк)",
        "category": "Парк",
        "desc": "Найпопулярніший парк міста для прогулянок, відпочинку та сімейного дозвілля, з алеями та атракціонами.",
        "address": "вул. Хмельницьке шосе",
        "tags": ["парк", "прогулянка", "відпочинок", "діти", "дружби народів"],
        "duration": 50,
        "img": "https://source.unsplash.com/400x260/?park,alley",
    },
    {
        "name": "Театральна площа",
        "category": "Центр",
        "desc": "Центральна площа міста з музичним драматичним театром ім. Садовського, місце проведення подій.",
        "address": "Театральна площа",
        "tags": ["площа", "театр", "центр", "події"],
        "duration": 20,
        "img": "https://source.unsplash.com/400x260/?theatre,square",
    },
    {
        "name": "Музей історії міста Вінниці",
        "category": "Музей",
        "desc": "Експозиції з історії Вінниці від найдавніших часів до сьогодення.",
        "address": "вул. Соборна",
        "tags": ["музей", "історія", "експозиція"],
        "duration": 50,
        "img": "https://source.unsplash.com/400x260/?history,museum",
    },
    {
        "name": "Синагога «Бейт Кнесет»",
        "category": "Релігія",
        "desc": "Діюча синагога, що є свідченням багатої єврейської історії міста.",
        "address": "центр міста",
        "tags": ["синагога", "релігія", "історія", "євреї"],
        "duration": 20,
        "img": "https://source.unsplash.com/400x260/?synagogue",
    },
]

EVENTS = [
    {
        "name": "VinnytsiaJazzFest",
        "date": "Червень",
        "month": 6,
        "desc": "Міжнародний джазовий фестиваль просто неба за участю українських та закордонних музикантів.",
        "place": "Центральний парк / набережна",
    },
    {
        "name": "Vinnytsia Food Fest",
        "date": "Липень–Серпень",
        "month": 7,
        "desc": "Фестиваль вуличної їжі з десятками локальних закладів і фудтраків.",
        "place": "Театральна площа",
    },
    {
        "name": "«Острів Європи»",
        "date": "Вересень",
        "month": 9,
        "desc": "Мультикультурний фестиваль, присвячений європейським традиціям, музиці та кухні різних країн.",
        "place": "Набережна / Кемпа",
    },
    {
        "name": "День міста Вінниці",
        "date": "Вересень",
        "month": 9,
        "desc": "Головне міське свято з концертами, ярмарками та феєрверком.",
        "place": "Центр міста",
    },
    {
        "name": "Різдвяний ярмарок",
        "date": "Грудень",
        "month": 12,
        "desc": "Новорічно-різдвяний ярмарок з ковзанкою, гарячими напоями та сувенірами.",
        "place": "Театральна площа",
    },
]

RESTAURANTS = [
    {"name": "Кафе «Вишня»", "type": "Українська кухня", "rating": 4.7, "price": "$$"},
    {"name": "Пивна ресторація «Козак Мамай»", "type": "Українська / пиво", "rating": 4.5, "price": "$$"},
    {"name": "PizzaMasters", "type": "Італійська", "rating": 4.4, "price": "$"},
    {"name": "Sushi-Ya", "type": "Японська", "rating": 4.6, "price": "$$"},
    {"name": "Кав'ярня «Львівська майстерня шоколаду»", "type": "Кав'ярня", "rating": 4.8, "price": "$"},
    {"name": "Steak House Bull", "type": "Стейки", "rating": 4.6, "price": "$$$"},
]

HOTELS = [
    {"name": "Готель «南Buk»", "stars": 4, "price_night": "1400 грн"},
    {"name": "Hotel Vinnytsia", "stars": 3, "price_night": "900 грн"},
    {"name": "Апарт-готель «Кемпа Residence»", "stars": 4, "price_night": "1600 грн"},
    {"name": "Хостел «Дружба»", "stars": 2, "price_night": "400 грн"},
]

TRANSPORT_INFO = """
**Як дістатися до Вінниці:**
- 🚄 Поїздом — прямі рейси з Києва (~3 год), Львова, Одеси, Хмельницького.
- 🚌 Автобусом — регулярні рейси з більшості обласних центрів України.
- 🚗 Автомобілем — траса М12 (Стрий–Знам'янка) проходить через місто.
- ✈️ Найближчий аеропорт — Вінницький міжнародний аеропорт "Гавришівка".

**Міський транспорт:**
- 🚋 Тролейбуси та автобуси — основний вид громадського транспорту.
- 🚲 Розвинена мережа велодоріжок, можна орендувати велосипед.
- 🚕 Таксі та каршерінг доступні через мобільні застосунки.
"""

ACHIEVEMENTS = """
- 🏆 Неодноразово визнавалась одним із найкращих міст України для життя.
- 💧 Фонтан Roshen — найбільший плавучий фонтан у Європі.
- 🌳 Високий рівень озеленення та комфортна міська інфраструктура.
- 🏥 Потужна медична школа, започаткована М. Пироговим.
"""

# =========================================================
#                       ЧАТ-БОТ (RULE-BASED)
# =========================================================

KNOWLEDGE_BASE = {
    "фонтан": {
        "keywords": ["фонтан", "roshen", "рошен", "шоу фонтану"],
        "answer": "💦 **Фонтан Roshen** — найбільший плавучий світломузичний фонтан у Європі, "
                  "розташований на річці Південний Буг біля Кемпи. Шоу відбувається у теплу пору "
                  "року у вечірній час — вода, світло та музика зливаються в яскраве видовище.",
    },
    "пирогов": {
        "keywords": ["пирогов", "музей пирогова", "вишня", "хірург"],
        "answer": "🏥 **Музей-садиба М.І. Пирогова «Вишня»** — місце, де жив і працював видатний хірург. "
                  "У церкві-некрополі на території садиби зберігається забальзамоване тіло вченого. "
                  "Адреса: вул. Пирогова, 155.",
    },
    "вежа": {
        "keywords": ["вежа", "водонапірна", "водонапирна"],
        "answer": "🗼 **Водонапірна вежа** — символ Вінниці, побудована у 1912 році. "
                  "Сьогодні в її приміщенні працює виставковий простір. Адреса: вул. Соборна.",
    },
    "мури": {
        "keywords": ["мури", "фортеця", "єзуїт"],
        "answer": "🏰 **Вінницькі мури** — залишки укріплень єзуїтського монастиря XVII століття, "
                  "одна з найстаріших пам'яток міста в історичному центрі.",
    },
    "церква": {
        "keywords": ["церква", "собор", "костел", "храм", "релігія", "синагога"],
        "answer": "⛪ У Вінниці варто відвідати: **Спасо-Преображенський кафедральний собор**, "
                  "**Костел Пресвятої Діви Марії Ангельської** та діючу **синагогу «Бейт Кнесет»** — "
                  "всі вони мають багату історію та цікаву архітектуру.",
    },
    "парк": {
        "keywords": ["парк", "прогулянка", "відпочинок", "дружби народів"],
        "answer": "🌳 Найпопулярніший — **Парк Дружби народів (Центральний парк)** на Хмельницькому шосе: "
                  "алеї, атракціони та місця для сімейного відпочинку.",
    },
    "ресторан": {
        "keywords": ["ресторан", "їжа", "поїсти", "кафе", "де поїсти", "кухня"],
        "answer": "🍽️ Рекомендую переглянути розділ **«Ресторани»** — там є підбірка закладів з рейтингами: "
                  "від української кухні до суші та стейків.",
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
                  "(липень–серпень) та фестиваль **«Острів Європи»** (вересень). Деталі — на сторінці «Події».",
    },
    "погода": {
        "keywords": ["погода", "температура", "прогноз"],
        "answer": "🌤️ Актуальну погоду у Вінниці можна побачити на **Головній сторінці** — там підключений "
                  "живий прогноз.",
    },
    "маршрут": {
        "keywords": ["маршрут", "план", "екскурсія", "куди піти", "що відвідати за день"],
        "answer": "🗺️ Скористайтеся сторінкою **«Маршрут»** — оберіть пам'ятки, і я складу для вас "
                  "оптимальний порядок відвідування з орієнтовним часом.",
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
                "події, готелі, погоду чи маршрут — і я підкажу!")

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
            "історію, події чи маршрут по місту.")


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


def build_route(selected_names, start_time_str):
    """Простий генератор маршруту: зберігає порядок вибору, рахує час відвідування + 15 хв на переїзд."""
    from datetime import datetime, timedelta
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
    c1, c2, c3, c4, c5 = st.columns(5)
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
    selected_cat = st.selectbox("Категорія", categories)

    filtered = LANDMARKS
    if selected_cat != "Усі":
        filtered = [i for i in filtered if i["category"] == selected_cat]
    if search:
        s = search.lower()
        filtered = [
            i for i in filtered
            if s in i["name"].lower() or s in i["desc"].lower() or any(s in t for t in i["tags"])
        ]

    st.write(f"Знайдено: **{len(filtered)}** з {len(LANDMARKS)}")

    cols = st.columns(2)
    for idx, item in enumerate(filtered):
        with cols[idx % 2]:
            with st.container(border=True):
                st.image(item["img"], use_container_width=True)
                st.subheader(item["name"])
                st.caption(f"{item['category']} · ⏱ ~{item['duration']} хв · 📍 {item['address']}")
                st.write(item["desc"])
                is_fav = item["name"] in st.session_state.fav_landmarks
                label = "💔 Прибрати з обраного" if is_fav else "❤️ Додати в обране"
                if st.button(label, key=f"fav_{item['name']}"):
                    if is_fav:
                        st.session_state.fav_landmarks.discard(item["name"])
                    else:
                        st.session_state.fav_landmarks.add(item["name"])
                    st.rerun()


def page_events():
    st.header("🎉 Події та фестивалі")
    today = date.today()
    st.caption(f"Сьогодні: {today.strftime('%d.%m.%Y')}")

    month_filter = st.selectbox(
        "Фільтр за місяцем",
        ["Усі"] + [f"{m:02d}" for m in range(1, 13)],
    )

    events_to_show = EVENTS
    if month_filter != "Усі":
        events_to_show = [e for e in EVENTS if e["month"] == int(month_filter)]

    if not events_to_show:
        st.info("У цьому місяці запланованих подій немає.")

    for ev in events_to_show:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(ev["name"])
                st.write(ev["desc"])
                st.caption(f"📍 {ev['place']}")
            with c2:
                st.metric("Період", ev["date"])


def page_restaurants():
    st.header("🍽️ Ресторани Вінниці")
    c1, c2 = st.columns(2)
    sort_option = c1.radio("Сортувати за:", ["Рейтингом", "Назвою"], horizontal=True)
    price_filter = c2.selectbox("Цінова категорія", ["Усі", "$", "$$", "$$$"])

    data = RESTAURANTS.copy()
    if price_filter != "Усі":
        data = [r for r in data if r["price"] == price_filter]
    if sort_option == "Рейтингом":
        data.sort(key=lambda x: x["rating"], reverse=True)
    else:
        data.sort(key=lambda x: x["name"])

    for r in data:
        stars = "⭐" * int(round(r["rating"]))
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            c1.markdown(f"**{r['name']}**  \n_{r['type']}_")
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
            st.success(f"Маршрут складено! Орієнтовний час завершення: **{finish}**")
            for i, stop in enumerate(route, start=1):
                st.markdown(
                    f"**{i}. {stop['name']}** — {stop['start']}–{stop['end']} "
                    f"(⏱ {stop['duration']} хв) · 📍 {stop['address']}"
                )
                if i < len(route):
                    st.caption("🚶 ~15 хв на переїзд/перехід до наступної точки")


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
    tab1, tab2, tab3 = st.tabs(["🚌 Транспорт і як дістатись", "🏆 Досягнення", "🏨 Проживання"])
    with tab1:
        st.markdown(TRANSPORT_INFO)
    with tab2:
        st.markdown(ACHIEVEMENTS)
    with tab3:
        for h in HOTELS:
            st.markdown(f"**{h['name']}** — {'⭐' * h['stars']} · {h['price_night']}/ніч")


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
    st.caption("Запитайте про пам'ятки, ресторани, готелі, події, транспорт, погоду чи маршрут по місту.")

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
    }

    with st.sidebar:
        st.markdown("## 🏙️ Моя Вінниця")
        choice = st.radio("Навігація", list(pages.keys()), index=list(pages.keys()).index(st.session_state.page))
        st.session_state.page = choice
        st.markdown("---")
        n_fav = len(st.session_state.fav_landmarks) + len(st.session_state.fav_restaurants)
        st.caption(f"❤️ В обраному: {n_fav}")
        st.caption("Демо-платформа про м. Вінниця, зроблена на Streamlit.")

    pages[st.session_state.page]()


if __name__ == "__main__":
    main()
