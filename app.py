# -*- coding: utf-8 -*-
"""
Платформа "Моя Вінниця" — інформаційний портал про місто Вінниця
з чат-ботом-гідом на Streamlit.

Запуск:
    pip install streamlit
    streamlit run vinnytsia_app.py
"""

import streamlit as st
import re
from datetime import date

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
]

LANDMARKS = [
    {
        "name": "Фонтан Roshen",
        "category": "Розваги",
        "desc": "Найбільший плавучий світломузичний фонтан у Європі, розташований на річці Південний Буг. "
                "Шоу відбувається у теплу пору року у вечірній час, поєднуючи воду, світло та музику.",
        "address": "Набережна, біля Кемпа",
        "tags": ["фонтан", "roshen", "рошен", "шоу", "музика", "набережна"],
    },
    {
        "name": "Музей-садиба М.І. Пирогова «Вишня»",
        "category": "Музей",
        "desc": "Меморіальний комплекс, де жив і працював видатний хірург Микола Пирогов. "
                "У церкві-некрополі зберігається забальзамоване тіло вченого.",
        "address": "вул. Пирогова, 155",
        "tags": ["пирогов", "музей", "садиба", "вишня", "хірург"],
    },
    {
        "name": "Вінницькі мури (Мури)",
        "category": "Історія",
        "desc": "Залишки укріплень єзуїтського монастиря XVII століття, одна з найстаріших пам'яток міста, "
                "розташована в історичному центрі.",
        "address": "Старе місто, центр",
        "tags": ["мури", "фортеця", "історія", "центр", "єзуїти"],
    },
    {
        "name": "Водонапірна вежа",
        "category": "Архітектура",
        "desc": "Символ Вінниці, споруджена у 1912 році. Нині в приміщенні вежі працює виставковий простір.",
        "address": "вул. Соборна",
        "tags": ["вежа", "водонапірна", "архітектура", "соборна"],
    },
    {
        "name": "Спасо-Преображенський кафедральний собор",
        "category": "Церква",
        "desc": "Головний православний храм міста, кафедральний собор з багатою історією та красивим інтер'єром.",
        "address": "вул. Соборна, 23",
        "tags": ["церква", "собор", "храм", "релігія"],
    },
    {
        "name": "Костел Пресвятої Діви Марії Ангельської",
        "category": "Церква",
        "desc": "Один з найстаріших католицьких храмів Вінниці, зразок бароккової архітектури.",
        "address": "Старе місто",
        "tags": ["костел", "церква", "храм", "барокко"],
    },
    {
        "name": "Парк Дружби народів (Центральний парк)",
        "category": "Парк",
        "desc": "Найпопулярніший парк міста для прогулянок, відпочинку та сімейного дозвілля, з алеями та атракціонами.",
        "address": "вул. Хмельницьке шосе",
        "tags": ["парк", "прогулянка", "відпочинок", "діти", "дружби народів"],
    },
    {
        "name": "Театральна площа",
        "category": "Центр",
        "desc": "Центральна площа міста з музичним драматичним театром ім. Садовського, місце проведення подій.",
        "address": "Театральна площа",
        "tags": ["площа", "театр", "центр", "події"],
    },
    {
        "name": "Музей історії міста Вінниці",
        "category": "Музей",
        "desc": "Експозиції з історії Вінниці від найдавніших часів до сьогодення.",
        "address": "вул. Соборна",
        "tags": ["музей", "історія", "експозиція"],
    },
    {
        "name": "Синагога «Бейт Кнесет»",
        "category": "Релігія",
        "desc": "Діюча синагога, що є свідченням багатої єврейської історії міста.",
        "address": "центр міста",
        "tags": ["синагога", "релігія", "історія", "євреї"],
    },
]

EVENTS = [
    {
        "name": "VinnytsiaJazzFest",
        "date": "Червень",
        "desc": "Міжнародний джазовий фестиваль просто неба за участю українських та закордонних музикантів.",
        "place": "Центральний парк / набережна",
    },
    {
        "name": "Vinnytsia Food Fest",
        "date": "Липень–Серпень",
        "desc": "Фестиваль вуличної їжі з десятками локальних закладів і фудтраків.",
        "place": "Театральна площа",
    },
    {
        "name": "«Острів Європи»",
        "date": "Вересень",
        "desc": "Мультикультурний фестиваль, присвячений європейським традиціям, музиці та кухні різних країн.",
        "place": "Набережна / Кемпа",
    },
    {
        "name": "День міста Вінниці",
        "date": "Вересень",
        "desc": "Головне міське свято з концертами, ярмарками та феєрверком.",
        "place": "Центр міста",
    },
    {
        "name": "Різдвяний ярмарок",
        "date": "Грудень",
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
}

GREETINGS = ["привіт", "вітаю", "добрий день", "доброго дня", "хай", "hello", "hi"]
THANKS = ["дякую", "спасибі", "дяка", "thanks"]

QUICK_QUESTIONS = [
    "Розкажи про фонтан Roshen",
    "Де музей Пирогова?",
    "Які події найближчим часом?",
    "Порадь ресторан",
    "Як дістатися до Вінниці?",
    "Коли засновано місто?",
]


def get_bot_response(user_text: str) -> str:
    """Проста rule-based логіка чат-бота на основі ключових слів."""
    text = user_text.lower().strip()
    text_clean = re.sub(r"[^\w\sа-яіїєґ]", "", text)

    if any(g in text_clean for g in GREETINGS):
        return ("Вітаю! 👋 Я віртуальний гід по Вінниці. Запитайте мене про пам'ятки, ресторани, "
                "події чи транспорт — і я підкажу!")

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
            "музей Пирогова, Вінницькі мури, церкви, парки, ресторани, транспорт, історію або події міста.")


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
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🗺️ Пам'ятки", use_container_width=True):
        st.session_state.page = "Пам'ятки"
        st.rerun()
    if c2.button("🎉 Події", use_container_width=True):
        st.session_state.page = "Події"
        st.rerun()
    if c3.button("🍽️ Ресторани", use_container_width=True):
        st.session_state.page = "Ресторани"
        st.rerun()
    if c4.button("🤖 Чат-бот", use_container_width=True):
        st.session_state.page = "Чат-бот"
        st.rerun()

    st.markdown("---")
    st.subheader("💡 Цікаві факти")
    for fact in FACTS:
        st.markdown(f"- {fact}")


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
        with st.expander(f"📍 {item['name']}  —  _{item['category']}_"):
            st.write(item["desc"])
            st.caption(f"Адреса: {item['address']}")


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


def page_about():
    st.header("ℹ️ Про місто")
    tab1, tab2 = st.tabs(["🚌 Транспорт і як дістатись", "🏆 Досягнення"])
    with tab1:
        st.markdown(TRANSPORT_INFO)
    with tab2:
        st.markdown(ACHIEVEMENTS)


def page_chatbot():
    st.header("🤖 Чат-бот — віртуальний гід по Вінниці")
    st.caption("Запитайте про пам'ятки, ресторани, події, транспорт чи історію міста.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Вітаю! 👋 Я віртуальний гід по Вінниці. Чим можу допомогти?"}
        ]

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
    render_header()

    pages = {
        "Головна": page_home,
        "Пам'ятки": page_landmarks,
        "Події": page_events,
        "Ресторани": page_restaurants,
        "Чат-бот": page_chatbot,
        "Про місто": page_about,
    }

    if "page" not in st.session_state:
        st.session_state.page = "Головна"

    with st.sidebar:
        st.markdown("## 🏙️ Моя Вінниця")
        choice = st.radio("Навігація", list(pages.keys()), index=list(pages.keys()).index(st.session_state.page))
        st.session_state.page = choice
        st.markdown("---")
        st.caption("Демо-платформа про м. Вінниця, зроблена на Streamlit.")

    pages[st.session_state.page]()


if __name__ == "__main__":
    main()
