from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import pandas as pd
from main import Contact  # Импорт модели из FastAPI

DATABASE_URL = "sqlite:///./contacts.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

TOKEN = "7795817928:AAG0AXvfrETo2lif6rIgyqYBbjXufLX6wSg"
SECRET_PASSWORD = "temas"  # Заданный пароль для доступа

# Словарь для хранения состояния пользователя (запрашиваем пароль и выбранную категорию)
user_password_state = {}
user_category_state = {}

# Генерация кнопок для главного меню
def generate_main_menu():
    keyboard = [
        ["Получить список контактов", "Ввести пароль"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Генерация кнопок для выбора категории
def generate_category_menu():
    topics = session.query(Contact.topic).distinct().all()
    keyboard = [[topic[0]] for topic in topics]  # Кнопка для каждой категории
    keyboard.append(["Все категории"])  # Кнопка для выбора всех категорий
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отправляем сообщение с кнопками главного меню
    await update.message.reply_text(
        "Привет! Используй одну из кнопок ниже, чтобы продолжить.",
        reply_markup=generate_main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Обработка ввода пароля
    if text == "Ввести пароль":
        await update.message.reply_text("Введите ваш пароль текстом.")
    elif text == SECRET_PASSWORD:
        user_password_state[user_id] = True
        await update.message.reply_text("Пароль верен! Теперь вы можете получить контакты.")
    elif text == "Получить список контактов":
        await choose_category(update, context)
    elif text in [topic[0] for topic in session.query(Contact.topic).distinct().all()] + ["Все категории"]:
        await get_contacts(update, context, category=text)
    else:
        await update.message.reply_text("Неизвестная команда. Попробуйте снова или введите пароль.")

async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Проверка состояния пользователя, если пароль не введен
    if user_id not in user_password_state or not user_password_state[user_id]:
        await update.message.reply_text(
            "Для получения контактов введите пароль."
        )
        return

    # Отправляем кнопки для выбора категории
    await update.message.reply_text(
        "Выберите категорию из списка ниже:",
        reply_markup=generate_category_menu()
    )

async def get_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = None):
    user_id = update.message.from_user.id

    # Проверка состояния пользователя, если пароль не введен
    if user_id not in user_password_state or not user_password_state[user_id]:
        await update.message.reply_text(
            "Для получения контактов введите пароль."
        )
        return

    # Фильтрация контактов по категории
    if category == "Все категории":
        contacts = session.query(Contact).all()
    else:
        contacts = session.query(Contact).filter(Contact.topic == category).all()

    if not contacts:
        await update.message.reply_text("Контакты не найдены.")
        return

    # Формируем данные для экспорта в Excel
    data = [
        {"Имя": contact.name, "Телефон": contact.phone, "Категория": contact.topic, "Дата": contact.created_at}
        for contact in contacts
    ]
    df = pd.DataFrame(data)

    file_path = "contacts.xlsx"
    df.to_excel(file_path, index=False)
    with open(file_path, "rb") as file:
        await update.message.reply_document(file)

    # Возврат к главному меню после отправки
    await update.message.reply_text("Контакты отправлены. Что будем делать дальше?", reply_markup=generate_main_menu())

def main():
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обработчик текстовых сообщений

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
