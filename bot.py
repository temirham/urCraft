from telegram import Update, ReplyKeyboardMarkup
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

# Словарь для хранения состояния пользователя (запрашиваем пароль)
user_password_state = {}

# Кнопки для меню
def generate_reply_keyboard():
    keyboard = [
        ["Получить список контактов", "Ввести пароль"],  # Ряды кнопок
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Отправляем сообщение с кнопками над клавиатурой
    await update.message.reply_text(
        "Привет! Используй одну из кнопок ниже, чтобы продолжить.",
        reply_markup=generate_reply_keyboard()
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
        await get_contacts(update, context)
    else:
        await update.message.reply_text("Неизвестная команда. Попробуйте снова или введите пароль.")

async def get_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Проверка состояния пользователя, если пароль не введен
    if user_id not in user_password_state or not user_password_state[user_id]:
        await update.message.reply_text(
            "Для получения контактов введите пароль."
        )
        return

    # Если пользователь авторизован, получаем контакты
    contacts = session.query(Contact).all()
    if not contacts:
        await update.message.reply_text("Контакты не найдены.")
        return

    data = [
        {"Имя": contact.name, "Телефон": contact.phone, "Дата": contact.created_at}
        for contact in contacts
    ]
    df = pd.DataFrame(data)

    file_path = "contacts.xlsx"
    df.to_excel(file_path, index=False)
    with open(file_path, "rb") as file:
        await update.message.reply_document(file)

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
