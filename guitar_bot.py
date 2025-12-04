import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.types import ReplyKeyboardRemove
from moviepy.editor import VideoFileClip
from PIL import Image
API_TOKEN = '7506710417:AAHXrTPDGkwAb4_AOl_Dx1s0e9_KPmI_Kj0'  # Замените на ваш токен
CHANNEL_ID = '2415954391'  # Замените на ваш ID канала

# Пути к видео и миниатюре
video_path = 'фриссон.mp4'  # Замените на ваш путь
thumbnail_path = 'thumbnail.jpg'

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Функция создания миниатюры
def create_thumbnail(video_path, thumbnail_path, time=1.0):
    clip = VideoFileClip(video_path)
    frame = clip.get_frame(time)
    img = Image.fromarray(frame)
    img.save(thumbnail_path)

# Создаем миниатюру один раз при запуске
if not os.path.exists(thumbnail_path):
    create_thumbnail(video_path, thumbnail_path)

# Хранение состояния выбора инструмента и информации о записи
user_states = {}
user_enrollment = {}
user_feedback = {}
user_feedback_given = {}
previous_teachers = {}  # Хранение предыдущих преподавателей для кнопки назад


# Начальное состояние
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("👋 Приветствуем вас в онлайн-школе гитары “Фриссон”!😃\n\n"
                         "🔥 Здесь, в “Фриссоне”, мы верим, что музыка 🎵 - это не просто звук, это чувство. "
                         "Это мурашки по коже, это дрожь вдохновения, это тот самый “фриссон”, который заставляет сердце биться чаще.\n\n"
                         "🎸 Независимо от вашего уровня подготовки – новичок вы или опытный музыкант – мы поможем вам "
                         "раскрыть свой музыкальный потенциал 📈 и найти свой уникальный гитарный голос 💡.\n\n"
                         "🤘 В нашей школе вас ждет:\n\n"
                         "✅ Индивидуальный подход: Персонализированные уроки, адаптированные под ваши цели и темп обучения.\n\n"
                         "✅ Профессиональные преподаватели: Опытные гитаристы, которые увлечены музыкой и готовы делиться своими знаниями.\n\n"
                         "✅ Удобный формат обучения: Занимайтесь в любое время и в любом месте, где есть интернет.\n\n"
                         "✅ Поддержка и вдохновение: Присоединяйтесь к нашему дружному сообществу гитаристов и получайте мотивацию для дальнейшего развития.\n\n"
                         "🎸Приготовьтесь к захватывающему путешествию в мир гитары🐱!\n\n"
                         "Перед этим просим посмотреть видеоролик о нашей школе🎸.\n"
                         "⬇️ ⬇️ ⬇️"
                         )

    await bot.send_video(chat_id=message.chat.id, video=open('фриссон.mp4', 'rb'))


    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Да ✅", callback_data="join_courses"), 
                 InlineKeyboardButton("Нет ❌", callback_data="decline_courses"))
    
    await message.answer("⭐ Хотите ли вы присоединиться к нашим курсам?", reply_markup=keyboard)

@dp.callback_query_handler(lambda callback_query: callback_query.data == "join_courses")
async def process_yes(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Акустическая 🎸", callback_data="Акустическая гитара"),
                 InlineKeyboardButton("Электро 🎸", callback_data="Электрогитара"),
                 InlineKeyboardButton("Укулеле 🎸", callback_data="Укулеле"))
    
    await bot.send_message(callback_query.from_user.id, "Выберите пожалуйста инструмент 🎸:", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda callback_query: callback_query.data == "decline_courses")
async def process_no(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, "😔 Обидно, но надеюсь, вы передумаете!")
    await callback_query.answer()

@dp.callback_query_handler(lambda callback_query: callback_query.data == "think_about_it") 
async def process_think_about_it(callback_query: types.CallbackQuery): 
    await bot.send_message(callback_query.from_user.id, "😔 Обидно, но надеюсь, вы передумаете!") 
    await callback_query.answer()

@dp.callback_query_handler(lambda callback_query: callback_query.data in ["Акустическая гитара", "Электрогитара", "Укулеле"])
async def process_instrument_selection(callback_query: types.CallbackQuery):
    instrument = callback_query.data
    user_states[callback_query.from_user.id] = instrument
    previous_teachers[callback_query.from_user.id] = None  # Сбросить предыдущего преподавателя

    await show_teacher(callback_query, "Ефим", instrument)  # Показываем первого преподавателя

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("next_"))
async def process_next_teacher(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if callback_query.data == "next_kostya":
        previous_teachers[user_id] = "Ефим"  # Сохраняем предыдущего преподавателя
        await show_teacher(callback_query, "Константин (Костет)", "Электрогитара")

@dp.callback_query_handler(lambda callback_query: callback_query.data == "back")
async def process_back(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    previous_teacher = previous_teachers.get(user_id)

    if previous_teacher:
        if previous_teacher == "Ефим":
            await show_teacher(callback_query, "Ефим", user_states[user_id])
        elif previous_teacher == "Константин (Костет)":
            await show_teacher(callback_query, "Константин (Костет)", user_states[user_id])

async def show_teacher(callback_query: types.CallbackQuery, teacher_name: str, instrument: str):
    description = get_teacher_description(teacher_name)
    photo_path = f"{teacher_name}.jpg"  # Предполагается, что фотографии названы по имени преподавателя (например: "Ефим.jpg")

    await send_teacher_info(callback_query.message, teacher_name, description, photo_path, f"https://t.me/fima_578")

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Согласиться ✅", callback_data=f"agree_{teacher_name}"),
                 InlineKeyboardButton("Следующий ⏭️", callback_data="next_kostya"))

    # Добавляем кнопку "Назад"
    if previous_teachers[callback_query.from_user.id] is not None:
        keyboard.add(InlineKeyboardButton("Назад 🔙", callback_data="back"))

    await bot.send_message(callback_query.from_user.id, "🚀 Что вы хотите сделать дальше 🤖?", reply_markup=keyboard)

def get_teacher_description(teacher_name: str) -> str:
    if teacher_name == "Ефим":
        return (
            "🔥 Ефим преподает:\n\n "
            "- Акустическую гитару\n"
            "- Электрогитару\n"
            "- Укулеле\n\n"
            "✅ Является участником и основателем группы Saint Sanity.\n\n"
            "✅ Шикарно владеет инструментом!\n\n"
            "✅ Личный подход к каждому ученику!\n\n"
            "✅ Большой опыт преподавания!\n\n"
            "✅ Опыт игры на гитаре более 10 лет!"
        )
    else:  # Константин 
        return (
            "🔥 Константин (Костет) преподает:\n\n"
            "- Акустическую гитару\n"
            "- Электрогитару\n"
            "- Укулеле\n\n"
            "✅ Является основателем проекта!\n\n"
            "✅ Большой опыт работы на сцене!\n"
            "✅ Участник множества музыкальных проектов!\n\n"
            "✅ Личный подход к каждому ученику!\n"
            "✅ Большой опыт преподавания!\n\n"
            "✅ Обучение прошли более 50 учеников!"
        )

@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith("agree_"))
async def process_agree(callback_query: types.CallbackQuery): 
    user_id = callback_query.from_user.id

    if callback_query.data == "agree_Ефим":
        await bot.send_message(user_id, "👍 Отлично! Ждем вас на занятиях с Ефимом 🥳!")
    elif callback_query.data == "agree_Константин (Костет)":
        await bot.send_message(user_id, "👍 Отлично! Ждем вас на занятиях с Константином 🥳!")

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Записаться 🎯", callback_data="signup"),
                 InlineKeyboardButton("Подумаю 🤔", callback_data="think_about_it"))
    
    await bot.send_message(user_id, "Что бы вы хотели сделать дальше 👁️?", reply_markup=keyboard)

@dp.message_handler(commands=['musical'])
async def handle_musical_command(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Акустическая 🎸", callback_data="Акустическая гитара"),
                 InlineKeyboardButton("Электро 🎸", callback_data="Электрогитара"),
                 InlineKeyboardButton("Укулеле 🎸", callback_data="Укулеле"))
    await message.answer("Пожалуйста, выберите инструмент 🎸:", reply_markup=keyboard)

@dp.message_handler(commands=['help'])
async def handle_help_command(message: types.Message):
    help_text = (
        "📚 Добро пожаловать в онлайн-школу гитары «Фриссон»! \n"
        "Мы предлагаем:🚀\n\n"
        "- Индивидуальные занятия 🎈\n"
        "- Уроки по различным музыкальным инструментам 🎸(акустическая гитары, электрогитара и укулеле 🎸!)\n"
        "- Безопасное обучение 😇\n"
        "- Поддержка наших преподавателей в Telegram и на канале ❤️.\n\n"
        "Чтобы записаться на занятия, просто нажмите кнопку 'Записаться 🎯', и вы получите всю необходимую информацию!\n\n"
        "Стоимость обучения 💰 зависит от формата и длительности занятий. Пожалуйста, посмотрите на прайс-лист или напишите в телеграмм канал🔥!\n\n"
        "Если у вас есть вопросы ❓, не стесняйтесь писать в нашем Telegram-канале: https://t.me/frisson777.\n\n"
    )
    await message.answer(help_text)

@dp.message_handler(commands=['feedback']) 
async def handle_feedback_command(message: types.Message): 
    await bot.send_message(message.from_user.id, "Пожалуйста, оставьте ваш отзыв 📝 о занятиях:") 
    user_feedback[message.from_user.id] = message.from_user.first_name # Сохраняем имя пользователя

@dp.message_handler(lambda message: message.from_user.id in user_feedback) 
async def handle_feedback(message: types.Message): 
    user_id = message.from_user.id 
    user_name = user_feedback[user_id] # Получаем сохраненное имя пользователя feedback = message.text
    feedback = message.text
    await message.answer("Спасибо за ваш отзыв! Мы ценим ваше мнение. 😊")

    await bot.send_message('5207722001', f"Отзыв от {user_name}: {feedback}") # Замените на ID администратора, куда отправляется отзыв

# Измененная функция для отправки информации о преподавателе
async def send_teacher_info(message: types.Message, teacher_name: str, description: str, photo_path: str, button_url: str):
    # Сначала отправляем фотографию с кнопкой
    inline_buttons = InlineKeyboardMarkup()
    inline_buttons.add(InlineKeyboardButton(teacher_name, url=button_url))  # Добавляем кнопку с ссылкой на аккаунт

    await bot.send_photo(message.chat.id, photo=open(photo_path, 'rb'), reply_markup=inline_buttons)
    await bot.send_message(message.chat.id, f"🎉 Вы выбрали инструмент! Вот информация 💡 о вашем преподавателе ⭐:\n{description}")

@dp.callback_query_handler(lambda callback_query: callback_query.data == "signup")
async def process_signup(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    await bot.send_message(callback_query.from_user.id, "🎊 Отлично! 🎊 Переходите на наш Telegram-канал: https://t.me/frisson777")
    await bot.send_message(callback_query.from_user.id, "Переходите на аккаунт нашего менеджера 💰, чтобы записаться на первый бесплатный урок 🙃: (https://@Frissonguitar)")

    await bot.send_animation(chat_id=callback_query.message.chat.id, animation=open("Собака.gif.mp4", 'rb'))

    await request_feedback(user_id)

# Запрос на обратную связь
async def request_feedback(user_id):
    # Создание клавиатуры с кнопками для оценок
    feedback_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("Плохо 👎"),
        KeyboardButton("Нормально 😐"),
        KeyboardButton("Хорошо 👍"),
        KeyboardButton("Отлично 🌟"),
        KeyboardButton("Замечательно 🎉")
    ]
    feedback_keyboard.add(*buttons)

    await bot.send_message(user_id, "Пожалуйста, оцените работу нашего бота:", reply_markup=feedback_keyboard)

@dp.message_handler(lambda message: message.text in ["Плохо 👎", "Нормально 😐", "Хорошо 👍", "Отлично 🌟", "Замечательно 🎉"])
async def handle_feedback_rating(message: types.Message):
    user_id = message.from_user.id
    rating = message.text

    # Отправляем оценку админу
    await bot.send_message('5156742036', f"Отзыв от {message.from_user.first_name}: Оценка {rating}")  # Замените на ID администратора

    await bot.send_message(user_id, "Спасибо за вашу оценку! Мы ценим ваше мнение. 😊", reply_markup=ReplyKeyboardRemove())

    user_feedback_given[user_id] = True  # Помечаем, что оценка была выставлена


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)