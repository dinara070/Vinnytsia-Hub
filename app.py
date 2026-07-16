# -*- coding: utf-8 -*-
"""
Платформа "Моя Вінниця" — розширений інформаційний портал про місто Вінниця
з чат-ботом-гідом, інтерактивною картою, обраним та планувальником маршруту.

Запуск:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import re
from datetime import date, datetime

# =========================================================
#                       НАЛАШТУВАННЯ СТОРІНКИ
# =========================================================
st.set_page_config(
    page_title="Моя Вінниця",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    "Вінниця — один із лідерів України за рівнем розвитку велоінфраструктури.",
]

# Кожна пам'ятка має координати (lat/lon) для карти та орієнтовний час відвідування
LANDMARKS = [
    {
        "name": "Фонтан Roshen", "category": "Розваги",
        "desc": "Найбільший плавучий світломузичний фонтан у Європі на річці Південний Буг. "
                "Шоу відбувається у теплу пору року у вечірній час.",
        "address": "Набережна, біля Кемпи", "lat": 49.2327, "lon": 28.4707,
        "visit_min": 45,
        "tags": ["фонтан", "roshen", "рошен", "шоу", "музика", "набережна"],
    },
    {
        "name": "Музей-садиба М.І. Пирогова «Вишня»", "category": "Музей",
        "desc": "Меморіальний комплекс, де жив і працював видатний хірург Микола Пирогов. "
                "У церкві-некрополі зберігається забальзамоване тіло вченого.",
        "address": "вул. Пирогова, 155", "lat": 49.2160, "lon": 28.4084,
        "visit_min": 60,
        "tags": ["пирогов", "музей", "садиба", "вишня", "хірург"],
    },
    {
        "name": "Вінницькі мури (Мури)", "category": "Історія",
        "desc": "Залишки укріплень єзуїтського монастиря XVII століття в історичному центрі.",
        "address": "Старе місто, вул. Соборна", "lat": 49.2332, "lon": 28.4767,
        "visit_min": 30,
        "tags": ["мури", "фортеця", "історія", "центр", "єзуїти"],
    },
    {
        "name": "Водонапірна вежа", "category": "Архітектура",
        "desc": "Символ Вінниці, споруджена у 1912 році. Нині тут працює виставковий простір.",
        "address": "пл. Європейська", "lat": 49.2346, "lon": 28.4828,
        "visit_min": 30,
        "tags": ["вежа", "водонапірна", "архітектура", "європейська"],
    },
    {
        "name": "Спасо-Преображенський кафедральний собор", "category": "Церква",
        "desc": "Головний православний храм міста з багатою історією та красивим інтер'єром.",
        "address": "вул. Соборна, 23", "lat": 49.2332, "lon": 28.4754,
        "visit_min": 25,
        "tags": ["церква", "собор", "храм", "релігія"],
    },
    {
        "name": "Костел Пресвятої Діви Марії Ангельської", "category": "Церква",
        "desc": "Один з найстаріших католицьких храмів Вінниці, зразок бароккової архітектури.",
        "address": "вул. Соборна, 12", "lat": 49.2331, "lon": 28.4753,
        "visit_min": 25,
        "tags": ["костел", "церква", "храм", "барокко", "капуцини"],
    },
    {
        "name": "Парк Дружби народів (Центральний парк)", "category": "Парк",
        "desc": "Найпопулярніший парк міста для прогулянок, відпочинку та сімейного дозвілля.",
        "address": "вул. Хмельницьке шосе", "lat": 49.2280, "lon": 28.4560,
        "visit_min": 60,
        "tags": ["парк", "прогулянка", "відпочинок", "діти", "дружби народів"],
    },
    {
        "name": "Театральна площа", "category": "Центр",
        "desc": "Центральна площа міста з театром ім. Садовського, місце проведення подій.",
        "address": "Театральна площа", "lat": 49.2361, "lon": 28.4791,
        "visit_min": 20,
        "tags": ["площа", "театр", "центр", "події"],
    },
    {
        "name": "Музей історії міста Вінниці", "category": "Музей",
        "desc": "Експозиції з історії Вінниці від найдавніших часів до сьогодення.",
        "address": "вул. Соборна", "lat": 49.2350, "lon": 28.4795,
        "visit_min": 45,
        "tags": ["музей", "історія", "експозиція"],
    },
    {
        "name": "Синагога «Бейт Кнесет»", "category": "Релігія",
        "desc": "Діюча синагога, що є свідченням багатої єврейської історії міста.",
        "address": "центр міста", "lat": 49.2342, "lon": 28.4833,
        "visit_min": 20,
        "tags": ["синагога", "релігія", "історія", "євреї"],
    },
    {
        "name": "Пішохідний Кайдацький міст", "category": "Архітектура",
        "desc": "Один із символічних мостів через Південний Буг з гарним видом на набережну.",
        "address": "Набережна", "lat": 49.2325, "lon": 28.4700,
        "visit_min": 20,
        "tags": ["міст", "набережна", "прогулянка", "вид"],
    },
    {
        "name": "Кемпа (острів)", "category": "Парк",
        "desc": "Мальовничий острів на Південному Бузі, популярне місце для прогулянок та перегляду фонтану.",
        "address": "Острів Кемпа", "lat": 49.2330, "lon": 28.4670,
        "visit_min": 40,
        "tags": ["кемпа", "острів", "набережна", "прогулянка"],
    },
    {
        "name": "Літній театр", "category": "Центр",
        "desc": "Історична локація для концертів і культурних подій просто неба в центрі міста.",
        "address": "Центральний парк", "lat": 49.2286, "lon": 28.4570,
        "visit_min": 25,
        "tags": ["театр", "концерти", "події", "парк"],
    },
    {
        "name": "Вінницький обласний краєзнавчий музей", "category": "Музей",
        "desc": "Один із найстаріших музеїв області з колекціями з археології, природи та етнографії.",
        "address": "вул. Соборна, 19", "lat": 49.2334, "lon": 28.4767,
        "visit_min": 50,
        "tags": ["музей", "краєзнавчий", "археологія", "етнографія"],
    },
    {
        "name": "Парк Дружби народів: Алея закоханих", "category": "Парк",
        "desc": "Романтична алея в парку — популярне місце для прогулянок та фотосесій.",
        "address": "Парк Дружби народів", "lat": 49.2275, "lon": 28.4555,
        "visit_min": 20,
        "tags": ["алея", "парк", "прогулянка", "романтика"],
    },
]

EVENTS = [
    {"name": "VinnytsiaJazzFest", "date": "Червень",
     "desc": "Міжнародний джазовий фестиваль просто неба за участю українських та закордонних музикантів.",
     "place": "Центральний парк / набережна"},
    {"name": "Vinnytsia Food Fest", "date": "Липень–Серпень",
     "desc": "Фестиваль вуличної їжі з десятками локальних закладів і фудтраків.",
     "place": "Театральна площа"},
    {"name": "«Острів Європи»", "date": "Вересень",
     "desc": "Мультикультурний фестиваль, присвячений європейським традиціям, музиці та кухні різних країн.",
     "place": "Набережна / Кемпа"},
    {"name": "День міста Вінниці", "date": "Вересень",
     "desc": "Головне міське свято з концертами, ярмарками та феєрверком.",
     "place": "Центр міста"},
    {"name": "Різдвяний ярмарок", "date": "Грудень",
     "desc": "Новорічно-різдвяний ярмарок з ковзанкою, гарячими напоями та сувенірами.",
     "place": "Театральна площа"},
]

RESTAURANTS = [
    {"name": "Кафе «Вишня»", "type": "Українська кухня", "rating": 4.7, "price": "$$"},
    {"name": "Пивна ресторація «Козак Мамай»", "type": "Українська / пиво", "rating": 4.5, "price": "$$"},
    {"name": "PizzaMasters", "type": "Італійська", "rating": 4.4, "price": "$"},
    {"name": "Sushi-Ya", "type": "Японська", "rating": 4.6, "price": "$$"},
    {"name": "Кав'ярня «Львівська майстерня шоколаду»", "type": "Кав'ярня", "rating": 4.8, "price": "$"},
    {"name": "Steak House Bull", "type": "Стейки", "rating": 4.6, "price": "$$$"},
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
                  "Сьогодні в її приміщенні працює виставковий простір. Адреса: пл. Європейська.",
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
        "keywords": ["парк", "прогулянка", "відпочинок", "дружби народів", "кемпа"],
        "answer": "🌳 Найпопулярніший — **Парк Дружби народів (Центральний парк)** на Хмельницькому шосе, "
                  "а також острів **Кемпа** — чудове місце для прогулянок і перегляду фонтану Roshen.",
    },
    "ресторан": {
        "keywords": ["ресторан", "їжа", "поїсти", "кафе", "де поїсти", "кухня"],
        "answer": "🍽️ Рекомендую переглянути розділ **«Ресторани»** — там є підбірка закладів з рейтингами: "
                  "від української кухні до суші та стейків.",
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
    "карта": {
        "keywords": ["карта", "де знаходиться", "маршрут", "де на карті"],
        "answer": "🗺️ Усі пам'ятки відмічені на сторінці **«Карта»** — там можна побачити їх розташування "
                  "одразу, а на сторінці **«Маршрут»** — скласти власний план подорожі.",
    },
    "готель": {
        "keywords": ["готель", "де зупинитися", "проживання", "хостел", "апартаменти"],
        "answer": "🏨 У Вінниці є готелі різних категорій — від бюджетних хостелів у центрі до готелів "
                  "рівня 4* біля набережної. Рекомендується бронювати заздалегідь у сезон фестивалів.",
    },
    "погода": {
        "keywords": ["погода", "клімат", "температура", "яка погода"],
        "answer": "🌤️ Вінниця має помірно-континентальний клімат: тепле літо (+22...+28°C) та помірно "
                  "холодну зиму (-3...-7°C). Найкращий час для відвідування — з травня по вересень.",
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
    "Яка зараз погода?",
]


def _contains_phrase(text: str, phrases: list) -> bool:
    """Перевіряє наявність фрази як окремого слова/виразу (не всередині інших слів)."""
    return any(re.search(rf"(?<!\w){re.escape(p)}(?!\w)", text) for p in phrases)


def get_bot_response(user_text: str) -> str:
    """Проста rule-based логіка чат-бота на основі ключових слів."""
    text = user_text.lower().strip()
    # Роздільники замінюємо на пробіл, щоб слова не "склеювались" (було: "привіт,як" -> "привітяк")
    text_clean = re.sub(r"[^\w\s]", " ", text)
    text_clean = re.sub(r"\s+", " ", text_clean)

    # 1) Спочатку шукаємо змістовну відповідь — щоб на "Привіт, розкажи про фонтан"
    #    бот відповідав про фонтан, а не лише вітався
    best_match = None
    best_score = 0
    for data in KNOWLEDGE_BASE.values():
        score = sum(1 for kw in data["keywords"] if kw in text_clean)
        if score > best_score:
            best_score = score
            best_match = data["answer"]

    if best_match:
        return best_match

    # 2) Якщо змістовного збігу немає — обробляємо привітання та подяки
    if _contains_phrase(text_clean, GREETINGS):
        return ("Вітаю! 👋 Я віртуальний гід по Вінниці. Запитайте мене про пам'ятки, ресторани, "
                "події, транспорт чи погоду — і я підкажу!")

    if _contains_phrase(text_clean, THANKS):
        return "Будь ласка! 😊 Якщо ще щось цікавить — питайте."

    return ("🤔 Вибачте, я поки не знаю відповіді на це питання. Спробуйте запитати про фонтан Roshen, "
            "музей Пирогова, Вінницькі мури, церкви, парки, ресторани, транспорт, готелі, погоду, "
            "історію, карту або події міста.")


# =========================================================
#                       ДОПОМІЖНІ ФУНКЦІЇ (СТАН)
# =========================================================

def init_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "Головна"
    if "nav_radio" not in st.session_state:
        st.session_state.nav_radio = st.session_state.page
    if "favorites" not in st.session_state:
        st.session_state.favorites = set()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Вітаю! 👋 Я віртуальний гід по Вінниці. Чим можу допомогти?"}
        ]
    if "feedback_list" not in st.session_state:
        st.session_state.feedback_list = []


def toggle_favorite(name: str):
    if name in st.session_state.favorites:
        st.session_state.favorites.remove(name)
    else:
        st.session_state.favorites.add(name)


def landmark_by_name(name: str):
    for item in LANDMARKS:
        if item["name"] == name:
            return item
    return None


def _sync_nav_from_page():
    """Програмна зміна сторінки (кнопки швидкого доступу) → оновлюємо стан
    радіо-перемикача ДО його створення, інакше він перезапише сторінку назад."""
    if st.session_state.nav_radio != st.session_state.page:
        st.session_state.nav_radio = st.session_state.page


def _on_nav_change():
    """Користувач обрав сторінку в сайдбарі → оновлюємо поточну сторінку."""
    st.session_state.page = st.session_state.nav_radio


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
    # (колонка, підпис кнопки, цільова сторінка) — ціль вказана явно,
    # без крихкого розбирання рядка з емодзі
    quick_nav = [
        (c1, "🗺️ Пам'ятки", "Пам'ятки"), (c2, "🎉 Події", "Події"),
        (c3, "🍽️ Ресторани", "Ресторани"), (c4, "🤖 Чат-бот", "Чат-бот"),
        (c5, "🧭 Карта", "Карта"), (c6, "📝 Маршрут", "Маршрут"),
    ]
    for col, label, target_page in quick_nav:
        if col.button(label, use_container_width=True):
            st.session_state.page = target_page
            st.rerun()

    st.markdown("---")
    left, right = st.columns([2, 1])
    with left:
        st.subheader("💡 Цікаві факти")
        for fact in FACTS:
            st.markdown(f"- {fact}")
    with right:
        st.subheader("📈 Популярність пам'яток")
        st.caption("Умовна статистика відвідувань за 2025 рік (демо-дані)")
        demo_df = pd.DataFrame({
            "Пам'ятка": ["Фонтан Roshen", "Музей Пирогова", "Мури", "Парк Дружби", "Водонапірна вежа"],
            "Відвідувачі (тис.)": [420, 180, 95, 260, 70],
        }).set_index("Пам'ятка")
        st.bar_chart(demo_df)


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

    for item in filtered:
        is_fav = item["name"] in st.session_state.favorites
        with st.expander(f"{'⭐' if is_fav else '📍'} {item['name']}  —  _{item['category']}_"):
            st.write(item["desc"])
            st.caption(f"Адреса: {item['address']} · Орієнтовний час відвідування: {item['visit_min']} хв")
            fav_label = "💔 Прибрати з обраного" if is_fav else "❤️ Додати в обране"
            if st.button(fav_label, key=f"fav_{item['name']}"):
                toggle_favorite(item["name"])
                st.rerun()


def page_map():
    st.header("🧭 Інтерактивна карта пам'яток")
    st.caption("Позначки показують розташування основних пам'яток Вінниці")

    categories = ["Усі"] + sorted(set(item["category"] for item in LANDMARKS))
    selected_cat = st.selectbox("Фільтр за категорією", categories, key="map_cat")

    filtered = LANDMARKS if selected_cat == "Усі" else [i for i in LANDMARKS if i["category"] == selected_cat]

    if filtered:
        map_df = pd.DataFrame({
            "lat": [i["lat"] for i in filtered],
            "lon": [i["lon"] for i in filtered],
        })
        st.map(map_df, zoom=13)
    else:
        st.info("Немає пам'яток у цій категорії.")

    st.markdown("---")
    st.subheader("Список позначок на карті")
    for item in filtered:
        st.markdown(f"- **{item['name']}** ({item['category']}) — {item['address']}")


def page_events():
    st.header("🎉 Події та фестивалі")
    today = date.today()
    st.caption(f"Сьогодні: {today.strftime('%d.%m.%Y')}")

    for ev in EVENTS:
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
    sort_option = st.radio("Сортувати за:", ["Рейтингом", "Назвою"], horizontal=True)

    data = RESTAURANTS.copy()
    if sort_option == "Рейтингом":
        data.sort(key=lambda x: x["rating"], reverse=True)
    else:
        data.sort(key=lambda x: x["name"])

    for r in data:
        stars = "⭐" * int(round(r["rating"]))
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.markdown(f"**{r['name']}**  \n_{r['type']}_")
            c2.write(f"{stars} {r['rating']}")
            c3.write(f"Цінник: {r['price']}")


def page_favorites():
    st.header("⭐ Обране")
    if not st.session_state.favorites:
        st.info("Ви ще не додали жодної пам'ятки в обране. Перейдіть на сторінку «Пам'ятки», "
                 "щоб додати цікаві місця сюди.")
        if st.button("🗺️ Перейти до пам'яток"):
            st.session_state.page = "Пам'ятки"
            st.rerun()
        return

    st.write(f"У вас **{len(st.session_state.favorites)}** обраних пам'яток:")
    for name in sorted(st.session_state.favorites):
        item = landmark_by_name(name)
        if not item:
            continue
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{item['name']}** — _{item['category']}_")
                st.caption(item["desc"])
            with c2:
                if st.button("💔 Прибрати", key=f"remove_fav_{name}"):
                    toggle_favorite(name)
                    st.rerun()


def page_route_planner():
    st.header("📝 Планувальник маршруту")
    st.caption("Оберіть пам'ятки, які хочете відвідати, і отримайте орієнтовний план дня")

    names = [i["name"] for i in LANDMARKS]
    default_selection = list(st.session_state.favorites) if st.session_state.favorites else []
    selected = st.multiselect("Оберіть пам'ятки для маршруту", names, default=default_selection)

    start_time = st.time_input("Час початку прогулянки", value=datetime.strptime("10:00", "%H:%M").time())
    travel_between = st.slider("Орієнтовний час переміщення між локаціями (хв)", 5, 40, 15)

    if not selected:
        st.info("Оберіть хоча б одну пам'ятку, щоб побудувати маршрут.")
        return

    items = [landmark_by_name(n) for n in selected]
    total_visit = sum(i["visit_min"] for i in items)
    total_travel = travel_between * max(0, len(items) - 1)
    total_minutes = total_visit + total_travel

    current_dt = datetime.combine(date.today(), start_time)
    st.subheader("🗓️ Ваш план на день")
    for idx, item in enumerate(items, start=1):
        end_dt = current_dt + pd.Timedelta(minutes=item["visit_min"])
        st.markdown(
            f"**{idx}. {item['name']}** — {current_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')} "
            f"({item['visit_min']} хв) · {item['address']}"
        )
        current_dt = end_dt + pd.Timedelta(minutes=travel_between)

    st.markdown("---")
    h, m = divmod(total_minutes, 60)
    st.success(f"⏱️ Загальний час маршруту: **{h} год {m} хв** "
               f"(відвідування: {total_visit} хв, переміщення: {total_travel} хв)")

    itinerary_text = "\n".join(
        f"{idx}. {i['name']} — {i['address']} (~{i['visit_min']} хв)"
        for idx, i in enumerate(items, start=1)
    )
    st.download_button(
        "⬇️ Завантажити маршрут як текстовий файл",
        data=f"Маршрут по Вінниці\nПочаток: {start_time.strftime('%H:%M')}\n\n{itinerary_text}",
        file_name="vinnytsia_route.txt",
        mime="text/plain",
    )


def page_about():
    st.header("ℹ️ Про місто")
    tab1, tab2 = st.tabs(["🚌 Транспорт і як дістатись", "🏆 Досягнення"])
    with tab1:
        st.markdown(TRANSPORT_INFO)
    with tab2:
        st.markdown(ACHIEVEMENTS)


def page_feedback():
    st.header("📮 Зворотній зв'язок")
    st.caption("Поділіться враженнями від платформи або запропонуйте нову пам'ятку чи заклад")

    with st.form("feedback_form", clear_on_submit=True):
        name = st.text_input("Ваше ім'я")
        email = st.text_input("Email (необов'язково)")
        category = st.selectbox("Тема звернення", ["Пропозиція", "Помилка на сайті", "Подяка", "Інше"])
        message = st.text_area("Повідомлення")
        submitted = st.form_submit_button("📤 Надіслати")

        if submitted:
            if not name or not message:
                st.warning("Будь ласка, заповніть ім'я та повідомлення.")
            else:
                st.session_state.feedback_list.append({
                    "name": name, "email": email, "category": category,
                    "message": message, "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                })
                st.success("Дякуємо за ваш відгук! 🙌")

    if st.session_state.feedback_list:
        st.markdown("---")
        st.subheader("Останні відгуки (демо, зберігаються лише в поточній сесії)")
        for fb in reversed(st.session_state.feedback_list[-5:]):
            with st.container(border=True):
                st.markdown(f"**{fb['name']}** · _{fb['category']}_ · {fb['date']}")
                st.write(fb["message"])


def page_chatbot():
    st.header("🤖 Чат-бот — віртуальний гід по Вінниці")
    st.caption("Запитайте про пам'ятки, ресторани, події, транспорт, погоду чи історію міста.")

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
    init_session_state()
    render_header()

    pages = {
        "Головна": page_home,
        "Пам'ятки": page_landmarks,
        "Карта": page_map,
        "Події": page_events,
        "Ресторани": page_restaurants,
        "Обране": page_favorites,
        "Маршрут": page_route_planner,
        "Чат-бот": page_chatbot,
        "Про місто": page_about,
        "Зворотній зв'язок": page_feedback,
    }

    with st.sidebar:
        st.markdown("## 🏙️ Моя Вінниця")
        # Синхронізація в обидва боки:
        #  - page → nav_radio: перед створенням віджета (кнопки швидкого доступу);
        #  - nav_radio → page: через on_change (вибір користувача в сайдбарі).
        _sync_nav_from_page()
        st.radio("Навігація", list(pages.keys()), key="nav_radio", on_change=_on_nav_change)
        st.markdown("---")
        st.caption(f"⭐ Обраних пам'яток: {len(st.session_state.favorites)}")
        st.caption("Демо-платформа про м. Вінниця, зроблена на Streamlit.")

    # get() із запасним варіантом — щоб уникнути KeyError при некоректному значенні
    pages.get(st.session_state.page, page_home)()


if __name__ == "__main__":
    main()
