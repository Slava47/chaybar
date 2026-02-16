"""
Телеграм-бот для бара «Ли Бо».
Запуск: python bot.py
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import init_db, add_user, add_quiz_session, add_cocktail_rating, get_user_stats
from cocktails import (
    get_cocktails_by_category,
    get_category_name,
    match_cocktails,
    COLD_COCKTAILS,
    HOT_COCKTAILS,
    ALCOHOLIC_COCKTAILS,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не задана. Получите токен у @BotFather.")

PICTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pictures")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


# ─── FSM States ───────────────────────────────────────────────────────────────

class QuizStates(StatesGroup):
    q_alcoholic = State()
    q_temperature = State()
    q_taste = State()
    q_tea = State()
    q_strength = State()
    browsing_results = State()
    waiting_review = State()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню", callback_data="menu")],
        [InlineKeyboardButton(text="Подобрать коктейль", callback_data="quiz_start")],
        [InlineKeyboardButton(text="Карточка гостя", callback_data="guest_card")],
        [InlineKeyboardButton(text="О нас", callback_data="about")],
    ])


def cocktail_text(c: dict) -> str:
    return (
        f"<b>{c['name']}</b>\n\n"
        f"{c['description']}\n\n"
        f"Состав: {c['ingredients']}\n"
        f"Цена: {c['price']} руб."
    )


def get_cocktail_image(c: dict):
    """Возвращает FSInputFile если файл изображения найден, иначе None."""
    image_name = c.get("image", "")
    if not image_name:
        return None
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(PICTURES_DIR, image_name + ext)
        if os.path.isfile(path):
            return FSInputFile(path)
    return None


# ─── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await add_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        message.from_user.last_name or "",
    )
    await message.answer(
        "Добро пожаловать в <b>Ли Бо</b> — чайный бар и коктейли!\n\nВыберите раздел:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )


# ─── MENU ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu")
async def menu_categories(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Холодные безалкогольные", callback_data="cat_cold")],
        [InlineKeyboardButton(text="Горячие безалкогольные", callback_data="cat_hot")],
        [InlineKeyboardButton(text="Алкогольные", callback_data="cat_alcoholic")],
        [InlineKeyboardButton(text="« Назад", callback_data="home")],
    ])
    await callback.message.edit_text(
        "<b>Меню</b>\n\nВыберите категорию:",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def menu_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.replace("cat_", "")
    items = get_cocktails_by_category(category)
    if not items:
        await callback.answer("Категория пуста")
        return
    await state.update_data(menu_category=category, menu_index=0)
    await show_menu_item(callback, state)


async def show_menu_item(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = data["menu_category"]
    index = data["menu_index"]
    items = get_cocktails_by_category(category)
    c = items[index]

    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data="menu_prev"))
    nav_buttons.append(
        InlineKeyboardButton(text=f"{index + 1}/{len(items)}", callback_data="menu_noop")
    )
    if index < len(items) - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data="menu_next"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons,
        [InlineKeyboardButton(text="« Назад к категориям", callback_data="menu")],
    ])

    text = f"<b>{get_category_name(category)}</b>\n\n{cocktail_text(c)}"
    photo = get_cocktail_image(c)

    # Delete old message and send new one (to support switching between photo/text)
    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo:
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


@router.callback_query(F.data == "menu_prev")
async def menu_prev(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = max(0, data.get("menu_index", 0) - 1)
    await state.update_data(menu_index=index)
    await show_menu_item(callback, state)


@router.callback_query(F.data == "menu_next")
async def menu_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = data.get("menu_category", "cold")
    items = get_cocktails_by_category(category)
    index = min(len(items) - 1, data.get("menu_index", 0) + 1)
    await state.update_data(menu_index=index)
    await show_menu_item(callback, state)


@router.callback_query(F.data == "menu_noop")
async def menu_noop(callback: CallbackQuery):
    await callback.answer()


# ─── ABOUT ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "<b>Ли Бо | Чайный бар и коктейли</b>\n"
        "Фридриха Энгельса, 13\n\n"
        "Авторские коктейли на китайском чае — алкогольные и безалкогольные. "
        "Азиатское крафтовое пиво, согревающие закуски. "
        "Поэзия вкуса в самом центре, у парка «Орлёнок».\n\n"
        "<b>Авторы бота:</b>\n"
        "Разработчик — Руденко Вячеслав Александрович\n"
        "Тестировщик — Баркалов Владимир Вячеславович\n\n"
        "Наши соц. сети:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ВКонтакте", url="https://vk.com/libotea")],
        [InlineKeyboardButton(text="Telegram", url="https://t.me/libo_tea")],
        [InlineKeyboardButton(text="Instagram", url="https://www.instagram.com/libo.tea/")],
        [InlineKeyboardButton(text="« Назад", callback_data="home")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── HOME ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Добро пожаловать в <b>Ли Бо</b> — чайный бар и коктейли!\n\nВыберите раздел:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── GUEST CARD ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "guest_card")
async def guest_card(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    stats = await get_user_stats(callback.from_user.id)
    text = (
        f"<b>Карточка гостя</b>\n\n"
        f"ID: <code>{callback.from_user.id}</code>\n"
        f"Подборов коктейлей: {stats['quiz_count']}\n\n"
    )
    if stats["ratings"]:
        text += "<b>Ваши оценки:</b>\n"
        for r in stats["ratings"][:10]:
            review_text = f" — {r['review']}" if r.get("review") else ""
            text += f"• {r['cocktail_name']}: {r['rating']}{review_text}\n"
    else:
        text += "Вы пока не оценивали коктейли."

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="home")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


# ─── QUIZ ─────────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "quiz_start")
async def quiz_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizStates.q_alcoholic)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Алкогольный", callback_data="qa_yes")],
        [InlineKeyboardButton(text="Безалкогольный", callback_data="qa_no")],
    ])
    await callback.message.edit_text(
        "<b>Подбор коктейля</b>\n\nВопрос 1/5:\nАлкогольный или безалкогольный?",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(QuizStates.q_alcoholic, F.data.startswith("qa_"))
async def quiz_alcoholic(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("qa_", "")
    await state.update_data(alcoholic=answer)

    if answer == "yes":
        # Алкогольные — пропускаем вопрос о температуре
        await state.update_data(temperature="any")
        await state.set_state(QuizStates.q_taste)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сладкий", callback_data="qt_sweet")],
            [InlineKeyboardButton(text="Кисло-сладкий", callback_data="qt_sour_sweet")],
            [InlineKeyboardButton(text="Кислый", callback_data="qt_sour")],
        ])
        await callback.message.edit_text(
            "<b>Подбор коктейля</b>\n\nВопрос 2/5:\nКакой вкус предпочитаете?",
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        await state.set_state(QuizStates.q_temperature)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Холодный", callback_data="qtemp_cold")],
            [InlineKeyboardButton(text="Горячий", callback_data="qtemp_hot")],
            [InlineKeyboardButton(text="Без разницы", callback_data="qtemp_any")],
        ])
        await callback.message.edit_text(
            "<b>Подбор коктейля</b>\n\nВопрос 2/5:\nХолодный или горячий?",
            reply_markup=kb,
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(QuizStates.q_temperature, F.data.startswith("qtemp_"))
async def quiz_temperature(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("qtemp_", "")
    await state.update_data(temperature=answer)
    await state.set_state(QuizStates.q_taste)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сладкий", callback_data="qt_sweet")],
        [InlineKeyboardButton(text="Кисло-сладкий", callback_data="qt_sour_sweet")],
        [InlineKeyboardButton(text="Кислый", callback_data="qt_sour")],
    ])
    await callback.message.edit_text(
        "<b>Подбор коктейля</b>\n\nВопрос 3/5:\nКакой вкус предпочитаете?",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(QuizStates.q_taste, F.data.startswith("qt_"))
async def quiz_taste(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("qt_", "")
    await state.update_data(taste=answer)
    await state.set_state(QuizStates.q_tea)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Более чайный", callback_data="qtea_more")],
        [InlineKeyboardButton(text="Менее чайный", callback_data="qtea_less")],
    ])
    await callback.message.edit_text(
        "<b>Подбор коктейля</b>\n\nВопрос 4/5:\nБолее чайный или менее чайный?",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(QuizStates.q_tea, F.data.startswith("qtea_"))
async def quiz_tea(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("qtea_", "")
    await state.update_data(tea_strength=answer)
    await state.set_state(QuizStates.q_strength)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Крепкий", callback_data="qs_strong")],
        [InlineKeyboardButton(text="Мягкий", callback_data="qs_soft")],
    ])
    await callback.message.edit_text(
        "<b>Подбор коктейля</b>\n\nВопрос 5/5:\nКрепкий или мягкий?",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(QuizStates.q_strength, F.data.startswith("qs_"))
async def quiz_strength(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.replace("qs_", "")
    await state.update_data(strength=answer)
    data = await state.get_data()

    session_id = await add_quiz_session(callback.from_user.id, data)
    results = match_cocktails(data)
    await state.update_data(
        quiz_results=results,
        quiz_result_index=0,
        quiz_session_id=session_id,
    )
    await state.set_state(QuizStates.browsing_results)
    await show_quiz_result(callback, state)


async def show_quiz_result(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    results = data.get("quiz_results", [])
    index = data.get("quiz_result_index", 0)

    if not results:
        await callback.message.edit_text(
            "К сожалению, не удалось подобрать коктейль. Попробуйте ещё раз!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="« Назад", callback_data="home")],
            ]),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    c = results[index]
    nav_buttons = []
    if index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data="qr_prev"))
    nav_buttons.append(
        InlineKeyboardButton(text=f"{index + 1}/{len(results)}", callback_data="qr_noop")
    )
    if index < len(results) - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data="qr_next"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        nav_buttons,
        [InlineKeyboardButton(text="Оценить коктейль", callback_data="rate_cocktail")],
        [InlineKeyboardButton(text="« На главную", callback_data="home")],
    ])

    text = f"<b>Рекомендация</b>\n\n{cocktail_text(c)}"
    photo = get_cocktail_image(c)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if photo:
        await callback.message.answer_photo(photo=photo, caption=text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")

    await callback.answer()


@router.callback_query(QuizStates.browsing_results, F.data == "qr_prev")
async def qr_prev(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = max(0, data.get("quiz_result_index", 0) - 1)
    await state.update_data(quiz_result_index=index)
    await show_quiz_result(callback, state)


@router.callback_query(QuizStates.browsing_results, F.data == "qr_next")
async def qr_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    results = data.get("quiz_results", [])
    index = min(len(results) - 1, data.get("quiz_result_index", 0) + 1)
    await state.update_data(quiz_result_index=index)
    await show_quiz_result(callback, state)


@router.callback_query(QuizStates.browsing_results, F.data == "qr_noop")
async def qr_noop(callback: CallbackQuery):
    await callback.answer()


# ─── RATING ───────────────────────────────────────────────────────────────────

RATING_OPTIONS = [
    "Отлично",
    "Слишком крепкий",
    "Слишком сладкий",
    "Слишком кислый",
    "Слишком чайный",
    "Недостаточно сладкий",
    "Недостаточно крепкий",
]


@router.callback_query(QuizStates.browsing_results, F.data == "rate_cocktail")
async def rate_cocktail(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt, callback_data=f"rating_{i}")]
        for i, opt in enumerate(RATING_OPTIONS)
    ] + [[InlineKeyboardButton(text="« Назад", callback_data="back_to_results")]])
    await callback.message.edit_text(
        "<b>Оцените коктейль:</b>",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(QuizStates.browsing_results, F.data == "back_to_results")
async def back_to_results(callback: CallbackQuery, state: FSMContext):
    await show_quiz_result(callback, state)


@router.callback_query(QuizStates.browsing_results, F.data.startswith("rating_"))
async def save_rating(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.replace("rating_", ""))
    rating = RATING_OPTIONS[idx]
    data = await state.get_data()
    results = data.get("quiz_results", [])
    index = data.get("quiz_result_index", 0)
    cocktail_name = results[index]["name"] if results else "Неизвестно"
    session_id = data.get("quiz_session_id")

    await state.update_data(pending_rating=rating, pending_cocktail=cocktail_name)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать отзыв", callback_data="write_review")],
        [InlineKeyboardButton(text="Пропустить", callback_data="skip_review")],
    ])
    await callback.message.edit_text(
        f"Оценка: <b>{rating}</b>\n\nХотите оставить отзыв?",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(QuizStates.browsing_results, F.data == "write_review")
async def write_review_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(QuizStates.waiting_review)
    await callback.message.edit_text(
        "Напишите ваш отзыв текстовым сообщением:",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(QuizStates.waiting_review)
async def save_review(message: Message, state: FSMContext):
    data = await state.get_data()
    rating = data.get("pending_rating", "")
    cocktail_name = data.get("pending_cocktail", "")
    session_id = data.get("quiz_session_id")
    review = message.text

    await add_cocktail_rating(message.from_user.id, cocktail_name, rating, review, session_id)
    await state.set_state(QuizStates.browsing_results)
    await message.answer(
        f"Спасибо за отзыв о <b>{cocktail_name}</b>!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« На главную", callback_data="home")],
        ]),
        parse_mode="HTML",
    )


@router.callback_query(QuizStates.browsing_results, F.data == "skip_review")
async def skip_review(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    rating = data.get("pending_rating", "")
    cocktail_name = data.get("pending_cocktail", "")
    session_id = data.get("quiz_session_id")

    await add_cocktail_rating(callback.from_user.id, cocktail_name, rating, None, session_id)
    await callback.message.edit_text(
        f"Оценка сохранена для <b>{cocktail_name}</b>!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« На главную", callback_data="home")],
        ]),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
