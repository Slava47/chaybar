import telebot
from telebot import types
import os
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения TELEGRAM_BOT_TOKEN
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    logger.error("Токен не найден! Установите переменную окружения TELEGRAM_BOT_TOKEN")
    logger.info("Пример: export TELEGRAM_BOT_TOKEN='ваш_токен' или создайте файл .env")
    exit(1)

bot = telebot.TeleBot(TOKEN)

# Путь к папке с фотографиями чая
TEA_PHOTOS_DIR = "app/tea_photos/"

# Проверяем существование папки с фотографиями
if not os.path.exists(TEA_PHOTOS_DIR):
    logger.warning(f"Папка {TEA_PHOTOS_DIR} не найдена. Создайте её и добавьте фотографии чаев.")
    os.makedirs(TEA_PHOTOS_DIR, exist_ok=True)

# Меню чаев с путями к фотографиям
TEA_MENU = {
    "Зеленый чай Сенча": {
        "description": "Японский зеленый чай с нежным травяным вкусом и свежим ароматом. Идеален для утреннего пробуждения.",
        "price": 180,
        "characteristics": {"type": "green", "strength": "light", "caffeine": "medium", "taste": "fresh", "aroma": "grassy"},
        "photo_file": "Сенча.png"
    },
    "Улун Те Гуань Инь": {
        "description": "Китайский улун с цветочным ароматом и медовым послевкусием. Ценится за сложный букет.",
        "price": 220,
        "characteristics": {"type": "oolong", "strength": "medium", "caffeine": "medium", "taste": "floral", "aroma": "orchid"},
        "photo_file": "улун_те_гуань_инь.jpg"
    },
    "Черный чай Дарджилинг": {
        "description": "Индийский черный чай с мускатными нотками, 'чайное шампанское'. Элегантный и бодрящий.",
        "price": 200,
        "characteristics": {"type": "black", "strength": "strong", "caffeine": "high", "taste": "muscatel", "aroma": "fruity"},
        "photo_file": "индия.jpg"
    },
    "Белый чай Бай Хао Инь Чжэнь": {
        "description": "Нежный белый чай из нераспустившихся почек с тонким цветочным вкусом. Утонченный выбор.",
        "price": 250,
        "characteristics": {"type": "white", "strength": "very_light", "caffeine": "low", "taste": "delicate", "aroma": "honey"},
        "photo_file": "белый.jpg"
    },
    "Пуэр Шу": {
        "description": "Ферментированный чай с землистым вкусом и глубоким послевкусием. С возрастом становится лучше.",
        "price": 240,
        "characteristics": {"type": "pu-erh", "strength": "very_strong", "caffeine": "medium", "taste": "earthy", "aroma": "woody"},
        "photo_file": "шу_пуэр.jpg"
    },
    "Ройбуш": {
        "description": "Южноафриканский травяной настой без кофеина со сладковатым вкусом. Успокаивающий напиток.",
        "price": 160,
        "characteristics": {"type": "herbal", "strength": "light", "caffeine": "none", "taste": "sweet", "aroma": "nutty"},
        "photo_file": "Ройбуш.jpg"
    },
    "Чай с жасмином": {
        "description": "Зеленый чай, ароматизированный цветами жасмина. Благоухающий и освежающий.",
        "price": 190,
        "characteristics": {"type": "scented", "strength": "light", "caffeine": "medium", "taste": "floral", "aroma": "jasmine"},
        "photo_file": "жасмин.jpg"
    },
    "Иван-чай": {
        "description": "Традиционный русский травяной напиток с мягким вкусом. Натуральный и полезный.",
        "price": 170,
        "characteristics": {"type": "herbal", "strength": "medium", "caffeine": "none", "taste": "herbal", "aroma": "meadow"},
        "photo_file": "иван_чай.jpg"
    }
}

# Вопросы теста для чайного сомелье
QUESTIONS = [
    {
        "text": "Какой тип чая предпочитаете?",
        "options": {
            "Зеленый": "green",
            "Черный": "black", 
            "Улун": "oolong",
            "Белый": "white",
            "Травяной": "herbal"
        }
    },
    {
        "text": "Какую крепость напитка предпочитаете?",
        "options": {
            "Очень легкую": "very_light",
            "Легкую": "light",
            "Среднюю": "medium",
            "Крепкую": "strong",
            "Очень крепкую": "very_strong"
        }
    },
    {
        "text": "Ваше отношение к кофеину?",
        "options": {
            "Хочу бодрящий эффект": "high",
            "Умеренное содержание": "medium",
            "Минимум кофеина": "low",
            "Без кофеина": "none"
        }
    },
    {
        "text": "Какие вкусовые предпочтения?",
        "options": {
            "Цветочные нотки": "floral",
            "Фруктовые оттенки": "fruity",
            "Травяные тона": "herbal",
            "Древесные/землистые": "earthy",
            "Свежий/травяной": "fresh"
        }
    },
    {
        "text": "Какой аромат больше привлекает?",
        "options": {
            "Цветочный": "floral",
            "Фруктовый": "fruity",
            "Травяной": "grassy",
            "Древесный": "woody",
            "Медовый": "honey"
        }
    }
]

# Хранилище ответов пользователей и состояний меню
user_responses = {}
user_states = {}
user_menu_pages = {}  # Для хранения текущей страницы меню пользователя

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("🍃 Пройти тест")
    btn2 = types.KeyboardButton("📖 Посмотреть меню")
    btn3 = types.KeyboardButton("🔄 Начать заново")
    btn4 = types.KeyboardButton("ℹ️ О чаях")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# Инлайн-кнопки для меню (по 1 чаю на страницу)
def get_menu_keyboard(page=0):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Получаем список чаев
    tea_list = list(TEA_MENU.items())
    total_pages = len(tea_list)
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("◀️ Назад", callback_data=f"menu_page_{page-1}"))
    
    nav_buttons.append(types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="current_page"))
    
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Вперед ▶️", callback_data=f"menu_page_{page+1}"))
    
    if nav_buttons:
        markup.row(*nav_buttons)
    
    # Кнопки действий
    markup.add(
        types.InlineKeyboardButton("🏠 В главное меню", callback_data="to_main_menu"),
        types.InlineKeyboardButton("🍃 Пройти тест", callback_data="start_test_from_menu")
    )
    
    return markup

# Функция для отправки фото чая
def send_tea_photo(chat_id, tea_name, tea_data, caption, reply_markup=None, message_id=None):
    """Отправляет фото чая, если файл существует"""
    photo_file = tea_data.get('photo_file')
    
    if photo_file:
        photo_path = os.path.join(TEA_PHOTOS_DIR, photo_file)
        
        # Проверяем существование файла
        if os.path.exists(photo_path):
            try:
                with open(photo_path, 'rb') as photo:
                    if message_id and reply_markup:
                        # Редактируем существующее сообщение с фото
                        bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=message_id,
                            media=types.InputMediaPhoto(photo, caption=caption, parse_mode="Markdown"),
                            reply_markup=reply_markup
                        )
                    elif reply_markup:
                        # Отправляем новое фото с кнопками
                        bot.send_photo(chat_id, photo, caption=caption, 
                                     reply_markup=reply_markup, parse_mode="Markdown")
                    else:
                        # Отправляем фото без кнопок
                        bot.send_photo(chat_id, photo, caption=caption, parse_mode="Markdown")
                logger.debug(f"Фото отправлено: {photo_file}")
                return True
            except Exception as e:
                logger.error(f"Ошибка при отправке фото {photo_file}: {e}")
                # Если ошибка, отправляем текстовое сообщение
                if message_id and reply_markup:
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=caption,
                            reply_markup=reply_markup,
                            parse_mode="Markdown"
                        )
                    except:
                        bot.send_message(chat_id, caption, reply_markup=reply_markup, 
                                       parse_mode="Markdown")
                else:
                    bot.send_message(chat_id, caption, reply_markup=reply_markup, 
                                   parse_mode="Markdown")
                return False
        else:
            logger.warning(f"Файл не найден: {photo_path}")
            # Файл не найден, отправляем текстовое сообщение
            if message_id and reply_markup:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=caption,
                        reply_markup=reply_markup,
                        parse_mode="Markdown"
                    )
                except:
                    bot.send_message(chat_id, caption, reply_markup=reply_markup, 
                                   parse_mode="Markdown")
            else:
                bot.send_message(chat_id, caption, reply_markup=reply_markup, 
                               parse_mode="Markdown")
            return False
    else:
        # Нет фото, отправляем текстовое сообщение
        if message_id and reply_markup:
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except:
                bot.send_message(chat_id, caption, reply_markup=reply_markup, 
                               parse_mode="Markdown")
        else:
            bot.send_message(chat_id, caption, reply_markup=reply_markup, 
                           parse_mode="Markdown")
        return False

# Команда /start
@bot.message_handler(commands=['start'])
def start_test(message):
    user_id = message.chat.id
    user_responses[user_id] = {}
    user_states[user_id] = "main"
    
    welcome_text = (
        "🍃 *Добро пожаловать в бота-чайного сомелье!*\n\n"
        "Я помогу подобрать идеальный чайный напиток для вас!\n\n"
        "Пройти тест из 5 вопросов - и я найду чай,\n"
        "который идеально соответствует вашим предпочтениям.\n\n"
        "Выберите действие:"
    )
    
    bot.send_message(
        user_id,
        welcome_text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {user_id} начал работу с ботом")

# Обработка кнопок главного меню
@bot.message_handler(func=lambda message: message.text in ["🍃 Пройти тест", "📖 Посмотреть меню", "🔄 Начать заново", "ℹ️ О чаях"])
def handle_main_menu(message):
    user_id = message.chat.id
    
    if message.text == "🍃 Пройти тест":
        user_responses[user_id] = {}
        user_states[user_id] = "test"
        logger.info(f"Пользователь {user_id} начал тест")
        ask_question(message, 0)
        
    elif message.text == "📖 Посмотреть меню":
        logger.info(f"Пользователь {user_id} запросил меню")
        show_menu_page(message, page=0)
        
    elif message.text == "🔄 Начать заново":
        logger.info(f"Пользователь {user_id} начал заново")
        start_test(message)
        
    elif message.text == "ℹ️ О чаях":
        show_tea_info(message)

# Показать страницу меню с фото чая
def show_menu_page(message, page=0):
    user_id = message.chat.id
    user_states[user_id] = "browsing_menu"
    user_menu_pages[user_id] = page
    
    tea_list = list(TEA_MENU.items())
    total_pages = len(tea_list)
    
    if page >= total_pages:
        page = 0
    
    # Получаем текущий чай
    tea_name, tea_data = tea_list[page]
    
    # Формируем описание
    caption = (
        f"📖 *Чайная карта* (страница {page+1}/{total_pages})\n\n"
        f"*{tea_name}*\n"
        f"Цена: {tea_data['price']}₽\n\n"
        f"{tea_data['description']}\n\n"
        f"*Характеристики:*\n"
        f"• Тип: {get_tea_type_name(tea_data['characteristics']['type'])}\n"
        f"• Крепость: {get_strength_name(tea_data['characteristics']['strength'])}\n"
        f"• Кофеин: {get_caffeine_name(tea_data['characteristics']['caffeine'])}\n"
        f"• Вкус: {get_taste_name(tea_data['characteristics']['taste'])}\n"
        f"• Аромат: {get_aroma_name(tea_data['characteristics']['aroma'])}\n\n"
        f"Используйте кнопки для навигации по меню"
    )
    
    # Отправляем фото с кнопками
    send_tea_photo(
        user_id, 
        tea_name, 
        tea_data, 
        caption, 
        get_menu_keyboard(page)
    )

# Показать информацию о типах чая
def show_tea_info(message):
    info_text = (
        "*ℹ️ Информация о типах чая:*\n\n"
        "*Зеленый чай* - минимальная обработка, сохраняет натуральный цвет и свежесть\n"
        "*Черный чай* - полная ферментация, насыщенный цвет и крепкий вкус\n"
        "*Улун* - частичная ферментация, сочетает свежесть зеленого и насыщенность черного\n"
        "*Белый чай* - самые нежные почки, минимальная обработка\n"
        "*Пуэр* - ферментированный чай, выдержанный годами\n"
        "*Травяные чаи* - настои трав, цветов, плодов (не содержат чайных листьев)\n\n"
        "Рекомендую пройти тест для точного подбора!"
    )
    
    bot.send_message(
        message.chat.id,
        info_text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# Вспомогательные функции для преобразования значений
def get_tea_type_name(type_code):
    types = {
        "green": "Зеленый",
        "black": "Черный",
        "oolong": "Улун",
        "white": "Белый",
        "pu-erh": "Пуэр",
        "herbal": "Травяной",
        "scented": "Ароматизированный"
    }
    return types.get(type_code, type_code)

def get_strength_name(strength):
    strengths = {
        "very_light": "Очень легкая",
        "light": "Легкая",
        "medium": "Средняя",
        "strong": "Крепкая",
        "very_strong": "Очень крепкая"
    }
    return strengths.get(strength, strength)

def get_caffeine_name(caffeine):
    caffeine_levels = {
        "high": "Высокое",
        "medium": "Среднее",
        "low": "Низкое",
        "none": "Отсутствует"
    }
    return caffeine_levels.get(caffeine, caffeine)

def get_taste_name(taste):
    tastes = {
        "fresh": "Свежий",
        "floral": "Цветочный",
        "fruity": "Фруктовый",
        "herbal": "Травяной",
        "earthy": "Землистый",
        "muscatel": "Мускатный",
        "delicate": "Нежный",
        "sweet": "Сладковатый"
    }
    return tastes.get(taste, taste)

def get_aroma_name(aroma):
    aromas = {
        "grassy": "Травяной",
        "orchid": "Орхидея",
        "fruity": "Фруктовый",
        "honey": "Медовый",
        "woody": "Древесный",
        "jasmine": "Жасмин",
        "meadow": "Луговой",
        "nutty": "Ореховый"
    }
    return aromas.get(aroma, aroma)

# Обработка инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    user_id = call.message.chat.id
    
    if call.data.startswith("menu_page_"):
        # Листание страниц меню
        page = int(call.data.split("_")[2])
        user_menu_pages[user_id] = page
        
        tea_list = list(TEA_MENU.items())
        total_pages = len(tea_list)
        
        if page < 0 or page >= total_pages:
            return
        
        # Получаем текущий чай
        tea_name, tea_data = tea_list[page]
        
        # Формируем описание
        caption = (
            f"📖 *Чайная карта* (страница {page+1}/{total_pages})\n\n"
            f"*{tea_name}*\n"
            f"Цена: {tea_data['price']}₽\n\n"
            f"{tea_data['description']}\n\n"
            f"*Характеристики:*\n"
            f"• Тип: {get_tea_type_name(tea_data['characteristics']['type'])}\n"
            f"• Крепость: {get_strength_name(tea_data['characteristics']['strength'])}\n"
            f"• Кофеин: {get_caffeine_name(tea_data['characteristics']['caffeine'])}\n"
            f"• Вкус: {get_taste_name(tea_data['characteristics']['taste'])}\n"
            f"• Аромат: {get_aroma_name(tea_data['characteristics']['aroma'])}\n\n"
            f"Используйте кнопки для навигации по меню"
        )
        
        # Обновляем фото и кнопки
        send_tea_photo(
            user_id,
            tea_name,
            tea_data,
            caption,
            get_menu_keyboard(page),
            call.message.message_id
        )
        
    elif call.data == "to_main_menu":
        # Возврат в главное меню из меню чаев
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
        
        # Показываем главное меню
        bot.send_message(
            user_id,
            "🍃 *Главное меню*\n\nВыберите действие:",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
        
    elif call.data == "start_test_from_menu":
        # Начать тест из меню чаев
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
        
        user_responses[user_id] = {}
        user_states[user_id] = "test"
        ask_question(call.message, 0)
        
    elif call.data == "start_test_from_result":
        # Начать тест из результатов
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
        
        user_responses[user_id] = {}
        user_states[user_id] = "test"
        ask_question(call.message, 0)
        
    elif call.data == "show_menu_from_result":
        # Показать меню из результатов
        try:
            bot.delete_message(user_id, call.message.message_id)
        except:
            pass
        
        show_menu_page(call.message, page=0)

# Начать тест с первого вопроса
def ask_question(message, question_index):
    user_id = message.chat.id
    
    if question_index < len(QUESTIONS):
        question = QUESTIONS[question_index]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        buttons = []
        for option_text in question["options"].keys():
            buttons.append(types.KeyboardButton(option_text))
        
        # Распределяем кнопки по 2 в ряд
        for i in range(0, len(buttons), 2):
            if i + 1 < len(buttons):
                markup.add(buttons[i], buttons[i + 1])
            else:
                markup.add(buttons[i])
        
        # Добавляем кнопку отмены
        cancel_btn = types.KeyboardButton("🔙 Отмена")
        markup.add(cancel_btn)
        
        bot.send_message(
            user_id,
            f"*Вопрос {question_index + 1}/{len(QUESTIONS)}:*\n{question['text']}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        # Сохраняем текущий вопрос
        user_states[user_id] = f"question_{question_index}"
        logger.debug(f"Пользователь {user_id} получил вопрос {question_index + 1}")
    else:
        show_result(message)

# Обработка ответов на вопросы теста
@bot.message_handler(func=lambda message: user_states.get(message.chat.id, "").startswith("question_"))
def handle_test_answer(message):
    user_id = message.chat.id
    
    if message.text == "🔙 Отмена":
        bot.send_message(user_id, "Тест отменен.", reply_markup=main_menu())
        user_states[user_id] = "main"
        logger.info(f"Пользователь {user_id} отменил тест")
        return
    
    # Получаем номер текущего вопроса
    current_state = user_states[user_id]
    question_index = int(current_state.split("_")[1])
    
    if question_index >= len(QUESTIONS):
        return
    
    question = QUESTIONS[question_index]
    user_answer = message.text
    
    # Проверяем, что ответ валидный
    if user_answer in question["options"]:
        user_responses[user_id][f"q{question_index}"] = question["options"][user_answer]
        logger.debug(f"Пользователь {user_id}: вопрос {question_index + 1}, ответ: {user_answer}")
        
        # Переходим к следующему вопросу
        next_question = question_index + 1
        ask_question(message, next_question)
    else:
        # Неверный ответ - повторяем вопрос
        bot.send_message(
            user_id,
            "Пожалуйста, выберите вариант из предложенных кнопок.",
            parse_mode="Markdown"
        )
        ask_question(message, question_index)

# Функция подбора чая (только один лучший)
def find_best_tea(user_prefs):
    best_tea = None
    best_score = 0
    
    for tea_name, tea_data in TEA_MENU.items():
        score = 0
        chars = tea_data["characteristics"]
        
        # Сравниваем каждый критерий
        for i in range(len(QUESTIONS)):
            q_key = f"q{i}"
            if q_key in user_prefs:
                user_val = user_prefs[q_key]
                tea_val = chars[list(chars.keys())[i]]
                
                if user_val == tea_val:
                    score += 3  # Полное совпадение
                elif i == 0 and user_val in ["green", "black", "oolong", "white"] and tea_val in ["green", "black", "oolong", "white"]:
                    score += 1  # Оба настоящие чаи
                elif i == 2:  # Кофеин
                    if user_val == "high" and tea_val == "high":
                        score += 2
                    elif user_val == "none" and tea_val == "none":
                        score += 2
                    elif user_val in ["medium", "low"] and tea_val in ["medium", "low"]:
                        score += 1
        
        # Если нашли чай с лучшим счетом
        if score > best_score:
            best_score = score
            best_tea = (tea_name, tea_data, score)
    
    return best_tea

# Показать результат с фото (только один лучший чай)
def show_result(message):
    user_id = message.chat.id
    
    if user_id not in user_responses or len(user_responses[user_id]) < len(QUESTIONS):
        bot.send_message(
            user_id, 
            "Давайте пройдем тест сначала.", 
            reply_markup=main_menu()
        )
        return
    
    # Находим лучший чай
    best_tea = find_best_tea(user_responses[user_id])
    
    if not best_tea:
        bot.send_message(
            user_id,
            "😔 К сожалению, не нашлось идеального чая по вашим предпочтениям.\nПопробуйте изменить критерии или посмотрите полное меню.",
            reply_markup=main_menu()
        )
        return
    
    tea_name, tea_data, score = best_tea
    
    # Формируем текст результата
    result_text = (
        f"🎉 *Ваш идеальный чай подобран!*\n\n"
        f"По вашим предпочтениям я рекомендую:\n\n"
        f"*{tea_name}* - {tea_data['price']}₽\n"
        f"Совпадение: {score}/15 баллов\n\n"
        f"{tea_data['description']}\n\n"
        f"*Характеристики:*\n"
        f"• Тип: {get_tea_type_name(tea_data['characteristics']['type'])}\n"
        f"• Крепость: {get_strength_name(tea_data['characteristics']['strength'])}\n"
        f"• Кофеин: {get_caffeine_name(tea_data['characteristics']['caffeine'])}\n"
        f"• Вкус: {get_taste_name(tea_data['characteristics']['taste'])}\n"
        f"• Аромат: {get_aroma_name(tea_data['characteristics']['aroma'])}\n\n"
        f"Что вы хотите сделать дальше?"
    )
    
    # Создаем кнопки для результата
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📖 Посмотреть меню", callback_data="show_menu_from_result"),
        types.InlineKeyboardButton("🍃 Пройти тест заново", callback_data="start_test_from_result"),
        types.InlineKeyboardButton("🏠 В главное меню", callback_data="to_main_menu")
    )
    
    # Отправляем результат с фото
    send_tea_photo(user_id, tea_name, tea_data, result_text, markup)
    
    user_states[user_id] = "result"
    logger.info(f"Пользователь {user_id} получил рекомендацию: {tea_name} (счет: {score}/15)")
    
    # Очищаем ответы пользователя для следующего теста
    user_responses[user_id] = {}

# Обработка команды /test
@bot.message_handler(commands=['test'])
def start_test_command(message):
    user_id = message.chat.id
    user_responses[user_id] = {}
    user_states[user_id] = "test"
    logger.info(f"Пользователь {user_id} начал тест через команду")
    ask_question(message, 0)

# Обработка команды /help
@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = (
        "*🍃 Чайный сомелье - доступные команды:*\n\n"
        "/start - Главное меню\n"
        "/test - Начать тест по подбору чая\n"
        "/menu - Показать чайную карту\n"
        "/help - Эта справка\n\n"
        "*Или используйте кнопки меню:*\n"
        "🍃 Пройти тест - подбор чая по предпочтениям\n"
        "📖 Посмотреть меню - вся чайная карта (листается кнопками)\n"
        "ℹ️ О чаях - информация о типах чая\n"
        "🔄 Начать заново - сбросить всё"
    )
    
    bot.send_message(
        message.chat.id,
        help_text,
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {message.chat.id} запросил справку")

# Обработка команды /menu
@bot.message_handler(commands=['menu'])
def command_menu(message):
    show_menu_page(message, page=0)

# Проверить существование всех файлов фотографий
def check_photo_files():
    missing_files = []
    available_files = []
    
    for tea_name, tea_data in TEA_MENU.items():
        photo_file = tea_data.get('photo_file')
        if photo_file:
            photo_path = os.path.join(TEA_PHOTOS_DIR, photo_file)
            if os.path.exists(photo_path):
                available_files.append(photo_file)
            else:
                missing_files.append((tea_name, photo_file))
    
    return available_files, missing_files

# Обработка любых других сообщений (fallback)
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    user_id = message.chat.id
    
    # Если это команда, игнорируем (она обрабатывается выше)
    if message.text and message.text.startswith('/'):
        return
    
    # Если пользователь не в состоянии или в главном меню
    if user_id not in user_states or user_states[user_id] == "main":
        bot.send_message(
            user_id,
            "🍃 *Чайный сомелье приветствует вас!*\n\n"
            "Пожалуйста, выберите действие из меню ниже:",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    else:
        # Если пользователь в процессе теста или другого состояния
        bot.send_message(
            user_id,
            "Пожалуйста, используйте кнопки для выбора вариантов или нажмите /start для возврата в главное меню.",
            parse_mode="Markdown"
        )

# Запуск бота
if __name__ == "__main__":
    # Проверяем фото файлы при запуске
    available_files, missing_files = check_photo_files()
    
    if available_files:
        logger.info(f"✅ Найдено {len(available_files)} фото: {', '.join(available_files)}")
    else:
        logger.warning("⚠️ Фотографии чаев не найдены. Бот будет работать без фото.")
    
    if missing_files:
        logger.warning("⚠️ Отсутствующие фото:")
        for tea_name, photo_file in missing_files:
            logger.warning(f"  - {tea_name}: {photo_file}")
    
    # Проверяем подключение к боту
    try:
        bot_info = bot.get_me()
        logger.info(f"✅ Бот успешно запущен: @{bot_info.username}")
        logger.info(f"🍃 Имя бота: {bot_info.first_name}")
        logger.info(f"🆔 ID бота: {bot_info.id}")
        logger.info("🍵 Чайный сомелье готов к работе!")
        logger.info("=" * 50)
        
        # Запускаем опрос
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        logger.error("Проверьте ваш токен TELEGRAM_BOT_TOKEN")
        exit(1)
