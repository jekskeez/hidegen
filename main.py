import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Токен Telegram-бота
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# URL для работы с mail.tm API
MAIL_TM_API_URL = "https://api.mail.tm"

# Функция для создания временной почты через API mail.tm
def create_temp_email():
    headers = {
        'Authorization': 'Bearer YOUR_MAIL_TM_API_TOKEN',
        'Content-Type': 'application/json'
    }
    response = requests.post(f"{MAIL_TM_API_URL}/api/v1/mailboxes", headers=headers)
    if response.status_code == 201:
        email_data = response.json()
        return email_data['address']
    else:
        return None

# Функция для получения последнего письма на временную почту
def get_latest_email(address):
    headers = {
        'Authorization': 'Bearer YOUR_MAIL_TM_API_TOKEN'
    }
    response = requests.get(f"{MAIL_TM_API_URL}/api/v1/mailboxes/{address}/messages", headers=headers)
    if response.status_code == 200:
        emails = response.json()
        if emails:
            return emails[0]['subject']  # Заголовок первого письма
        else:
            return "Нет новых писем"
    else:
        return "Ошибка при получении писем"

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я помогу тебе получить временную почту.")

# Функция для обработки команды /getemail
def get_email(update: Update, context: CallbackContext):
    temp_email = create_temp_email()
    if temp_email:
        update.message.reply_text(f"Твоя временная почта: {temp_email}")
    else:
        update.message.reply_text("Не удалось создать временную почту. Попробуй позже.")

# Функция для обработки команды /checkemail
def check_email(update: Update, context: CallbackContext):
    if context.args:
        temp_email = context.args[0]
        subject = get_latest_email(temp_email)
        update.message.reply_text(f"Последнее письмо на {temp_email}: {subject}")
    else:
        update.message.reply_text("Пожалуйста, укажи временную почту для проверки.")

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Основная функция для запуска бота
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Добавляем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("getemail", get_email))
    dp.add_handler(CommandHandler("checkemail", check_email))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
